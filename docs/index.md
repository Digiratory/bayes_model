---
layout: default
title: Bayesian Networks Modeler
nav_order: 1
---

# Bayesian Networks Modeler

Welcome to the BN Modeller Documentation.

BN Modeller is an open-source application designed to facilitate feature dependency modeling and evaluation using Bayesian Networks. In research fields like medicine and biology, understanding the complex relationships between different factors – such as genes, proteins, or patient characteristics – is crucial for advancing scientific discovery. BN Modeller provides a powerful tool to explore these relationships and gain deeper insights into the underlying biological or medical phenomena of interest.

**What are Bayesian Networks?** Briefly, they are visual models that represent relationships between variables. They allow researchers to represent cause-and-effect relationships, or correlations, between different factors, even when those relationships are not fully understood.

At its core, BN Modeller provides a user-friendly graphical interface for constructing, visualizing, and analyzing Bayesian Networks. It offers a range of tools for both network construction and inference, enabling users to:

* **Visualize Complex Relationships:** Build and visualize Bayesian Networks intuitively, even without extensive technical expertise. The graphical interface allows you to represent factors and their connections in a clear and understandable way.
* **Perform Robust Dependency Analysis:** Leverage powerful inference tools to evaluate the strength and nature of feature dependencies. This helps determine how changes in one factor might influence others.
* **Advance Research with Guidance:** Access practical guidelines and best practices to support feature dependency modeling and evaluation. These resources are designed to help researchers, regardless of their prior experience with Bayesian Networks, effectively utilize the software.
* **Understand Key Concepts:** Find explanations of fundamental Bayesian Network concepts and terminology to build a solid foundation for your research.

We invite you to explore the documentation and discover how BN Modeller can enhance your research and analysis workflows.

## Features

BN Modeller provides a comprehensive suite of tools designed to facilitate the creation, analysis, and visualization of Bayesian Networks. The following features are available to support your research workflows:

* **Data Import:** BN Modeller supports the import of datasets from common file formats, including CSV (Comma Separated Values) and Excel spreadsheets. This allows you to easily incorporate your existing data into the application for analysis.
* **Project-Based Data Management:** To streamline your research, BN Modeller utilizes a project-based system. This allows you to organize and manage multiple datasets within a single project, preserving the state of your work and facilitating easy switching between different analyses.
* **Bayesian Network Construction via Correlation Coefficients:** BN Modeller allows you to build and visualize Bayesian Networks based on statistical correlation measures. Specifically, you can utilize Pearson's correlation coefficient (measuring linear relationships), Spearman's rank correlation coefficient (measuring monotonic relationships), or partial correlation coefficients (accounting for the influence of other variables). A brief explanation of correlation coefficients is provided on the page [Understanding Correlation](./user-guide/understanding-correlation.html).
* **Correlation Evaluation:** The application provides tools to evaluate the strength and significance of correlations between variables. This allows you to identify potential dependencies and inform the structure of your Bayesian Network.
* **Manual Dependency Specification:** While BN Modeller can suggest potential dependencies based on correlation analysis, you retain full control over the network structure. You can manually select and specify the dependencies between variables, allowing you to incorporate domain expertise and refine the model.
* **Bayesian Network Visualization and Export:** BN Modeller allows you to export your constructed Bayesian Networks as image files in various formats, including PNG and SVG. This enables you to easily share your findings and incorporate the visualizations into reports and presentations.

## Getting started

This section will guide you through the initial setup and installation process. Choose the method that best suits your environment and technical expertise.

### 1. Installation via pip (Recommended for Python Users)

If you have Python installed on your system, we recommend using `pip`, the Python package installer, to install BN Modeller.

* **Prerequisites:** Ensure you have Python 3.7 or higher installed. You can download Python from [https://www.python.org/downloads/](https://www.python.org/downloads/).
* **Installation Command:** Open your terminal or command prompt and run the following command:

    ```bash
    pip install bn-modeller
    ```

* **Verification:** After the installation completes, you can verify that BN Modeller is installed correctly by running the following command in your terminal:

    ```bash
    bn_modeller --version
    ```

### 2. Installation using the Windows Executable**

For users who prefer not to use Python or are on Windows, a pre-built executable file is available.

* **Download:** You can download the latest Windows executable from the [BN Modeller GitHub Releases page](https://github.com/Digiratory/bayes_model/releases).
* **Installation:** There is no installation process; simply download and run the `.exe` file.
* **Note:** The executable includes all necessary dependencies and does not require a separate Python installation.

**Next Steps:**

Once BN Modeller is installed, you can explore the application's features and begin building your Bayesian Networks.  Refer to the [User Guide](./user-guide/index.html) for detailed instructions on using the software.

## Citations

If you use BN Modeller in your research or work, please consider citing it as follows:

```bibtex

```
