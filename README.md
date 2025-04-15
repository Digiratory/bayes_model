# GUI для работы с байесовским выводом (байесовские сети)

на основе библиотеки py_banshee


- Разрабатывалась для задачи поиска когнитивной состовляющий при назначении слуховых аппаратов, но хочется, чтобы можно было использовать для любых данных

Если не работает именно py_banshee, попробуй залесть в код библиотеки py_banshee и исправить:
/home/work/.local/lib/python3.8/site-packages/py_banshee

predict 307

func_i = interp1d(fe, xe, kind=way, fill_value="extrapolate")  # interpolation fill_value="extrapolate"

## Instalation

You can install this project using pip:

```bash
pip install bn_modeller
```

## Build

### Build Executable file for Windows

1. Install pyinstaller
2. Execute the following command:
```bash
pyinstaller --onefile --add-data="./bn_modeller/resources/icon.ico;." --icon=./bn_modeller/resources/icon.ico --name=bn_modeller.exe --windowed ./bn_modeller/app.py

```
## Instalation

### Graphviz

A Graphviz error could arise.
To solve the problem add the Graphviz executables on your systems' PATH as follows:

1. Install windows package from: https://graphviz.org/download/ (Linux and Mac instructions can be found here as well)
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

https://pygraphviz.github.io/documentation/stable/install.html

## Troubleshooting

### High storage utilization on Windows 10/11

This high storage utilization probably caused by WindowsSearch Engine. To mitigate the problem you should disable the indexing of content for .sqlite files as following.

1. Press Win to open Start Menu and type in Index.
2. Click on Indexing Options.
3. On this next screen, hit Advanced > (Tab) File Types. For extention `.sqlite` select "Index Properties Only".

## bn_visualize

turn off ```plt.show```
