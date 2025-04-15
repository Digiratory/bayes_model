import ctypes
import os
import sys

from PySide6.QtCore import QCommandLineOption, QCommandLineParser, QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

from bn_modeller import __version__
from bn_modeller.windows.main_window import MainWindow


def create_application(argv: list[str]) -> QApplication:
    QCoreApplication.setOrganizationName("Digiratory")
    QCoreApplication.setOrganizationDomain("digiratory.ru")
    QCoreApplication.setApplicationName("bn_modeller")
    QCoreApplication.setApplicationVersion(__version__)
    bn_modeller_appid = "digiratory.bn_modeller.{__version__}"
    if os.name == "nt":
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(bn_modeller_appid)
    if "no-gui" in argv:
        app = QCoreApplication(argv)
    else:
        app = QApplication(argv)
    return app


def manage_cli_args(app: QCoreApplication) -> QCommandLineParser:
    cl_parser: QCommandLineParser = QCommandLineParser()
    cl_parser.setApplicationDescription("Bayesian Network Modeller")
    cl_parser.addHelpOption()
    cl_parser.addVersionOption()

    no_gui = QCommandLineOption("nogui", "Launch in headless mode")
    cl_parser.process(app)

    return cl_parser


def main():
    app = create_application(sys.argv)
    cl_parser = manage_cli_args(app)

    if isinstance(app, QApplication):
        main_window = MainWindow()
        main_window.show()
    else:
        raise ValueError("Headless mode is not supported")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
