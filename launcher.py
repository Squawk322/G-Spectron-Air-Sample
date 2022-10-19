# -*- coding: utf-8 -*-
"""
Created on Wed Dec 22 13:10:00 2021

TITLE: Air Sample Annalyzer launcher

@author: Alejandro Condori aleja
E-mail: alejandrocondori2@gmail.com
"""
# import os
import sys
import yaml
import qdarkstyle
import air_main as ar
from pyqtgraph.Qt import QtGui, QtWidgets

if __name__ == "__main__":
    print('Hola QT')
    config = yaml.safe_load(open("config/config.yml"))
    app = QtWidgets.QApplication(sys.argv)
    window = ar.Air_MainWindow(config)
    dark_theme = False
    # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window.show()
    if dark_theme:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    else:
        app.setStyleSheet('')
    sys.exit(app.exec_())

