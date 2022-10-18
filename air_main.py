# -*- coding: utf-8 -*-
"""
Created on Wed Dec 22 13:10:00 2021

TITLE: Air Sample Annalyzer Main Window

@author: Alejandro Condori aleja
E-mail: alejandrocondori2@gmail.com
"""
#%%
import os
import sys
import time
import qdarkstyle
import numpy as np
import pyqtgraph as pg
from readfile import read_cnf_file
from dialogs import Pk_Search
from cuantifwiz import  Cuantif_Wizard
from widgets import AniLabel, MyTabWidget
from pyqtgraph.Qt import QtCore, QtGui, QtWidgets, uic

#%%
# mod_path, _ = os.path.split(os.path.abspath(__file__))
# os.chdir(mod_path)
# print(os.getcwd())
ui_main, ui_main_parent = uic.loadUiType("appearance/air_main.ui")

#%%

class Air_MainWindow(ui_main_parent, ui_main):
    '''Ventana Principl del programa Air Sample'''
    def __init__(self, config, dark_v):
        QtWidgets.QMainWindow.__init__(self)
        ui_main.__init__(self)
        self.setupUi(self)
        self.dark_v = dark_v
        pg.setConfigOptions(antialias=True)
        exit_act = QtGui.QAction(QtGui.QIcon(
            'icons/exit3.png'),
            'Exit',
            self
        )
        exit_act.setShortcut('Ctrl+Q')
        exit_act.setStatusTip('Exit application')
        exit_act.triggered.connect(self.close)
        self.toolbar.addAction(exit_act)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap("icons/tc45_3.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.setWindowIcon(icon)
        icon1 = QtGui.QIcon()
        icon1.addPixmap(QtGui.QPixmap("icons/psearchico.png"), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.menu_pks.setIcon(icon1)
        self.status_label = AniLabel(50,400)
        # self.status_label.setText(' ')
        self.status_bar.addPermanentWidget(self.status_label)
        a = QtGui.QLabel('')
        self.status_bar.addPermanentWidget(a)
        # Número de pestañas máximas
        self.n_files = config['file_number']
        self.nuclide_file = config['nuclide_file']
        self.n_tabs = 0
        self.tabs = []
        self.banners = []
        self.spec_views = []
        self.zooms = []
        self.sectioninfo = []
        
        self.menu_opcnf.triggered.connect(self.cnf_browser)
        self.action_open.triggered.connect(self.cnf_browser)
        self.action_zoom.triggered.connect(self.zoom_trigg)
        self.action_log.triggered.connect(self.log_trigg)
        self.tab_wid.currentChanged.connect(self.tab_change)
        self.menu_pks.triggered.connect(self.peak_search)
        self.menu_cua_air.triggered.connect(self.cuantif_air)
        
        # self.tab_change()

    def zoom_trigg(self, state):
        for i in range(self.n_tabs):
            self.tabs[i].upd_zoom_state(state)

    def log_trigg(self, state):
        for i in range(self.n_tabs):
            self.tabs[i].upd_log_state(state)

    def cnf_browser(self):
        '''Abre la ventana de apertura de archivo con extencion *.CNF, lee el 
        archivo, almacena la informacion y'''
        file_name = QtGui.QFileDialog.getOpenFileName(
            self, 'Abrir Archivo', 'files/',
            'CNF File (*.CNF *.cnf )'
        )
        sp_obj = 0
        if file_name[0]:
            try:
                sp_obj = read_cnf_file(file_name[0])
            except:
                QtGui.QMessageBox.critical(
                    self, 'Error al leer archivo...',
                    'El archivo especificado no existe o posee un formato '
                    'incompatible'
                )
            else:
                tab_i = None
                if self.n_tabs < self.n_files:
                    tab_i = self.add_tab(sp_obj, file_name)
                else:
                    ok_act = QtGui.QMessageBox.question(
                        self, 'Slots ocupados...',
                        'Máxima cantidad de archivos abiertos '
                        'permitido,\n¿Desea reemplazar algún slot?'
                    )
                    if ok_act == QtGui.QMessageBox.Yes:
                        tabfull, ok_act = QtGui.QInputDialog.getInt(
                            self, 'Reemplazar slot',
                            'Ingrese el número del slot a reemplazar: '
                            f'(1 - {self.n_files})',
                            1, 1, self.n_tabs
                        )
                        if ok_act:
                            tab_i = tabfull-1
                            self.tabs[tab_i].set_spec(sp_obj, True)
                            self.tabs[tab_i].file = [
                                os.path.join(file_name[0]),
                                os.path.basename(file_name[0])
                            ]
                            self.tab_wid.setCurrentIndex(tab_i)
                            self.tabs[tab_i].upd_vline()
                        # if tab_i == 0:
                        #     self.tab_wid.currentChanged.emit(
                        #         self.tab_wid.currentIndex()
                        #     )

    def add_tab(self, sp_obj, file_name):
        tab = MyTabWidget()
        self.tabs.append(tab)
        self.n_tabs += 1
        tab.set_spec(sp_obj)
        tab.file = [
            os.path.join(file_name[0]),
            os.path.basename(file_name[0])
        ]
        tab.upd_vline()
        if self.action_zoom.isChecked():
            tab.upd_zoom_state(True)
        if self.action_log.isChecked():
            tab.upd_log_state(True)
        tab_i = self.tab_wid.addTab(tab, f'Datasource {self.n_tabs}')
        self.tab_wid.setCurrentIndex(tab_i)
        return tab_i

    @QtCore.pyqtSlot()
    def tab_change(self):
        '''Metodo que cambia el título del la ventana principal, de acuerdo con
        la pestaña que este seleccionada'''
        # TODO !: QSTATUSBAR PATH de archivo
        ind = self.tab_wid.currentIndex()
        if self.tab_wid.isTabEnabled(ind):
            self.setWindowTitle(
                'Air Sample Gamma Analyzer'+' - '+
                self.tabs[ind].file[1]
            )
            self.tab_wid.setTabToolTip(ind, self.tabs[ind].file[1])
            self.status_label.setText(self.tabs[ind].file[0])
        else:
            self.setWindowTitle(
                'Air Sample Gamma Analyzer'
            )
        # for x in self.menu_cal.findChildren(QtGui.QAction):
        # for x in self.menu_cal.actions():
        #     if x.objectName == '':
        #         print(x)
        #     else:
        #         x.setEnabled(True)

    @QtCore.pyqtSlot()
    def cuantif_air(self):
        '''Metodo que inicia la ventana externa para ejecutar la rutina de 
        cuantificación de picos'''
        ind = self.tab_wid.currentIndex()
        if self.tab_wid.isTabEnabled(ind):
            cuant_wiz = Cuantif_Wizard(
                self,
                self.tabs[ind].data,
                None, 
                None,
                "config/nuclides.yml",
                'cals/airdefault.yml',
                self.dark_v,
                sp_name=self.tabs[ind].file[1]
            )
            cuant_wiz.exec_() 
        
    @QtCore.pyqtSlot()
    def peak_search(self):
        '''Metodo que inicia la ventana externa para ejecutar la rutina de 
        busqueda de picos'''
        ind = self.tab_wid.currentIndex()
        if self.tab_wid.isTabEnabled(ind):
            diag_psearch = Pk_Search(self, self.tabs[ind].data)
            diag_psearch.exec_() 
            # exec_() pausea esta función hasta que se cierre el dialogo
            if diag_psearch.can:
                self.tabs[ind].data.der_2, self.tabs[ind].data.der_1 = \
                    diag_psearch.result[1:]
                if diag_psearch.add.isChecked():
                    self.tabs[ind].data.peaks = \
                        list(self.tabs[ind].data.peaks) + \
                            diag_psearch.result[0]
                    self.tabs[ind].data.peaks = np.unique(
                        self.tabs[ind].data.peaks, axis=0
                    )
                else:
                   self.tabs[ind].data.peaks = np.array(diag_psearch.result[0])
                if diag_psearch.viewder.isChecked():
                    self.tabs[ind].deriv.ch = self.tabs[ind].data.channels
                    self.tabs[ind].deriv.co = self.tabs[ind].data.counts
                    self.tabs[ind].deriv.pr = self.tabs[ind].data.der_1
                    self.tabs[ind].deriv.se = self.tabs[ind].data.der_2
                    self.tabs[ind].deriv.plot_grafs()
                    self.tabs[ind].deriv.show()  #show abre el dialogo, pero no detiene la funcion
                self.tabs[ind].dockrep.addWidget(
                    self.tabs[ind].reporbar,
                    row=0, col=0
                )
                if self.tabs[ind].data.peaks.size == 0:
                    self.tabs[ind].data.peaks = None
                    self.tabs[ind].reporbar.setText(
                        '<center><font size="+1"><b>Resultados de Búsqueda de Picos</b></font><br>\
                            Fecha y Hora : <i>{:s}</i><br>Canal Inicial : <i>{:d}</i> &nbsp;&nbsp;&nbsp;\
                                Canal Final : <i>{:d}</i> <br>Significancia : <i>{:.2f}</i><br><b>\
                                    No se encontraron picos</b></center>'.format(
                        time.strftime('%d/%m/%Y %H:%M:%S', time.localtime()),
                        diag_psearch.ch_sta.value(),
                        diag_psearch.ch_end.value(),
                        diag_psearch.signi.value()
                        )
                    )
                else:
                    self.tabs[ind].reporbar.setText(
                        '<center><font size="+1"><b>Resultados de Búsqueda de Picos</b></font><br>\
                            Fecha y Hora : <i>{:s}</i><br>Canal Inicial : <i>{:d}</i> &nbsp;&nbsp;&nbsp;\
                                Canal Final : <i>{:d}</i> <br>Significancia : <i>{:.2f}</i></center>'.format(
                        time.strftime('%d/%m/%Y %H:%M:%S', time.localtime()),
                        diag_psearch.ch_sta.value(),
                        diag_psearch.ch_end.value(),
                        diag_psearch.signi.value()
                        )
                    )
                self.tabs[ind].reporbar.setStyleSheet(
                    'color:black; background-color: cyan'
                )
                self.tabs[ind].reportab.set_data(
                    self.tabs[ind].data.peaks,
                    'psearch',
                    self.tabs[ind].data.unit
                )
                self.tabs[ind].reportab.horizontalHeader().setSectionResizeMode(
                                QtGui.QHeaderView.Stretch
                                )
        # else:
        #     return None


#%%
if __name__ == "__main__":
    print('Hola QT')
    os.environ['PYQTGRAPH_QT_LIB'] = 'PyQt5'
    dark_theme = True
    import yaml
    config = yaml.safe_load(open("config/config.yml"))
    app = QtWidgets.QApplication(sys.argv)
    window = Air_MainWindow(config, dark_theme)
    if dark_theme:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    else:
        app.setStyleSheet('')
    # # app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    # app.setStyleSheet(
    #     qdarkstyle.load_stylesheet(qt_api=os.environ['PYQTGRAPH_QT_LIB'])
    # )
    window.show()
    sys.exit(app.exec_())

#%% Notes:
    # background-|: url(icons/tc45_3.png);