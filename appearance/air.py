# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'air_main.ui'
#
# Created by: PyQt5 UI code generator 5.12.3
#
# WARNING! All changes made in this file will be lost!


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(572, 372)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("../../../../.designer/backup/appearance/icons/tc45_3.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        MainWindow.setWindowIcon(icon)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("")
        self.centralwidget.setObjectName("centralwidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName("verticalLayout")
        self.tab_wid = QtWidgets.QTabWidget(self.centralwidget)
        self.tab_wid.setAutoFillBackground(False)
        self.tab_wid.setStyleSheet("")
        self.tab_wid.setTabsClosable(False)
        self.tab_wid.setObjectName("tab_wid")
        self.verticalLayout.addWidget(self.tab_wid)
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 572, 21))
        self.menubar.setObjectName("menubar")
        self.menuFile = QtWidgets.QMenu(self.menubar)
        self.menuFile.setObjectName("menuFile")
        self.menuCal = QtWidgets.QMenu(self.menubar)
        self.menuCal.setObjectName("menuCal")
        self.menuAnalysis = QtWidgets.QMenu(self.menubar)
        self.menuAnalysis.setObjectName("menuAnalysis")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.toolbar = QtWidgets.QToolBar(MainWindow)
        self.toolbar.setObjectName("toolbar")
        MainWindow.addToolBar(QtCore.Qt.TopToolBarArea, self.toolbar)
        self.action_open = QtWidgets.QAction(MainWindow)
        self.action_open.setObjectName("action_open")
        self.menu_opcnf = QtWidgets.QAction(MainWindow)
        self.menu_opcnf.setObjectName("menu_opcnf")
        self.action_log = QtWidgets.QAction(MainWindow)
        self.action_log.setCheckable(True)
        self.action_log.setObjectName("action_log")
        self.action_zoom = QtWidgets.QAction(MainWindow)
        self.action_zoom.setCheckable(True)
        self.action_zoom.setObjectName("action_zoom")
        self.actionPeak_Search = QtWidgets.QAction(MainWindow)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("../../../../.designer/backup/appearance/icons/psearchico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionPeak_Search.setIcon(icon1)
        self.actionPeak_Search.setObjectName("actionPeak_Search")
        self.menuFile.addAction(self.menu_opcnf)
        self.menuAnalysis.addAction(self.actionPeak_Search)
        self.menubar.addAction(self.menuFile.menuAction())
        self.menubar.addAction(self.menuCal.menuAction())
        self.menubar.addAction(self.menuAnalysis.menuAction())
        self.toolbar.addAction(self.action_open)
        self.toolbar.addAction(self.action_zoom)
        self.toolbar.addAction(self.action_log)

        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "Air Sample Gamma Analyzer"))
        self.menuFile.setTitle(_translate("MainWindow", "File"))
        self.menuCal.setTitle(_translate("MainWindow", "Calibrations"))
        self.menuAnalysis.setTitle(_translate("MainWindow", "Analysis"))
        self.toolbar.setWindowTitle(_translate("MainWindow", "toolBar"))
        self.action_open.setText(_translate("MainWindow", "Open1"))
        self.menu_opcnf.setText(_translate("MainWindow", "Open CNF File..."))
        self.action_log.setText(_translate("MainWindow", "Log"))
        self.action_log.setToolTip(_translate("MainWindow", "No se que poner aqui"))
        self.action_log.setShortcut(_translate("MainWindow", "Ctrl+L"))
        self.action_zoom.setText(_translate("MainWindow", "Zoom"))
        self.actionPeak_Search.setText(_translate("MainWindow", "Peak Search..."))
