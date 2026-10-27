---
title: Predicting Values
parent: User Guide - Welcome!
nav_order: 3
---

# Predicting Values

The **Prediction** page uses the Bayesian network you have built to estimate the
values of features that were not (or cannot be) measured, based on the features
you did observe. A typical use case is imputing missing laboratory measurements
from related markers. The prediction is performed with a **non-parametric
Bayesian network (NPBN)** quantified directly from your data, so no assumptions
about the parametric shape of the variable distributions are required.

This page explains how to use the Prediction page and describes every
computation in enough detail to be reproduced or cited in the Methods section
of a publication.

> **Note:** the Prediction page is available since BN Modeller **version 1.1**.

## Prerequisites

Before a prediction can be made, complete the following steps (see
[Data Analysis Workflow](data-analysis-workflow.html)):

1. Import your dataset into a project (CSV or Excel; one row per sample, one
   column per feature).
2. Select the relevant features and define their dependencies in the
   **Bayesian Network → Dependency** tab. Each checked cell states that the
   feature in the column depends on the feature in the row.
3. Check the network in the **Bayesian Network → Visualization** tab. The
   prediction always uses the network **exactly as shown there**, including the
   selected correlation family, the p-value filter and the threshold slider.

## Assigning feature roles

Open the **Bayesian Network → Prediction** tab. It contains two panels and a
threshold control:

* **Input Features** (left panel) — the observable features that will be used
  to condition the prediction. **All features start as inputs**, because in
  the beginning every feature is considered observable.
* **Features to Predict** (right panel) — the features whose values BN Modeller
  will estimate. This panel is initially empty.

To move features between the panels, select one or more rows in a panel and
click the **>** (or **<**) button between the panels. A feature can appear in
only one panel at a time.

The panels follow the **Dependency** tab automatically: unchecking a feature
there removes it from both panels, and checking it brings it back as an
input. A feature moved to **Features to Predict** keeps its role across
these updates for as long as it remains selected in the Dependency tab;
unchecking it resets the role, so it reappears on the input side when
selected again.

When you click **Predict**, the application conditions on **all input
features** (i.e. treats them as given, known values) and predicts **all marked
features**. Three rules apply:

* Features that are not connected to the network (no dependencies survive in
  the Dependency table and Visualization settings) cannot take part in a
  prediction. Marked features without connections are reported in an error
  dialog; unconnected input features are simply ignored.
* At least one feature must remain an input, otherwise there is nothing to
  condition on.
* At least one feature must be marked for prediction, otherwise there is
  nothing to compute.

### Filtering the input view with a threshold

The **Threshold Type** control filters which input features are *displayed* in
the left panel. It helps to find the most informative features quickly. The
available criteria are computed for every feature against all other features:

| Criterion | Meaning | Feature passes when |
|-----------|---------|---------------------|
| `R` (default) | Maximum absolute Spearman rank correlation with any other feature | value ≥ threshold |
| `P` | Maximum absolute partial correlation with any other feature (the influence of the remaining features is factored out) | value ≥ threshold |
| `P_val` | Minimum p-value of the Spearman correlation with any other feature | value ≤ threshold |

The defaults are `R = 0.0` and `P = 0.0` (everything visible) and
`P_val = 0.05` (only features correlated significantly with at least one other
feature are visible).

**Important:** the threshold only changes what is *displayed* in the left
panel. A feature hidden by the threshold is still an input feature and still
participates in the prediction, because every feature starts as an input.
Threshold-failing features can still be moved to the right panel through a
temporary lowering of the threshold.

For background on the correlation coefficients see
[Understanding Correlation](understanding-correlation.html).

## Running the prediction and reading the results

1. Transfer the features you want to estimate to the **Features to Predict**
   panel.
2. Click **Predict**. The computation runs in the background; a progress
   window is shown.
