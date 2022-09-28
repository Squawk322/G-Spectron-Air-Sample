'''
G-Spectron GUI
'''

import sys
import os
import time
import qdarkstyle
import numpy as np
import pyqtgraph.parametertree.parameterTypes as pTypes
import pyqtgraph as pg
from pyqtgraph.Qt import QtCore, QtGui, uic
from pyqtgraph.parametertree import ParameterTree
from pyqtgraph.dockarea import Dock, DockArea
from pandas import to_datetime
from readfile import read_cnf_file, Spec

from ventanas import Pk_Search, Der_Graph, Ener_Cal, EnFw_CalShow, EnFw_Cal, Eff_Cal, Eff_CalShow
# from ventanas import *
# from pyqtgraph.dockarea import *
# from PyQt5 import QtCore, QtGui, uic
# from PyQt5.QtWidgets import QFileDialog, QMessageBox, QAction, QInputDialog, QScrollBar, QLabel
# from PyQt5.QtGui import QIcon
#%%
# Ideas:
#    - Usar un set text cde forma : ('ajsjsjj %f kjdjdjdj %f', *vector)
# a = 'la wea wena'
# f'{a}'
# Out[6]: 'la wea wena'
# f'{a = }'
# Out[7]: "a = 'la wea wena'"

# TODO !: Cuando se actualize la calibración energética:
# - Actualizar los valores resultantes del área de reportes
# - Limpiar el área de reportes


#%%
# UIfile = "gspectron.ui" # Enter file here.
UI_MAIN = uic.loadUiType("UI_FILES/gspectron.ui")[0]
# UI_MAIN, QtBaseClass = uic.loadUiType(UIfile)

class DockArea2(DockArea):
    '''
    Change to avoid the collapse of the docks
    '''
    def makeContainer(self, typ):
        # new = super(DockArea, self).makeContainer(typ)
        new = super().makeContainer(typ)
        new.setChildrenCollapsible(False)
        return new

# class stat(QtGui.QObject):
#     def __init__(self):
#         QtGui.QObject.__init__(self)
#         self.ps_stat = [False for _ in range(6)]
#         self.pksDone = QtCore.pyqtSignal()
        
#     def did(self, routine, done_undone, ind):
#         if routine is 'peak_search':
#             self.ps_stat[ind] = done_undone
#             self.pksDone.emit()

