import os

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QDialog,
    QGridLayout,
    QLabel,
    QPlainTextEdit,
    QPushButton,
    QVBoxLayout,
)


class AboutDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        my_icon = QIcon()
        my_icon.addFile(
            os.path.join(os.path.dirname(__file__), "..", "resources\\icon.ico")
        )
        self.setWindowIcon(my_icon)

        self.initUI()

    def initUI(self):
        layout = QVBoxLayout()
        self.setLayout(layout)

        # License text
        license_text = """
           <b>Bayesian Network Modeller</b>, <br>
            A program to represents a set of variables and their conditional dependencies via a directed acyclic graph.<br>
            Copyright (C) 2025  Digiratory <br>
            <br>
            This program is free software: you can redistribute it and/or modify<br>
            it under the terms of the GNU General Public License as published by<br>
            the Free Software Foundation, either version 3 of the License, or<br>
            (at your option) any later version.<br>
            <br>
            This program is distributed in the hope that it will be useful,<br>
            but WITHOUT ANY WARRANTY; without even the implied warranty of<br>
            MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the<br>
            GNU General Public License for more details.<br>
            <br>
            You should have received a copy of the GNU General Public License<br>
            <a href="https://www.gnu.org/licenses/">https://www.gnu.org/licenses/</a>.<br>
            <br>
            Source code can be found at <a href="https://github.com/Digiratory/bayes_model">https://github.com/Digiratory/bayes_model</a>.
            """
        license_label = QLabel(license_text)
        layout.addWidget(license_label)

        # Open-source libraries and licenses
        lib_licenses = [
            ("PySide6", "LGPL-3.0"),
            ("Qt", "LGPL-3.0"),
            ("py-banshee", "GPL-3.0"),
            ("openpyxl", "MIT"),
            ("pygraphviz", "BSD License (BSD-3-Clause)"),
            ("pyqtgraph", "BSD License (BSD-3-Clause)"),
        ]
        lib_text = "<b>3rd party libraries used in this project:</b><br>"
        for i, (lib, license) in enumerate(lib_licenses):
            lib_text += f"""
                <b>{lib}:</b> {license} <br>
                """
        libs_label = QLabel(lib_text)
        libs_label.setFixedWidth(250)
        layout.addWidget(libs_label)

        # Authors
        authors_label = QLabel("<b>Authors:</b><br}")
        layout.addWidget(authors_label)
        authors_text = """
                Aleksandr Sinitca (amsinitca@etu.ru) <a href=\"mailto:amsinitca@etu.ru\">Contact</a><br>
                Irina Shpakovskaya<br>
                Tarapata Svetlana
            """
        rich_authors_label = QLabel(authors_text)
        rich_authors_label.setOpenExternalLinks(True)
        layout.addWidget(rich_authors_label)

        # Button to close the dialog
        button_box = QPushButton("Close")
        layout.addWidget(button_box)
        button_box.clicked.connect(self.close)

    def showEvent(self, event):
        super().showEvent(event)
        self.adjustSize()
