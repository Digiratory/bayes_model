---
title: Understanding Correlation Coefficients
parent: User Guide - Welcome!
nav_order: 2
---

# Understanding Correlation Coefficients

BN Modeller utilizes several correlation coefficients to help you identify potential dependencies between variables when constructing Bayesian Networks. Here's a brief explanation of each:

## What is Correlation?

Correlation measures the strength and direction of a linear relationship between two variables. A positive correlation means that as one variable increases, the other tends to increase as well. A negative correlation means that as one variable increases, the other tends to decrease. A correlation close to zero suggests little or no linear relationship.

## 1. Pearson's Correlation Coefficient (r)

* **What it measures:** Pearson's correlation coefficient (often denoted as 'r') measures the *linear* relationship between two continuous variables. It assesses how well the data points cluster around a straight line.
* **Range:** The value of 'r' ranges from -1 to +1.
  * +1 indicates a perfect positive linear correlation.
  * -1 indicates a perfect negative linear correlation.
  * 0 indicates no linear correlation.
* **Assumptions:** Pearson's correlation assumes that the data is normally distributed and that the relationship between the variables is linear.
* **Example:** A positive Pearson's correlation between drug dosage and patient recovery time might suggest that higher dosages are associated with faster recovery.

## 2. Spearman's Rank Correlation Coefficient (ρ)

* **What it measures:** Spearman's rank correlation coefficient (often denoted as 'ρ' - rho) measures the *monotonic* relationship between two variables. A monotonic relationship means that as one variable increases, the other tends to increase (or decrease) consistently, but not necessarily in a straight line.
* **Range:** Like Pearson's correlation, Spearman's rank correlation ranges from -1 to +1.
* **Advantages:** Spearman's rank correlation is less sensitive to outliers and does not require the assumption of normality.
* **Example:** A positive Spearman's rank correlation between gene expression level and disease severity might suggest that higher gene expression is associated with more severe disease, even if the relationship isn't perfectly linear.

## 3. Partial Correlation

* **What it measures:** Partial correlation measures the correlation between two variables while *controlling for* the influence of one or more other variables. It helps to isolate the direct relationship between the variables of interest.
* **Why it's useful:**  Sometimes, two variables appear to be correlated simply because they are both influenced by a third variable. Partial correlation helps to remove this confounding effect.
* **Example:**  You might observe a correlation between patient age and hospital readmission rate. However, this correlation might be influenced by the presence of other factors, such as the severity of the patient's condition. Partial correlation can be used to assess the correlation between age and readmission rate while controlling for the effect of disease severity.

## Important Notes

* Correlation does not imply causation. Just because two variables are correlated does not mean that one causes the other.
* Always consider the context of your data and the assumptions of each correlation coefficient when interpreting the results.