class TableWidget(pg.TableWidget):
    '''Modificaciones a la widget de pyqtgraph'''
    def __init__(self, *args, **kwds):
        pg.TableWidget.__init__(self, *args, **kwds)
        # self.setFormat('%.2f', 1)
        self.setFormat('%12.2f')
        self.setShowGrid(False)
        self.setStyleSheet(
            'QWidget { background-image: url(bg.png); } ')

    def set_data(self, data, mode, en_unit):
        '''Metodo adicional para formatear automaticamente'''
        self.setStyleSheet("")
        self.setData(data)
        if mode == 'psearch':
            self.setHorizontalHeaderLabels(
                ['Centroide\n(Canal)',
                 'Energía\n({})'.format(en_unit),
                 'Signif.']
            )
        elif mode == 'pfit':
            self.setHorizontalHeaderLabels(
                ['Inicio\nROI',
                 'Fin\nROI',
                 'Centroide\n(Canal)',
                 'Energía\n({})'.format(en_unit),
                 'FWHM\n({})'.format(en_unit),
                 'Area Neta\ndel Pico']
            )
        for col_n in range(self.columnCount()):
            for row_n in range(self.rowCount()):
                self.item(row_n, col_n).setTextAlignment(
                    int(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                )
        self.resizeRowsToContents()
        self.setStyleSheet(
            "QHeaderView::section { background-color:cyan; color:black;}\
            QTableCornerButton::section {  background-color:cyan; color:black;\
                                         border: 1px outset gray;}"
        )
        # self.setStyleSheet(
        #     "QTableCornerButton::section {  background-color:cyan; color:black}"
        # )

class InfoPar(pTypes.GroupParameter):
    '''Modelo para el ParamterTree con la info del Espectro'''
    def __init__(self, **opts):
        pTypes.GroupParameter.__init__(self, **opts)
        self.addChild({'name': 'Parámetros de Adquisición', 'type': 'group'})
        self.addChild({'name': 'Datos de Calibración', 'type': 'group'})
        self.adq = self.param('Parámetros de Adquisición')
        self.cal = self.param('Datos de Calibración')
        adqchilds = [
            {'name': 'Inicio de Adq.', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Tiempo Real', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Tiempo Vivo', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Tiempo Muerto', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Cuentas Totales', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Conteo Máximo', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Nro de Canales', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Unidad de Energía   ', 'type': 'str', 'value': '', 'readonly': True}
        ]
        for i in adqchilds:
            self.adq.addChild(i)
        self.adqchilds = [self.param('Parámetros de Adquisición', it['name']) for it in adqchilds]
        self.cal.addChild({'name': 'Energía (A1*Ch³ + A2*Ch² + A3*Ch + A4)', 'type': 'group'})
        encal = [
            {'name': 'A1', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'A2', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'A3', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'A4', 'type': 'str', 'value': '', 'readonly': True}
        ]
        for i in encal:
            self.param('Datos de Calibración', 'Energía (A1*Ch³ + A2*Ch² + A3*Ch + A4)').addChild(i)
        self.encalchilds = [
            self.param('Datos de Calibración', 'Energía (A1*Ch³ + A2*Ch² + A3*Ch + A4)', it['name'])
            for it in encal
        ]
        self.cal.addChild({'name': 'FWHM (B1*E^(1/2) + B2)', 'type': 'group'})
        fwcal = [
            {'name': 'B1', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'B2', 'type': 'str', 'value': '', 'readonly': True}
        ]
        for i in fwcal:
            self.param('Datos de Calibración', 'FWHM (B1*E^(1/2) + B2)').addChild(i)
        self.fwcalchilds = [
            self.param('Datos de Calibración', 'FWHM (B1*E^(1/2) + B2)', it['name'])
            for it in fwcal
        ]
        self.cal.addChild({'name': 'Eficiencia', 'type': 'group'})
        effcal = [
            {'name': 'C1', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'C2', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'C3', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'C4', 'type': 'str', 'value': '', 'readonly': True}
        ]
        for i in effcal:
            self.param('Datos de Calibración', 'Eficiencia').addChild(i)
        self.effcalchilds = [
            self.param('Datos de Calibración', 'Eficiencia', it['name'])
            for it in effcal
        ]

class MyApp(QtGui.QMainWindow, UI_MAIN): 
    '''Ventana Principl del programa G-Spectron'''
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        UI_MAIN.__init__(self)
        self.setupUi(self)
        pg.setConfigOption('background', 'k')
        pg.setConfigOption('foreground', 'd')
        self.disable() #Bloqueo widgets al iniciar programa
        pg.setConfigOptions(antialias=True)
        exit_act = QtGui.QAction(QtGui.QIcon('icons/exit3.png'), 'Exit', self)
        exit_act.setShortcut('Ctrl+Q')
        exit_act.setStatusTip('Exit application')
        exit_act.triggered.connect(self.close)
        self.menu_opcnf.triggered.connect(self.cnf_browser)
        self.open.triggered.connect(self.cnf_browser)
        self.menu_opgsp.triggered.connect(self.gsp_browser)
        self.zoom.triggered.connect(self.zoom_trigg)
        self.toolbar.addAction(exit_act)
        self.log.triggered.connect(self.log_trigg)
        self.wat.currentChanged.connect(self.tab_change)
        self.menu_pks.triggered.connect(self.peak_search)
        self.menu_enercal.triggered.connect(self.ener_calib)
        self.menu_enfwcal.triggered.connect(self.enfw_calib)
        self.eff_val.triggered.connect(self.eff_calib)
        tab_layouts = [self.l1, self.l2, self.l3, self.l4, self.l5, self.l6]
        self.s_data = [Spec() for _ in range(6)]
        self.areas = [DockArea2() for _ in range(6)]
        bar_container = [QtGui.QWidget() for _ in range(6)]
        self.dockbar = [QtGui.QHBoxLayout() for _ in range(6)]
        for i in range(6):
            tab_layouts[i].addWidget(bar_container[i])
            bar_container[i].setLayout(self.dockbar[i])
            tab_layouts[i].addWidget(self.areas[i])
            self.dockbar[i].setContentsMargins(0, 0, 0, 0)
            bar_container[i].setStyleSheet('background-color: black')
        self.dockgraf = [Dock("Total", size=(700, 150)) for _ in range(6)]
        self.dockzoom = [Dock("Zoom", size=(500, 120)) for _ in range(6)]
        self.dockinfo = [Dock("Info Total", size=(700, 80)) for _ in range(6)]
        self.dockrep = [Dock("Area de Reportes", size=(500, 300)) for _ in range(6)]
        self.graf = [pg.PlotWidget() for _ in range(12)]
        self.vscrolls = [QtGui.QScrollBar() for _ in range(6)]
        self.file = ['' for _ in range(6)]
        self.set_graf(self.dockgraf+self.dockzoom, self.graf, self.vscrolls)
        self.pld = [None for _ in range(12)]  #plotdata
        # TODO !: 
        self.issaved = [False for _ in range(6)]
        self.pks_done = [False for _ in range(6)] 
        # TODO !: 
        # self.
        self.vlines = [pg.InfiniteLine(angle=90, movable=True) for _ in range(12)]
        self.set_vlines(self.vlines, self.graf)
        self.bartop = [
            [QtGui.QLabel('Canal : ') for _ in range(6)], [QtGui.QLabel() for _ in range(6)],
            [QtGui.QLabel('Energía : ') for _ in range(6)], [QtGui.QLabel() for _ in range(6)],
            [QtGui.QLabel('Cuentas: ') for _ in range(6)], [QtGui.QLabel() for _ in range(6)]
        ]
        # BARTOP[0] ES LABEL CANAL, BARTOP[1] ES VALOR CANAL, BARTOP[2] ES LABEL ENERGIA
        # BARTOP[3] ES VALOR ENERGIA, BARTOP[4] ES LABEL CUENTAS, BARTOP[5] ES VALOR CUENTAS
        self.rois = [pg.ROI([100, 100], [100, 1000]) for _ in range(6)]
        self.plt_region = [[False, -20, 0, 0, 0] for _ in range(6)] # [¿Log?, x_0, x_1, y_0, y_1]
        self.roi_region = [[False, 0, 0, 0, 0] for _ in range(6)] #[¿Log?, posx, posy, sizex, sizey]
        self.info = [ParameterTree() for _ in range(6)]
        self.infotree = [InfoPar(name='par'+str(i)) for i in range(6)]
        self.reportab = [TableWidget() for _ in range(6)]
        self.reporbar = [QtGui.QLabel('<b>Resultados</b>') for _ in range(6)]
        self.derivs = [Der_Graph() for _ in range(6)]
        self.pos_widgets()
        self.tab_change()

    @QtCore.pyqtSlot()
    def peak_search(self):
        '''Metodo que inicia la ventana externa para ejecutar la rutina de busqueda de picos'''
        ind = self.wat.currentIndex()
        if self.wat.isTabEnabled(ind):
            diag_psearch = Pk_Search(self, self.s_data[ind])
            diag_psearch.exec_() #exec pausea esta función hasta que se cierre el dialogo
            if diag_psearch.can:
                self.s_data[ind].der_2, self.s_data[ind].der_1 = diag_psearch.result[1:]
                if diag_psearch.add.isChecked():
                    self.s_data[ind].peaks = list(self.s_data[ind].peaks)+diag_psearch.result[0]
                    self.s_data[ind].peaks = np.unique(self.s_data[ind].peaks, axis=0)
                else:
                    self.s_data[ind].peaks = np.array(diag_psearch.result[0])
                if diag_psearch.viewder.isChecked():
                    self.derivs[ind].ch = self.s_data[ind].channels
                    self.derivs[ind].co = self.s_data[ind].counts
                    self.derivs[ind].pr = self.s_data[ind].der_1
                    self.derivs[ind].se = self.s_data[ind].der_2
                    self.derivs[ind].plot_grafs()
                    self.derivs[ind].show()  #show abre el dialogo, pero no detiene la funcion
                self.dockrep[ind].addWidget(self.reporbar[ind], row=0, col=0)
                if self.s_data[ind].peaks.size == 0:
                    self.s_data[ind].peaks = None
                    self.reporbar[ind].setText(
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
                    self.reporbar[ind].setText(
                        '<center><font size="+1"><b>Resultados de Búsqueda de Picos</b></font><br>\
                            Fecha y Hora : <i>{:s}</i><br>Canal Inicial : <i>{:d}</i> &nbsp;&nbsp;&nbsp;\
                                Canal Final : <i>{:d}</i> <br>Significancia : <i>{:.2f}</i></center>'.format(
                        time.strftime('%d/%m/%Y %H:%M:%S', time.localtime()),
                        diag_psearch.ch_sta.value(),
                        diag_psearch.ch_end.value(),
                        diag_psearch.signi.value()
                        )
                    )
                self.reporbar[ind].setStyleSheet(
                    'color:black; background-color: cyan'
                )
                self.reportab[ind].set_data(
                    self.s_data[ind].peaks,
                    'psearch',
                    self.s_data[ind].unit
                )
                self.reportab[ind].horizontalHeader().setSectionResizeMode(
                                QtGui.QHeaderView.Stretch
                                )
        # else:
        #     return None

    @QtCore.pyqtSlot()
    def ener_calib(self):
        '''Metodo que inicia la ventana externa para realizar la calibración \
            /de Energía'''
        ind = self.wat.currentIndex()
        if self.s_data[ind].peaks is not None:
            impo = True
            data_sent = self.s_data[ind].peaks.T[:2]
        else:
            impo = False
            data_sent = np.empty(0)
        if self.wat.isTabEnabled(ind):
            diag_encal = Ener_Cal(self, data_sent, impo)
            diag_encal.exec_()
            if diag_encal.can:
                cal_data = np.array([
                    diag_encal.model.input_channel,
                    diag_encal.model.input_energy,
                    np.zeros(len(diag_encal.model.input_energy))
                ])
                diag_calshow = EnFw_CalShow(
                    self,
                    cal_data,
                    self.s_data[ind],
                    from_diag='eneronly',
                    fname=self.file[ind][0]
                )
                diag_calshow.exec_()
                if diag_calshow.can:
                    self.s_data[ind].en_coef = diag_calshow.en_coef
                    self.s_data[ind].energy = diag_calshow.energy
                    self.set_spec(ind, self.s_data[ind])
                else:
                    print('sin cambios')
            else:
                print('se cancelo')
        # else:
        #     return None

    @QtCore.pyqtSlot()
    def enfw_calib(self):
        '''Metodo que inicia la ventana externa para realizar la calibración
            de Energía y fwhm'''
        ind = self.wat.currentIndex()
        if self.s_data[ind].peaks is not None:
            impo = True
            data_sent = self.s_data[ind].peaks.T[:2]
            data_sent = np.append(
                data_sent,
                [self.s_data[ind].fwhm[np.rint(data_sent[0]-1).astype(int)]],
                axis=0
            )
        else:
            impo = False
            data_sent = np.empty(0)
        if self.wat.isTabEnabled(ind):
            diag_encal = EnFw_Cal(self, data_sent, impo)
            diag_encal.exec_()
            if diag_encal.can:
                cal_data = np.array([
                    diag_encal.model.input_channel,
                    diag_encal.model.input_energy,
                    diag_encal.model.input_fwhm
                ])
                diag_calshow = EnFw_CalShow(
                    self, cal_data,
                    self.s_data[ind],
                    from_diag='enerfwhm',
                    fname=self.file[ind][0]
                )
                diag_calshow.exec_()
                if diag_calshow.can:
                    self.s_data[ind].en_coef = diag_calshow.en_coef
                    self.s_data[ind].fw_coef = diag_calshow.fw_coef
                    self.s_data[ind].energy = diag_calshow.energy
                    self.s_data[ind].fwhm = diag_calshow.fwhm
                    self.set_spec(ind, self.s_data[ind])
            #     else:
            #         print('sin cambios')
            # else:
            #     print('se cancelo')
        # else:
        #     return None

    @QtCore.pyqtSlot()
    def eff_calib(self):
        '''Abre el menu de ingreso de datos pra la calibracion de eficiencia'''
        ind = self.wat.currentIndex()
        # Saber si hay o no info de calibración de eficiencia previo
        if self.s_data[ind].eff is not None:
            impo = True
            data_sent = self.s_data[ind].eff['data']
        else:
            impo = False
            data_sent = np.empty(0)
        if self.wat.isTabEnabled(ind):
            diag_effcal = Eff_Cal(self, data_sent, impo)
            diag_effcal.exec_()
            if diag_effcal.can:
                cal_data = np.array([
                    diag_effcal.model.input_energy,
                    diag_effcal.model.input_effi,
                    diag_effcal.model.input_err
                ])
                diag_calshow = Eff_CalShow(
                    self, cal_data,
                    self.s_data[ind],
                    fname=self.file[ind][0]
                )
                diag_calshow.exec_()

    def pos_widgets(self):
        '''Posiciona las widgets y objetos generados dentro del lienzo generado en
        QtDesigner, asi como ciertos ajustes de propiedades'''
        for i in range(6):
            self.areas[i].addDock(self.dockgraf[i], 'left')
            self.dockgraf[i].hideTitleBar()
            self.dockzoom[i].hideTitleBar()
            self.areas[i].addDock(self.dockinfo[i], 'bottom', self.dockgraf[i])
            self.dockinfo[i].hideTitleBar()
            self.areas[i].addDock(self.dockrep[i], 'right', self.dockinfo[i])
            self.dockrep[i].hideTitleBar()
            self.dockbar[i].addWidget(self.bartop[0][i])
            self.dockbar[i].addWidget(self.bartop[1][i])
            self.dockbar[i].addWidget(self.bartop[2][i])
            self.dockbar[i].addWidget(self.bartop[3][i])
            self.dockbar[i].addWidget(self.bartop[4][i])
            self.dockbar[i].addWidget(self.bartop[5][i])
            self.rois[i].maxBounds = QtCore.QRectF(-20, -50, 4136, 20000000)#(x_0, y_0, ancho, alto)
            self.rois[i].addScaleHandle([0, 0.5], [1, 0.5])
            self.rois[i].addScaleHandle([0.5, 1], [0.5, 0])
            self.rois[i].addScaleHandle([1, 0.5], [0, 0.5])
            self.rois[i].addScaleHandle([0.5, 0], [0.5, 1])
            self.rois[i].addScaleHandle([0, 0], [1, 1])
            self.rois[i].addScaleHandle([0, 1], [1, 0])
            self.rois[i].addScaleHandle([1, 0], [0, 1])
            self.rois[i].addScaleHandle([1, 1], [0, 0])
            self.rois[i].sigRegionChanged.connect(self.upd_zoom)
            self.dockinfo[i].addWidget(self.info[i])
            self.info[i].setParameters(self.infotree[i], showTop=False)
            self.dockrep[i].addWidget(self.reportab[i], row=1, col=0)
            # self.dockrep[i].addWidget(self.reporbar[i], row=0, col=0)
            for j in range(3):
                self.bartop[j*2][i].setAlignment(QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter)
                # self.bartop[j*2][i].setFixedHeight(25)
                self.bartop[j*2][i].setMinimumHeight(25)
                self.bartop[j*2][i].setStyleSheet(
                    'color:cyan; font-weight: bold; background-color: black'
                )
                self.bartop[j*2+1][i].setAlignment(QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter)
                # self.bartop[j*2+1][i].setFixedHeight(25)
                self.bartop[j*2][i].setMinimumHeight(25)
                self.bartop[j*2+1][i].setStyleSheet(
                    'color: yellow; font-weight: bold; background-color: black'
                )

    @QtCore.pyqtSlot()
    def tab_change(self):
        '''Metodo que cambia el título del la ventana principal, de acuerdo con
        la pestaña que este seleccionada'''
        ind = self.wat.currentIndex()
        if self.wat.isTabEnabled(ind):
            self.setWindowTitle(
                'G-Spectron: Gamma-Spectrum Analyzer & Quantification'+' - '+
                self.file[ind][1]
            )
            self.wat.setTabToolTip(ind, self.file[ind][1])
        else:
            self.setWindowTitle(
                'G-Spectron: Gamma-Spectrum Analyzer & Quantification'
            )
        # for x in self.menu_cal.findChildren(QtGui.QAction):
        for x in self.menu_cal.actions():
            if x.objectName == '':
                print(x)
            else:
                x.setEnabled(True)
            # print(x.objectName(), type(x))
            
        # for x in self.menu_cal.findChildren(QtGui.QMenu):
        #     for y in x.findChildren(QtGui.QAction):
        #         y.setEnabled(False)

    @QtCore.pyqtSlot()
    def log_trigg(self):
        '''Accion al seleccionar/desseleccionar el boton de escala Logaritmica:
        Convierte a escala logaritmica/linea el eje Y de todas las pestañas y
        ajusta el tamaño de la ROI y de sus límites de movimiento. Del mismo
        modo modifica los parámetros de la barra de "desplazamiento" vertical'''
        for i in range(6):
            if self.pld[i] is not None:
                if self.log.isChecked() and not self.roi_region[i][0]:
                    if self.zoom.isChecked():
                        roi_state = self.rois[i].getState()
                        x_0, y_0 = roi_state['pos']
                        roi_width, roi_height = roi_state['size']
                        self.roi_region[i][1:] = [x_0, y_0, roi_width, roi_height]
                    self.pld[i].setLogMode(False, True)
                    self.pld[i+6].setLogMode(False, True)
                    yn0 = self.roi_region[i][2] / (
                        self.plt_region[i][4] - self.plt_region[i][3]
                    )
                    yn1 = (self.roi_region[i][2] + self.roi_region[i][4]) / (
                        self.plt_region[i][4] - self.plt_region[i][3]
                    )
                    self.plt_region[i][0] = True
                    ymax = np.ceil(np.log10(self.s_data[i].maxc))
                    self.plt_region[i][3:] = [-0.15, ymax]
                    self.upd_plt_zone(i)
                    yn0 *= self.plt_region[i][4]-self.plt_region[i][3]
                    yn1 *= self.plt_region[i][4]-self.plt_region[i][3]
                    self.roi_region[i][0] = True
                    self.roi_region[i][2] = yn0
                    self.roi_region[i][4] = yn1-yn0
                    if self.zoom.isChecked():
                        self.set_roi(i)
                    self.vscrolls[i].setMaximum(9)
                    self.vscrolls[i].setValue(self.vscrolls[i].maximum()+1-int(ymax))
                else:
                    if self.roi_region[i][0]:
                        if self.zoom.isChecked():
                            roi_state = self.rois[i].getState()
                            x_0, y_0 = roi_state['pos']
                            roi_width, roi_height = roi_state['size']
                            self.roi_region[i][1:] = [x_0, y_0, roi_width, roi_height]
                        self.pld[i].setLogMode(False, False)
                        self.pld[i+6].setLogMode(False, False)
                        yn0 = self.roi_region[i][2]/(self.plt_region[i][4]-self.plt_region[i][3])
                        yn1 = (self.roi_region[i][2]+self.roi_region[i][4])/\
                            (self.plt_region[i][4]-self.plt_region[i][3])
                        self.plt_region[i][0] = False
                        ymax = 2**(np.ceil(np.log2(self.s_data[i].maxc)))
                        if ymax < 16:
                            ymax = 16
                        self.plt_region[i][3:] = [-0.001*ymax, ymax]
                        self.upd_plt_zone(i)
                        yn0 *= (self.plt_region[i][4]-self.plt_region[i][3])
                        yn1 *= (self.plt_region[i][4]-self.plt_region[i][3])
                        self.roi_region[i][0] = False
                        self.roi_region[i][2] = yn0
                        self.roi_region[i][4] = yn1-yn0
                        if self.zoom.isChecked():
                            self.set_roi(i)
                        self.vscrolls[i].setMaximum(28)
                        self.vscrolls[i].setValue(self.vscrolls[i].maximum()-int(np.log2(ymax/16)))

    def upd_plt_zone(self, i):
        '''Ajusta la region del grafico'''
        self.graf[i].setRange(None, self.plt_region[i][1:3], self.plt_region[i][3:], padding=0.0)

    def set_vlines(self, vlines, grafs):
        '''Posiciona las lineas verticales (marcadores)
        en todas las graficas de las pestañas'''
        for i in range(12):
            grafs[i].addItem(vlines[i], ignoreBounds=True)
            vlines[i].setPos(100)
            if i < 6:
                vlines[i].sigPositionChanged.connect(self.upd_vlines)
            else:
                vlines[i].sigPositionChanged.connect(self.upd_vlines2)

    @QtCore.pyqtSlot()
    def upd_vlines(self):
        '''Limita el movimiento de las lineas verticales de la grafica superior
        a modo discreto, es decir de canal en canal.
        Llama a una función de actualizacion'''
        i = self.wat.currentIndex()
        ch0 = round(self.vlines[i].value())
        self.real_upd_vlines(i, ch0)

    @QtCore.pyqtSlot()
    def upd_vlines2(self):
        '''Limita el movimiento de las lineas verticales de la grafica inferior
        a modo discreto, es decir de canal en canal.
        Llama a una función de actualizacion'''
        i = self.wat.currentIndex()
        ch0 = round(self.vlines[i+6].value())
        self.real_upd_vlines(i, ch0)

    def real_upd_vlines(self, tab, pos):
        '''Funcion que actualiza la info del marcador (linea vertical)'''
        if pos < 1:
            pos = 1
        if pos > 4096:
            pos = 4096
        self.vlines[tab].setPos(pos)
        self.vlines[tab+6].setPos(pos)
        self.bartop[1][tab].setText(str(pos))
        self.bartop[3][tab].setText(
            str(round(self.s_data[tab].energy[pos-1], 2))+' '+self.s_data[tab].unit
        )
        self.bartop[5][tab].setText(str(int(self.s_data[tab].counts[pos-1])))

    def set_graf(self, dock, plot, v_slid):
        '''Metodo que posiciona las graficas en sus respectivos lienzos'''
        for i in range(12):
            dock[i].addWidget(plot[i], col=0)
            plot[i].showAxis('bottom', False)
            plot[i].showAxis('left', False)
            plot[i].setMouseEnabled(x=False, y=False)
            plot[i].hideButtons()
            if i < 6:
                dock[i].addWidget(v_slid[i], row=0, col=1)
                v_slid[i].valueChanged.connect(self.upd_slide)
                plot[i].setMinimumHeight(100)
                plot[i].scene().sigMouseClicked.connect(self.v_click1)
            else:
                plot[i].scene().sigMouseClicked.connect(self.v_click2)

    @QtCore.pyqtSlot()
    def upd_slide(self):
        '''Ajusta el rango vertical del grafico de acuerdo a la posicion de la
        barra de desplazamiento vertical'''
        i = self.wat.currentIndex()
        svalue = self.vscrolls[i].maximum()-self.vscrolls[i].value()
        if self.plt_region[i][0]:    # True es logaritmico
            if self.zoom.isChecked():
                roi_state = self.rois[i].getState()
                x_0, y_0 = roi_state['pos']
                roi_width, roi_height = roi_state['size']
            else:
                x_0, y_0, roi_width, roi_height = self.roi_region[i][1:]
            ymax = 1+svalue
            yn0 = y_0/(self.plt_region[i][4]-self.plt_region[i][3])
            yn1 = (y_0+roi_height)/(self.plt_region[i][4]-self.plt_region[i][3])
            self.plt_region[i][4] = ymax
            self.upd_plt_zone(i)
            yn0 *= (self.plt_region[i][4]-self.plt_region[i][3])
            yn1 *= (self.plt_region[i][4]-self.plt_region[i][3])
            if self.zoom.isChecked():
                self.rois[i].setPos((x_0, yn0))
                self.rois[i].setSize((roi_width, yn1-yn0))
                x_0, x_1, y_0, y_1 = self.plt_region[i][1:5]
                self.rois[i].maxBounds = QtCore.QRectF(x_0, y_0, x_1-x_0, y_1-y_0)
                self.real_upd_zoom(i)
            else:
                self.roi_region[i][2] = yn0
                self.roi_region[i][4] = yn1-yn0
        else:
            if self.zoom.isChecked():
                roi_state = self.rois[i].getState()
                x_0, y_0 = roi_state['pos']
                roi_width, roi_height = roi_state['size']
            else:
                x_0, y_0, roi_width, roi_height = self.roi_region[i][1:]
            ymax = 16*2**(svalue)
            yn0 = y_0/(self.plt_region[i][4]-self.plt_region[i][3])
            yn1 = (y_0+roi_height)/(self.plt_region[i][4]-self.plt_region[i][3])
            self.plt_region[i][4] = ymax
            self.plt_region[i][3] = -0.005*ymax
            self.upd_plt_zone(i)
            yn0 *= (self.plt_region[i][4]-self.plt_region[i][3])
            yn1 *= (self.plt_region[i][4]-self.plt_region[i][3])
            if self.zoom.isChecked():
                self.rois[i].setPos((x_0, yn0))
                self.rois[i].setSize((roi_width, yn1-yn0))
                x_0, x_1, y_0, y_1 = self.plt_region[i][1:5]
                self.rois[i].maxBounds = QtCore.QRectF(x_0, y_0, x_1-x_0, y_1-y_0)
                self.real_upd_zoom(i)
            else:
                self.roi_region[i][2] = yn0
                self.roi_region[i][4] = yn1-yn0

    @QtCore.pyqtSlot()
    def zoom_trigg(self):
        '''Accion al seleccionar/desselecionar el boton de zoom. Añade/elimina una ROI
        rectangular y un Dock con la grafica ampliada en la ROI'''
        if self.zoom.isChecked():
            for i in range(0, 6):
                if self.pld[i] is not None:
                    self.areas[i].addDock(self.dockzoom[i], 'bottom', self.dockgraf[i])
                    self.graf[i].addItem(self.rois[i])
                    self.set_roi(i)
        else:
            for i in range(0, 6):
                if self.pld[i] is not None:
                    roi_state = self.rois[i].getState()
                    x_0, y_0 = roi_state['pos']
                    roi_width, roi_height = roi_state['size']
                    self.roi_region[i][1:] = [x_0, y_0, roi_width, roi_height]
                    self.dockzoom[i].close()
                    self.graf[i].removeItem(self.rois[i])

    def set_roi(self, i):
        '''Posiciona la ROI en el grafico'''
        x_0, y_0, roi_width, roi_height = self.roi_region[i][1:5]
        self.rois[i].setPos((x_0, y_0))
        self.rois[i].setSize((roi_width, roi_height))
        x_0, x_1, y_0, y_1 = self.plt_region[i][1:5]
        self.rois[i].maxBounds = QtCore.QRectF(x_0, y_0, x_1-x_0, y_1-y_0)
        self.real_upd_zoom(i)

    @QtCore.pyqtSlot()
    def upd_zoom(self):
        '''Accion desencadenada cuando la ROI es modificada'''
        i = self.wat.currentIndex()
        self.real_upd_zoom(i)

    def real_upd_zoom(self, i):
        '''Actualiza la region del grafico del zoom cuando la ROI es modificada'''
        roi_state = self.rois[i].getState()
        x_0, y_0 = roi_state['pos']
        roi_width, roi_height = roi_state['size']
        x_1 = x_0+roi_width
        y_1 = y_0+roi_height
        # if upd: self.roi_region[i][1:] = [x_0, y_0, roi_width, roi_height]
        self.graf[i+6].setYRange(y_0, y_1, padding=0)
        self.graf[i+6].setXRange(x_0, x_1, padding=0)

    def disable(self):
        '''Bloquea todas las pestañas'''
        for i in range(6):
            self.wat.setTabEnabled(i, False)

    @QtCore.pyqtSlot()
    def cnf_browser(self):
        '''Abre la ventana de apertura de archivo con extencion *.CNF, lee el archivo,
        almacena la informacion y'''
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
                    'El archivo especificado no existe o posee un formato incompatible'
                )
            else:
                tab_i = None
                for i in range(6):
                    if not self.wat.isTabEnabled(i):
                        tab_i = i
                        self.wat.setTabEnabled(tab_i, True)
                        break
                if tab_i is None:
                    ok_act = QtGui.QMessageBox.question(
                        self, 'Slots ocupados...',
                        'Todos los slots de archivos ocupados,\n¿Desea reemplazar algún slot?'
                    )
                    if ok_act == QtGui.QMessageBox.Yes:
                        tabfull, ok_act = QtGui.QInputDialog.getInt(
                            self, 'Reemplazar slot', 'Ingrese el número del slot a reemplazar:',
                            1, 1, 6
                        )
                        if ok_act:
                            tab_i = tabfull-1
                if tab_i is not None:
                    self.set_spec(tab_i, sp_obj)
                    self.file[tab_i] = [
                        os.path.join(file_name[0]),
                        os.path.basename(file_name[0])
                    ]
                    self.wat.setCurrentIndex(tab_i)
                    self.upd_vlines()
                    print(self.file[tab_i])
                    if tab_i == 0:
                        self.wat.currentChanged.emit(self.wat.currentIndex())

    def set_spec(self, i, sp_obj):
        '''Almacena la información del archivo como un atributo de la ventana principal
        Grafica y acomoda la informacion en la interfaz'''
        self.s_data[i] = sp_obj
        if self.pld[i] is None:
            self.pld[i] = self.graf[i].plot(self.s_data[i].channels, self.s_data[i].counts)
            self.pld[i+6] = self.graf[i+6].plot(self.s_data[i].channels, self.s_data[i].counts)
        else:
            self.pld[i].setData(self.s_data[i].channels, self.s_data[i].counts)
            self.pld[i+6].setData(self.s_data[i].channels, self.s_data[i].counts)
        self.pld[i].setLogMode(False, False)
        self.pld[i+6].setLogMode(False, False)
        x_0 = -20
        x_1 = self.s_data[i].n_ch+20
        y_1 = 2**(np.ceil(np.log2(self.s_data[i].maxc)))
        y_0 = -0.005*y_1
        if y_1 < 16:
            y_1 = 16
        self.plt_region[i] = [False, x_0, x_1, y_0, y_1]
        self.roi_region[i] = [False, 0.02*x_1, 0.1*y_1, 0.1*x_1, 0.3*y_1]
        self.graf[i].setRange(None, self.plt_region[i][1:3], self.plt_region[i][3:], padding=0.0)
        self.vscrolls[i].setMaximum(28)
        self.vscrolls[i].setValue(self.vscrolls[i].maximum()-int(np.log2(y_1/16)))
        if self.log.isChecked():
            self.pld[i].setLogMode(False, True)
            self.pld[i+6].setLogMode(False, True)
            y_0 = -0.15
            y_1 = (np.ceil(np.log10(self.s_data[i].maxc)))
            self.plt_region[i] = [True, x_0, x_1, y_0, y_1]
            self.roi_region[i] = [True, 0.02*x_1, 0.1*y_1, 0.1*x_1, 0.3*y_1]
            self.vscrolls[i].setMaximum(9)
            self.vscrolls[i].setValue(self.vscrolls[i].maximum()+1-int(y_1))
        if self.zoom.isChecked():
            self.areas[i].addDock(self.dockzoom[i], 'bottom', self.dockgraf[i])
            self.graf[i].addItem(self.rois[i])
            self.set_roi(i)
        x_0, x_1, y_0, y_1 = self.plt_region[i][1:]
        self.rois[i].maxBounds = QtCore.QRectF(x_0, y_0, x_1-x_0, y_1-y_0)
        self.upd_plt_zone(i)
        self.upd_info(i, sp_obj)

    def upd_info(self, i, sp_obj):
        if sp_obj.eff is None:
            effic = [0, 0, 0, 0]
        else:
            effic = sp_obj.eff['coef']
        newvalues = [
            to_datetime(str(sp_obj.start)).strftime('%d/%m/%Y %H:%M:%S'),
            '{:.3f}'.format(sp_obj.real)+' s', '{:.3f}'.format(sp_obj.live)+' s',
            '{:.3f}'.format((sp_obj.real-sp_obj.live)/sp_obj.real*100)+' %',
            str(sp_obj.tot), str(sp_obj.maxc), str(sp_obj.n_ch), sp_obj.unit, *sp_obj.en_coef,
            *sp_obj.fw_coef[:2], *effic
        ]
        for ind, new in enumerate(newvalues):
            if ind < 8:
                self.infotree[i].adqchilds[ind].setValue(new)
            elif ind < 12:
                self.infotree[i].encalchilds[ind-8].setValue('{:.3E}'.format(new))
            elif ind < 14:
                self.infotree[i].fwcalchilds[ind-12].setValue('{:.3E}'.format(new))
            else:
                self.infotree[i].effcalchilds[ind-14].setValue('{:.3E}'.format(new))
        
    def v_click1(self, ev_cl):
        '''Accion desencadenada al hacer click en el grafico superior, que reposiciona
        la linea vertical (marcador) a la posicion del click'''
        if ev_cl.button() == QtCore.Qt.LeftButton:
            i = self.wat.currentIndex()
            try:
                a_pos = self.graf[i].plotItem.vb.mapDeviceToView(QtCore.QPointF(ev_cl.pos()))
            except:
                pass
            else:
                ch0 = round(a_pos.x())
                self.real_upd_vlines(i, ch0)

    def v_click2(self, ev_cl):
        '''Accion desencadenada al hacer click en el grafico inferior, que reposiciona
        la linea vertical (marcador) a la posicion del click'''
        if ev_cl.button() == QtCore.Qt.LeftButton:
            t_i = self.wat.currentIndex()
            try:
                a_pos = self.graf[t_i+6].plotItem.vb.mapDeviceToView(QtCore.QPointF(ev_cl.pos()))
            except:
                pass
            else:
                ch_sel = round(a_pos.x())
                self.real_upd_vlines(t_i, ch_sel)

    @QtCore.pyqtSlot()
    def gsp_browser(self):
        '''Abre la ventana de apertura de archivo con extencion *.GSP, lee el archivo,
        almacena la informacion'''
        file_name = QtGui.QFileDialog.getOpenFileName(
            self, 'Abrir Archivo', 'files/', 'GSP File(*.GSP *.gsp)'
        )
        return file_name
        # TODO: generar formato de archivo para el programa a usar

#%%
if __name__ == "__main__":
    print('Hola QT')
    app = QtGui.QApplication(sys.argv)
    window = MyApp()
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    window.show()
    sys.exit(app.exec_())