3. The **Prediction Results** dialog appears with:
   * a **Table** tab — one row per sample. The first column, `Sample Id`,
     carries the original sample identifier from the project, so the rows
     stay matchable to the source data. Each predicted feature adds a
     `Predicted <name>` column next to the observed values. Rows whose
     input values are incomplete are not shown (see
     [How the prediction is computed](#how-the-prediction-is-computed)).
   * one **plot tab per predicted feature** — a scatter plot with the
     *predicted* values on the horizontal axis and the *observed* values on
     the vertical axis. Each dot is one sample with both values known. Red
     dots are influential points (outliers) detected by Cook's distance; the
     line is a linear fit through the remaining points.
4. Under every plot a caption shows two correlation coefficients,
   `R: <value> → <value>`: the Pearson correlation between predicted and
   observed values, and the same correlation computed after removal of the
   Cook's-distance outliers. A large drop between the two values (as in
   `R: 0.682 → 0.141`) means the apparent quality of the prediction is driven
   by a few influential samples rather than a general trend — worth
   investigating those samples in the source data.
5. **Save CSV...** exports the whole table (the `Sample Id` column followed
   by the observed and predicted columns) to a comma-separated file for
   further processing or archiving.

## How the prediction is computed

This section describes the computations in the order in which they are
performed. It is written so that it can be adapted directly for a Materials
and Methods section. Network quantification and conditional inference are
implemented with the py-banshee library (see [References](#references)).

### 1. Network structure

The directed graph is rebuilt at prediction time from the same settings shown
on the Visualization tab:

1. Edges are taken from the dependency table (row feature → column feature).
2. Each edge is weighted with the correlation coefficient of the selected
   correlation family (Pearson, Spearman or partial; the default is Spearman).
3. If the p-value filter is enabled, an edge whose coefficient is not
   significant at α = 0.05 is removed.
4. Edges whose absolute coefficient is not greater than the threshold slider
   value are removed.
5. Directed cycles, if present, are resolved iteratively: within each detected
   cycle the edge with the smallest weight is removed until the graph is
   acyclic.

Only features connected to this graph participate in the prediction; the
remaining nodes of the network are the connected features that were not
marked as inputs.

### 2. Network quantification

The structure is quantified with the conditional rank correlation matrix of
the non-parametric Bayesian network formalism (computed by the `bn_rankcorr`
procedure of py-banshee). In this formalism the dependence of each node on
each of its parents is described by a single conditional rank correlation.
For sampling, these rank correlations are converted into the Pearson
correlation matrix of an auxiliary multivariate normal distribution (a
Gaussian copula).

The quantification uses **complete observations only**: samples with at least
one missing value among the network features are excluded from this step,
because the empirical distributions below require complete data.

### 3. Empirical marginal distributions

Every feature is described by its empirical cumulative distribution function
(ECDF) computed from the complete observations. The support of each ECDF is
extended by 0.1 beyond the smallest and largest observed value so that the
boundary values remain inside the interpolation domain.

### 4. Conditional inference

For every sample whose input values are complete:

1. Each observed input value is mapped through its ECDF to a cumulative
   probability and then through the inverse standard normal distribution to a
   normal quantile.
2. The conditional joint normal distribution of the remaining (unobserved)
   nodes given these quantiles is obtained with the standard formulas for
   conditioning a multivariate normal distribution.
3. 10,000 samples are drawn from this conditional distribution and mapped back
   to the original scale through the inverse ECDF of each predicted feature,
   using linear interpolation.
4. The **mean** of these 10,000 values is the reported prediction for that
   sample and feature.

If an input value lies outside the range observed in the complete samples,
it is clamped to that range before conditioning: the empirical distribution
has no support beyond it, and the boundary yields the nearest supported
prediction. Samples with incomplete input values produce no prediction (their
rows are absent from the results), while samples with missing *predicted*
features are still predicted — this is the imputation use case, and their
observed cells are simply empty in the results.

### 5. Diagnostics

For every predicted feature with known observed values, the Pearson
correlation R between predicted and observed values is computed. A linear
regression of observed on predicted values is fitted, and samples whose
Cook's distance exceeds the common 4/n rule-of-thumb threshold are flagged as
influential points and drawn in red. R is then recomputed without these
points. Comparing the two values shows whether the predictive performance is
spread over the whole dataset or driven by a few influential samples.

## Interpreting the results

* **Scatter close to the diagonal with high R** — the network reproduces the
  observed values well; predictions for missing values can be trusted within
  the observed range.
* **Large drop after outlier removal** (e.g. `R: 0.682 → 0.141`) — the
  correlation is carried by a handful of influential samples. Check whether
  the red samples form a distinct group (for example a ceiling or floor value
  of a scoring scale) and consider collecting more data in that range.
* **Predictions outside the observed data range are not produced:** the
  empirical margins only support the observed values (plus the small 0.1
  boundary extension), and out-of-range inputs are clamped to that range
  before conditioning.
* **Correlation is not causation.** The predictions reflect associations in
  your dataset and the dependency structure you specified.

## References

* Koot, P., Mendoza-Lugo, M.A., Paprotny, D., Morales-Nápoles, O., Ragno, E. and Worm, D.T., 2023. PyBanshee version (1.0): A Python implementation of the MATLAB toolbox BANSHEE for Non-Parametric Bayesian Networks with updated features. SoftwareX, 21, p.101279. Project page and citation: [https://github.com/mike-mendoza/py_banshee](https://github.com/mike-mendoza/py_banshee).
* Kurowicka, D. and Cooke, R.M., 2006. Uncertainty analysis with high dimensional dependence modelling. John Wiley & Sons. (Non-parametric Bayesian networks and the conditional rank correlation formalism.)
* Cook, R.D., 2000. Detection of influential observation in linear regression. Technometrics, 42(1), pp.65-68. (Cook's distance.)
