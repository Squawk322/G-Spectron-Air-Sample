# -*- coding: utf-8 -*-
"""
Created on Tue Dec 28 12:27:07 2021

TITLE: Ventanas de diálogo

@author: Alejandro Condori aleja
E-mail: alejandrocondori2@gmail.com
"""
# %%
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, uic
from pyqtgraph.dockarea import Dock, DockArea
from peaksearch import peak_search

# %%
ui_pks, ui_pks_parent = uic.loadUiType("appearance/psearch.ui")
ui_der, ui_der_parent = uic.loadUiType("appearance/der.ui")
ui_wiz, ui_wiz_parent = uic.loadUiType("appearance/quantif.ui")
# %% Peak search dialog
class Pk_Search(ui_pks_parent, ui_pks):
    '''Ventana para ejecutar la rutina de Busqueda de Picos'''
    def __init__(self, parent, spec = None):
        ui_pks_parent.__init__(self, parent)
        # ui_pks.__init__(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setupUi(self)
        self.ejecutar.clicked.connect(self.st)
        self.cancel.clicked.connect(self.ca)
        self.spec = spec
        self.can = False
        self.adjustSize()
        geo = self.frameGeometry()
        self.setFixedSize(geo.width(), geo.height())

    def st(self):
        '''Accion al ejecutar la rutina de búsqueda de picos'''
        counts = self.spec.counts
        enercal = self.spec.en_coef
        fwhme = self.spec.fwhm #En Kev
        fwhmc = fwhme/enercal[2] #En canales
        signif = self.signi.value()
        start = self.ch_sta.value()
        end = self.ch_end.value()
        self.result = peak_search(counts, fwhmc, signif, enercal, ch_ini=start, ch_end=end)
        self.can = True
        self.close()

    def ca(self):
        '''Accion al presionar el boton cancelar'''
        self.close()

# %%  VENTANA DE GRAFICOS

class Der_Graph(ui_der_parent, ui_der):
    '''Ventna donde se visualizan los gráficos de las derivadas'''
    def __init__(self):
        ui_der_parent.__init__(self)
        # ui_der.__init__(self)
        self.setupUi(self)
        self.ar = DockArea()
        self.l1.addWidget(self.ar)
        self.sp = Dock('Espectro Gamma', size=(500,25))
        self.fdock = Dock("Primera Derivada", size=(500,25))
        self.sdock = Dock("Segunda Derivada", size=(500,25))
        self.spgraf = pg.PlotWidget()
        self.fgraf = pg.PlotWidget()
        self.sgraf = pg.PlotWidget()
        self.ar.addDock(self.sp) 
        self.ar.addDock(self.fdock, 'bottom', self.sp)
        self.ar.addDock(self.sdock, 'bottom', self.fdock)
        self.fdock.addWidget(self.fgraf)
        self.sdock.addWidget(self.sgraf)
        self.sp.addWidget(self.spgraf)
        self.spgraf.setXLink(self.fgraf)
        self.sgraf.setXLink(self.fgraf)
        self.sgraf.setYLink(self.fgraf)
        self.ch = 0
        self.co = 0
        self.pr = 0
        self.se = 0
        # self.fgraf.setTitle('Primera Derivada')
        # self.sgraf.setTitle('Segunda Derivada')
    
    def plot_grafs(self):
        self.spgraf.clear()
        self.spgraf.plot(self.ch, self.co)
        self.spgraf.setLogMode(False, True)
        self.fgraf.clear()
        self.fgraf.plot(self.ch, self.pr)
        self.sgraf.clear()
        self.sgraf.plot(self.ch, self.se)

# %% WIZARD DE CUANTIFICACIÓN

class Cuantif_Wizard(ui_wiz_parent, ui_wiz):
    def __init__(self):
        ui_wiz_parent.__init__(self)
        self.setupUi(self)
        logo = QtGui.QPixmap("icons/tc45_3.png").scaledToWidth(65)
        self.setPixmap(1, logo)
        # self.startpage.
        

# %%
if __name__ == "__main__":
    import sys
    print('Hola QT')
    app = QtGui.QApplication(sys.argv)
    window = Cuantif_Wizard()
    window.show()
    sys.exit(app.exec_())
