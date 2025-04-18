![GitHub Release](https://img.shields.io/github/v/release/Digiratory/bayes_model?link=https%3A%2F%2Fgithub.com%2FDigiratory%2Fbayes_model%2Freleases)
![GitHub Issues or Pull Requests](https://img.shields.io/github/issues/Digiratory/bayes_model?link=https%3A%2F%2Fgithub.com%2FDigiratory%2Fbayes_model%2Fissues)
![GitHub Downloads (all assets, all releases)](https://img.shields.io/github/downloads/Digiratory/bayes_model/total?label=GitHub%20Downloads)
![PyPI - Downloads](https://img.shields.io/pypi/dm/bn_modeller?label=PyPI%20-%20Downloads&link=https%3A%2F%2Fpypi.org%2Fproject%2Fbn-modeller%2F)

<p align="center">
    <h1 align="center">BN Modeller</h1>
    <p align="center">An open-source application designed to facilitate feature dependency modeling and evaluation using Bayesian Networks.</p>
</p>

## Instalation

You can install this project using pip:

```bash
pip install bn_modeller
```

or can download the latest Windows executable from the [BN Modeller GitHub Releases page](https://github.com/Digiratory/bayes_model/releases).

### Graphviz

A Graphviz error could arise. To solve the problem add the Graphviz executables on your systems' PATH as follows:

1. Install windows package from: <https://graphviz.org/download/> (Linux and Mac instructions can be found here as well)
2. Install python graphviz package
3. Press the Windows key
4. Type in the search box: edit environment variables for your account
5. Select Path
6. Click Edit… button
7. Click New
8. Add 'bin' folder to User path in environment variables manager (e.g: C:\Program Files (x86)\Graphviz2.38\bin)
9. Add location dot.exe to System Path (e.g: C:\Program Files (x86)\Graphviz2.38\bin\dot.exe)
10. Click OK and OK again

Once have done that, restart your python IDE (if it is open). If this was running in a CMD prompt (e.g.
Anaconda Command prompt), restart this prompt as well to make sure the prompt finds the new
environment variables.

<https://pygraphviz.github.io/documentation/stable/install.html>

## Launch Application

To launch the application installed with `pip`, run:

```bash
bn_modeller
```

If you have downloaded BN Modeller using the Windows executable, simply double-click the `bn_modeller.exe` file located in the directory.

## Build

### Build Executable file for Windows

1. Install pyinstaller
2. Execute the following command:

```bash
pyinstaller --onefile --add-data="./bn_modeller/resources/templates/*:./bn_modeller/resources/templates/" --add-data="./bn_modeller/resources/icon.ico:./bn_modeller/resources/icon.ico" --icon=./bn_modeller/resources/icon.ico --name=bn_modeller.exe --windowed ./bn_modeller/app.py

```

## Troubleshooting

### High storage utilization on Windows 10/11

This high storage utilization probably caused by WindowsSearch Engine. To mitigate the problem you should disable the indexing of content for .sqlite files as following.

1. Press Win to open Start Menu and type in Index.
2. Click on Indexing Options.
3. On this next screen, hit Advanced > (Tab) File Types. For extention `.sqlite` select "Index Properties Only".
