# -*- coding: utf-8 -*-
"""
Created on Wed Jan 19 13:08:08 2022

TITLE: 

@author: Alejandro Condori aleja
E-mail: alejandrocondori2@gmail.com
"""

import qdarkstyle
import yaml
import pyqtgraph.parametertree.parameterTypes as pTypes
import numpy as np
import pyqtgraph as pg
import copy as cp
from datetime import datetime
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore
from pyqtgraph.parametertree import ParameterTree
from pyqtgraph.dockarea import Dock, DockArea
from readfile import read_cnf_file, Spec
from peaksearch import peak_search
from peakfitair import limits_calc, peak_analysis_ind, peak_analysis

# import this


# %%

class Cuantif_Wizard(QtWidgets.QWizard):
    NUM_PAGES = 5
    (StartPage, NuclidePage, ManualPage, AutoPage,
        ResultPage) = range(NUM_PAGES)
    
    def __init__(self, parent=None, sp_obj=None, en=None, eff=None, nucFile=None, calFile=None, dark_v=False, sp_name=None):
        QtWidgets.QWizard.__init__(self, parent)
        self.sp_obj = sp_obj
        self.Start_Page = Start_Page(self, dark_v, en, eff, calFile)
        self.Nuclide_Page = Nuclide_Page(self, dark_v, en, eff, nucFile)
        self.Manual_Page = Manual_Page(self, dark_v, self.sp_obj, en, eff)
        self.Auto_Page = Auto_Page(self, dark_v, self.sp_obj, en, eff)
        self.Result_Page = Result_Page(self, dark_v, sp_name)
        # set pages
        self.setPage(self.StartPage, self.Start_Page)
        self.setPage(self.NuclidePage, self.Nuclide_Page)
        self.setPage(self.ManualPage, self.Manual_Page)
        self.setPage(self.AutoPage, self.Auto_Page)
        self.setPage(self.ResultPage, self.Result_Page)
        # self.file = file
        self.setStartId(self.StartPage)
        # images won't show in Windows 7 if style not set
        self.setWizardStyle(1)
        self.setOption(self.HaveHelpButton, True)
        self.setWindowTitle(self.tr("Análisis y Cuantificación"))
        self.setOptions(
            QtWidgets.QWizard.HaveHelpButton|
            QtWidgets.QWizard.HelpButtonOnRight|
            QtWidgets.QWizard.NoBackButtonOnLastPage|
            QtWidgets.QWizard.NoBackButtonOnStartPage
        )
        self.Nuclide_Page.end.connect(self.nuclidetocalc)
        self.Nuclide_Page.endNuclide.connect(self.selectPath)
        # self.Manual_Page.iniciar.connect(self.manual)
        self.Manual_Page.endManual.connect(self.manual_end)
        self.Auto_Page.endAuto.connect(self.auto_end)
        
        # 0:Watermark(left) 1:Logo(Header) 2:Banner(Fondo Header) 3:OnlyMac
        # self.setPixmap(
        #     QtWidgets.QWizard.BannerPixmap, # 2
        #     QtGui.QPixmap("icons/banner.png")
        # )
        # self.setPixmap(
        #     QtWidgets.QWizard.WatermarkPixmap, # 0
        #     QtGui.QPixmap("icons/tc45_3.png").scaledToWidth(65)
        # )
        # set up help messages
        # self._lastHelpMsg = ''
        # self._helpMsgs = self._createHelpMsgs()
        # self.helpRequested.connect(self._showHelp)

    def selectPath(self, value):
        self.Auto_Page.isManual = value

    def nuclidetocalc(self, nuc):
        self.nucToCalc = nuc
        self.Manual_Page.nucToCalc = self.nucToCalc
        self.Auto_Page.nucToCalc = self.nucToCalc

    def manual(self):
        self.Manual_Page.nucToCalc = self.nucToCalc

    def manual_end(self, lims, sp_obj):
        self.Auto_Page.limits = lims
        self.Auto_Page.sp_obj = sp_obj

    def auto_end(self, obj, eff, datos):
        self.Result_Page.nucToCalc = self.nucToCalc
        self.Result_Page.sp_obj = obj
        self.Result_Page.datos = datos
        self.Result_Page.eff = eff
        

class Start_Page(QtWidgets.QWizardPage):
    
    def __init__(self, parent=None, dark_v=False, en=None, eff=None, calFile=None):
        QtWidgets.QWizardPage.__init__(self, parent)
        self.setTitle(
            '<html><head/><body><p><span style="font-size:16pt; '
            'font-weight:600">Análisis y Cuantificación de Muestras '
            'de Aire</span></p></body></html>'
        )
        self.setSubTitle(
            '<html><head/><body><p><span style="font-size:11pt; '
            'font-weight:600">1. Verificación de los datos de calibración'
            '</span></p></body></html>'
        )
        # self.setPixmap(
        #     QtWidgets.QWizard.LogoPixmap, # 1
        #     QtGui.QPixmap("icons/tc45_3.png").scaledToWidth(65)
        # )
        if not dark_v:
            
            self.setPixmap(
                QtWidgets.QWizard.BannerPixmap, # 2
                QtGui.QPixmap("icons/banner2.png").scaledToHeight(90)
            )
        self.setPixmap(
            QtWidgets.QWizard.WatermarkPixmap, # 0
            QtGui.QPixmap("icons/watermark.png").scaledToWidth(200)
        )
        fs = 10 # Font Size
        self.en = en
        self.eff = eff
        self.calFile = calFile
        if en is not None:
            self.ener_cal = True
        else:
            self.ener_cal = False
        if eff is not None:
            self.eff_cal = True
        else:
            self.eff_cal = False
        self.setStyleSheet(
            'QGroupBox{font-size: 13px;}'
        )
        group1 = QtWidgets.QGroupBox('Importante')
        group2 = QtWidgets.QGroupBox('Curvas de Calibración')
        # group2.setFlat(True)
        self.enlabel = QtWidgets.QLabel('Energía: ')
        self.efflabel = QtWidgets.QLabel('Eficiencia: ')
        spacer1 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer2 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        self.eff_btn = QtWidgets.QPushButton('Eficiencia por defecto')
        self.eff_btn.setAutoDefault(False)
        label1 = QtWidgets.QLabel(
            '<html><head/><body><p align="justify"><span style='
            f'" font-size:{fs+1}pt;">Asistente para realizar el análisis '
            'y cuantificación de espectros gamma de muestras de aire '
            'tomadas con filtro de carbon activado TC-45</span>'
            '</p></body></html>' # <p align="justify"><br/></p>
        )
        label1.setWordWrap(True)
        label2 = QtWidgets.QLabel(
            '<html><head/><body><p align="justify"><span style=" font-size:'
            f'{fs}pt;">A continuación se muestran los datos de calibración de '
            'energías y eficiencia.</span></p><p align="justify"><span style='
            f'" font-size:{fs}pt;">Verificar que estos datos en correctos. '
            f'</span></p><p align="justify"><span style=" font-size:{fs}pt;">'
            'En caso esten incorrectos o estén incompletos, se recomienda '
            'realizar primero la calibración.</span></p><p align="justify">'
            f'<span style=" font-size:{fs}pt;">Se puede utilizar el botón '
            '&quot;Eficiencia por defecto&quot; para cargar automáticamente '
            'el archivo por defecto de calibración de eficiencia para una '
            'fuente de tipo &quot;Filtro de Aire TC-45&quot; en posición '
            'estándar dentro del blindaje.</span></p></body></html>'
        )
        label2.setWordWrap(True)
        lay1 = QtWidgets.QVBoxLayout()
        lay2 = QtWidgets.QVBoxLayout()
        lay3 = QtWidgets.QVBoxLayout()
        lay4 = QtWidgets.QHBoxLayout()
        lay1.addWidget(label1)
        lay1.addWidget(group1)
        self.setLayout(lay1)
        group1.setLayout(lay2)
        lay2.addWidget(label2)
        lay2.addWidget(group2)
        group2.setLayout(lay3)
        lay3.addWidget(self.enlabel)
        lay3.addWidget(self.efflabel)
        lay2.addLayout(lay4)
        lay4.addItem(spacer1)
        lay4.addWidget(self.eff_btn)
        lay4.addItem(spacer2)
        self.eff_btn.clicked.connect(self.eff_btn_clicked)

    def eff_btn_clicked(self):
        self.ener_cal = True
        self.eff_cal = True
        self.completeChanged.emit()

    def isComplete(self):
        if self.ener_cal and self.eff_cal:
            return True
        else:
            return False

    def nextId(self):
        return Cuantif_Wizard.NuclidePage
        # if self.ener_cal and self.eff_cal:
        #     return Cuantif_Wizard.NuclidePage
        # else:
        #     return 0

class Nuclide_Page(QtWidgets.QWizardPage):
    end = QtCore.pyqtSignal(dict)
    endNuclide = QtCore.pyqtSignal(bool)

    def __init__(self, parent=None, dark_v=False, en=None, eff=None, file=None):
        QtWidgets.QWizardPage.__init__(self, parent)
        self.setStyleSheet(
            'QCheckBox{font-size: 15px;};'
            # 'font-size: 16pt;'
        )
        self.setTitle(
            '<html><head/><body><p><span style="font-size:16pt; '
            'font-weight:600">Análisis y Cuantificación de Muestras '
            'de Aire</span></p></body></html>'
        )
        self.setSubTitle(
            '<html><head/><body><p><span style="font-size:11pt; '
            'font-weight:600">2. Elección del radioisótopo a cuantificar'
            '</span></p></body></html>'
        )
        self.file = file
        if not dark_v:
            self.setPixmap(
                QtWidgets.QWizard.BannerPixmap, # 2
                QtGui.QPixmap("icons/banner2.png").scaledToHeight(90)
            )
        self.setPixmap(
            QtWidgets.QWizard.WatermarkPixmap, # 0
            QtGui.QPixmap("icons/watermark.png").scaledToWidth(200)
        )
        fs = 10
        lay1 = QtWidgets.QVBoxLayout()
        lay2 = QtWidgets.QHBoxLayout()
        # lay3 = QtWidgets.QVBoxLayout()
        label1 = QtWidgets.QLabel(
            '<html><head/><body><p align="justify"><span style=" font-size:'
            f'{fs}pt;">Seleccione el radioisótopo que desea cuantificar en '
            'el espectro gamma que esta siendo analizado.</span></p></span>'
            f'</p><p align="justify"><span style=" font-size:{fs}pt;">Se '
            'cuantificará utilizando el fotopico más representativo. '
            f'</span></p></body></html>'
        )
        label1.setWordWrap(True)
        label2 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:10pt;"> '
            'Lista de radisótopos:</span></p></body></html>'
        )
        label2.setIndent(6)
        area = DockArea2()
        nuclides = Dock2("Nucleidos", size=(100, 10), hideTitle=True)
        # nuclides.hideTitleBar()
        info = Dock2("Información", size=(100, 50), hideTitle=True)
        # info.hideTitleBar()
        area.addDock(nuclides, 'top')
        area.addDock(info, 'bottom', nuclides)
        spacer1 = QtWidgets.QSpacerItem(
            4, 2,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        self.check = QtWidgets.QCheckBox('ROI/Delimitación Manual')
        self.list_wid = QtWidgets.QListWidget()
        self.tree = ParameterTree()
        self.nuctree = NuclidePar(name = 'nucinfo')
        info.addWidget(self.tree)
        self.tree.setParameters(self.nuctree, showTop=False)
        
        self.list_items = []
        self.list_info = []
        # ensambling
        self.setLayout(lay1)
        lay1.addWidget(label1)
        lay1.addWidget(area)
        lay1.addLayout(lay2)
        lay2.addItem(spacer1)
        lay2.addWidget(self.check)
        # nuclides.setLayout(lay3)
        nuclides.addWidget(label2)
        nuclides.addWidget(self.list_wid)
        self.data = dict()
        self.item_key = []
        self.item_obj = []
        # self.list_wid.itemDoubleClicked.connect(self.onClicked)
        self.list_wid.currentItemChanged.connect(self.onClicked) 

    def initializePage(self):
        self.get_nuclides()

    def get_nuclides(self):
        self.data.update(yaml.safe_load(open(self.file)))
        for i in self.data:
            self.item_key.append(i)
            obj = QtWidgets.QListWidgetItem(self.data[i]['name'])
            self.item_obj.append(obj)
            self.list_wid.addItem(obj)
        self.list_wid.setCurrentRow(0)

    def onClicked(self, item):
        ind = self.item_obj.index(item)
        key = self.item_key[ind]
        info = self.data[key]
        self.current = {key:info}
        
        name = f"{info['name']} ({key})"
        z = f"{info['Z']}"
        a = f"{info['A']}"
        hlt = info['hl']['type'] # 0:segs 1:min 2:hrs 3:dias 4:años
        if hlt == 0:
            un = 'segundos'
        elif hlt == 1:
            un = 'minutos'
        elif hlt == 2:
            un = 'horas'
        elif hlt == 3:
            un = 'dias'
        else:
            un = 'años'
        hl = f"{info['hl']['value']} {un}"
        dect = info['decay'] # 0:gamma(IT) 1:beta- 2:beta+ 3:alpha
        dec = ''
        for i in dect:
            if i == 0:
                dec += 'Gamma (IT) '
            elif i == 1:
                dec += 'Beta- '
            elif i == 2:
                dec += 'Beta+ (EC) '
            elif i == 3:
                dec += 'Alpha'
        self.nuctree.addData(name, z, a, hl, dec)
        self.nuctree.addGammas(info['gamma'])

    def nextId(self):
        self.end.emit(self.current)
        if self.check.isChecked():
            self.endNuclide.emit(True)
            return Cuantif_Wizard.ManualPage
        else:
            self.endNuclide.emit(False)
            return Cuantif_Wizard.AutoPage

class Manual_Page(QtWidgets.QWizardPage):
    iniciar = QtCore.pyqtSignal()
    endManual = QtCore.pyqtSignal(list, Spec)
    
    def __init__(self, parent=None, dark_v=False, sp_obj = None, en=None, eff=None, file=None):
        QtWidgets.QWizardPage.__init__(self, parent)
        self.sp_obj = sp_obj
        self.nucToCalc = None
        self.limits = None
        fs = 10
        self.plot_data = None
        self.defs = None
        lay1 = QtWidgets.QVBoxLayout()
        lay2 = QtWidgets.QHBoxLayout()
        lay3 = QtWidgets.QVBoxLayout()
        lay4 = QtWidgets.QHBoxLayout()
        lay5 = QtWidgets.QHBoxLayout()
        lay6 = QtWidgets.QHBoxLayout()
        self.setStyleSheet(
            'QSpinBox{font-size: 15px;};'
            # 'font-size: 16pt;'
        )
        self.setTitle(
            '<html><head/><body><p><span style="font-size:16pt; '
            'font-weight:600">Análisis y Cuantificación de Muestras '
            'de Aire</span></p></body></html>'
        )
        self.setSubTitle(
            '<html><head/><body><p><span style="font-size:11pt; '
            'font-weight:600">2.1 Elección Manual de límites'
            '</span></p></body></html>'
        )
        if not dark_v:
            self.setPixmap(
                QtWidgets.QWizard.BannerPixmap, # 2
                QtGui.QPixmap("icons/banner2.png").scaledToHeight(90)
            )
        # self.setPixmap(
        #     QtWidgets.QWizard.WatermarkPixmap, # 0
        #     QtGui.QPixmap("icons/watermark.png").scaledToWidth(200)
        # )
        label1 = QtWidgets.QLabel(
            '<html><head/><body><p align="justify"><span style=" font-size:'
            f'{fs}pt;">Seleccione el rango del fotopico para calcular el  '
            'área bajo la curva.</span></p></span>'
            f'</p><p align="justify"><span style=" font-size:{fs}pt;">El '
            'marcador izquierdo está en rojo y el derecho en azul. Procure '
            'seleccionar por completo el fotpico y una pequeña región extra '
            f'para la estimación del fondo</span></p></body></html>'
        )
        bar_wid = QtWidgets.QWidget()
        bar_wid.setStyleSheet('background-color: black')
        bar_wid.setFixedHeight(25)

        # Partes y armado de la barra
        texts = ['Marker : ', '', 'Canal : ', '', 'Energía : ', '', 'Cuentas :', '']
        bar_lay = QtWidgets.QHBoxLayout(bar_wid)
        bar_lay.setContentsMargins(10, 0, 10, 0)
        self.bar = [QtWidgets.QLabel(f'{texts[i]}') for i in range(8)]
        for i in range(8):
            bar_lay.addWidget(self.bar[i])
        for j in range(4):
            self.bar[j*2].setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
            self.bar[j*2].setStyleSheet(
                'color:cyan; font-weight: bold; background-color: black'
            )
            self.bar[j*2+1].setAlignment(
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            )
            self.bar[j*2+1].setStyleSheet(
                'color: yellow; font-weight: bold; background-color: black'
            )
        
        label1.setWordWrap(True)
        label2 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Centroide : </span></p></body></html>'
        )
        label2.setMinimumWidth(130)
        label3 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Límite Inferior : </span></p></body></html>'
        )
        label3.setMinimumWidth(130)
        label4 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Límite Superior : </span></p></body></html>'
        )
        label4.setMinimumWidth(130)
        self.label5 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            '0</span></p></body></html>'
        )
        self.label5.setMinimumWidth(80)
        self.label5.setAlignment(
            QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter
        )
        self.lefSpin = QtWidgets.QSpinBox()
        self.lefSpin.setMaximum(4096)
        self.lefSpin.setAlignment(
            QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter
        )
        self.lefSpin.setMinimumWidth(80)
        self.lefSpin.setSuffix(' Ch')
        self.rigSpin = QtWidgets.QSpinBox()
        self.rigSpin.setMaximum(4096)
        self.rigSpin.setAlignment(
            QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter
        )
        self.rigSpin.setMinimumWidth(80)
        self.rigSpin.setSuffix(' Ch')
        self.defButtom = QtWidgets.QPushButton('Valores por Defecto')
        self.defButtom.setStyleSheet(
            "QPushButton{font-size: 15px}"
        )
        spacer1 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer2 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer3 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer4 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer5 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer6 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer7 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        area = DockArea2()
        plotDock = Dock2("Plot", size=(100, 10), hideTitle=True)
        dataDock = Dock2("Datos", size=(100, 50), hideTitle=True)
        self.graf = pg.PlotWidget()
        self.graf.setMinimumHeight(300)
        self.graf.hideAxis('left')
        self.graf.hideAxis('bottom')
        self.lefLine = pg.InfiniteLine(
            angle=90,
            movable=True,
            pen='red',
            hoverPen='orange'
        )
        self.rigLine = pg.InfiniteLine(
            angle=90,
            movable=True,
            pen='blue',
            hoverPen='cyan'
        )
        
        self.graf.addItem(self.lefLine, ignoreBounds=True)
        self.graf.addItem(self.rigLine, ignoreBounds=True)
        area.addDock(plotDock, 'top')
        area.addDock(dataDock, 'bottom', plotDock)
        self.setLayout(lay1)
        lay1.addWidget(label1)
        lay1.addWidget(area)
        # plotDock.layout.addLayout(lay2, 0, 0)
        plotDock.addWidget(bar_wid)
        plotDock.addWidget(self.graf)
        dataDock.layout.addLayout(lay5, 0, 0)
        lay5.addItem(spacer1)
        lay5.addLayout(lay3)
        lay5.addItem(spacer2)
        
        lay3.addItem(spacer3)
        lay3.addLayout(lay2)
        lay3.addItem(spacer4)
        lay3.addLayout(lay4)
        lay3.addItem(spacer5)
        lay3.addLayout(lay6)
        lay3.addItem(spacer6)
        lay3.addWidget(self.defButtom)
        lay3.addItem(spacer7)
        
        lay2.addWidget(label2)
        lay2.addWidget(self.label5)
        
        lay4.addWidget(label3)
        lay4.addWidget(self.lefSpin)
        
        lay6.addWidget(label4)
        lay6.addWidget(self.rigSpin)
        
        self.lefLine.sigPositionChanged.connect(self.upd_lefLine)
        self.rigLine.sigPositionChanged.connect(self.upd_rigLine)
        self.lefSpin.valueChanged.connect(self.upd_lefSpin)
        self.rigSpin.valueChanged.connect(self.upd_rigSpin)
        self.defButtom.clicked.connect(self.upd_values)

    def initializePage(self):
        self.iniciar.emit()
        c = self.sp_obj
        nuc = self.nucToCalc
        key = [*nuc][0]
        pk_en = nuc[key]['gamma'][0][0]
        pk_ch = pk_en/c.en_coef[2]
        fwhmc = c.fwhm/c.en_coef[2]
        encal = c.en_coef
        c.peaks, c.der_2, c.der_1 = peak_search(
            c.counts,
            fwhmc,
            3,
            encal,
            ch_ini=pk_ch-3*fwhmc[int(pk_ch)],
            ch_end=pk_ch+3*fwhmc[int(pk_ch)]
        )
        c.peaks = np.array(c.peaks)
        pos = round(c.peaks[0][0])
        self.limits = limits_calc(c, fwhmc)
        if self.plot_data is None:
            self.plot_data = self.graf.plot(
                self.sp_obj.channels,
                self.sp_obj.counts
            )
        else:
            self.plot_data.setData(
                self.sp_obj.channels,
                self.sp_obj.counts
            )
        self.plot_data.setLogMode(False, True)
        x_0 = (3 * self.limits[0][0] - self.limits[0][1]) / 2
        x_1 = (3 * self.limits[0][1] - self.limits[0][0]) / 2
        y_1 = (np.ceil(np.log10(self.sp_obj.counts[pos])))-0.8
        t = self.sp_obj.counts[int(x_1)]
        if t>0:
            y_0 = (np.log10(t))-0.1
        else:
            y_0 = -0.1
        self.graf.setRange(
            None,
            [x_0, x_1],
            [y_0, y_1],
            padding=0.0
        )
        
        # y_0 = -0.15
        # y_1 = (np.ceil(np.log10(self.data.maxc)))
        # self.plt_region = [True, x_0, x_1, y_0, y_1]
        
        
        
        self.rigLine.setPos(self.limits[0][1])
        self.lefLine.setPos(self.limits[0][0])
        self.defs = cp.deepcopy(self.limits)
        '<html><head/><body><p><span style="font-size:12pt;"> '
        '0</span></p></body></html>'
        a = str(round(self.sp_obj.energy[pos-1], 2)) + ' ' + self.sp_obj.unit
        self.label5.setText(
            '<html><head/><body><p><span style="font-size:11pt;"> '
            f'{a}</span></p></body></html>'
        )

    @QtCore.pyqtSlot()
    def upd_values(self):
        self.lefSpin.setValue(self.defs[0][0])
        self.rigSpin.setValue(self.defs[0][1])

    @QtCore.pyqtSlot()
    def upd_lefSpin(self):
        pos = self.lefSpin.value()
        if pos < 1:
            pos = 1
        if pos > round(self.rigLine.value()):
            pos = round(self.rigLine.value()) - 1
        self.rigSpin.setMinimum(pos+1)
        self.lefLine.setPos(pos)
        self.limits[0][0] = pos

    @QtCore.pyqtSlot()
    def upd_rigSpin(self):
        pos = self.rigSpin.value()
        if pos < round(self.lefLine.value()):
            pos = round(self.lefLine.value()) + 1
        if pos > 4096:
            pos = 4096
        self.lefSpin.setMaximum(pos-1)
        self.rigLine.setPos(pos)
        self.limits[0][1] = pos

    @QtCore.pyqtSlot()
    def upd_lefLine(self):
        pos = round(self.lefLine.value())
        if pos < 1:
            pos = 1
        if pos > round(self.rigLine.value()):
            pos = round(self.rigLine.value()) - 1
        self.lefLine.setPos(pos)
        self.lefSpin.setValue(pos)
        self.bar[1].setText('Izquierda')
        self.bar[3].setText(str(pos))
        self.bar[5].setText(
            str(round(self.sp_obj.energy[pos-1], 2)) + ' ' + self.sp_obj.unit
        )
        self.bar[7].setText(str(int(self.sp_obj.counts[pos-1])))

    @QtCore.pyqtSlot()
    def upd_rigLine(self):
        pos = round(self.rigLine.value())
        if pos < round(self.lefLine.value()):
            pos = round(self.lefLine.value()) + 1
        if pos > 4096:
            pos = 4096
        self.rigLine.setPos(pos)
        self.rigSpin.setValue(pos)
        self.bar[1].setText('Derecha')
        self.bar[3].setText(str(pos))
        self.bar[5].setText(
            str(round(self.sp_obj.energy[pos-1], 2)) + ' ' + self.sp_obj.unit
        )
        self.bar[7].setText(str(int(self.sp_obj.counts[pos-1])))

    def nextId(self):
        self.endManual.emit(self.limits, self.sp_obj)
        return Cuantif_Wizard.AutoPage
        

class Auto_Page(QtWidgets.QWizardPage):
    endAuto = QtCore.pyqtSignal(Spec, float, list)
    
    def __init__(self, parent=None, dark_v=False, sp_obj=None, en=None, eff=None, file=None):
        QtWidgets.QWizardPage.__init__(self, parent)
        self.isManual = False
        self.limits = None
        self.sp_obj = sp_obj
        self.nucToCalc = None
        self.plot_data = None
        self.plot_bkg = None
        self.plot_fit = None
        fs = 10
        self.setTitle(
            '<html><head/><body><p><span style="font-size:16pt; '
            'font-weight:600">Análisis y Cuantificación de Muestras '
            'de Aire</span></p></body></html>'
        )
        self.setSubTitle(
            '<html><head/><body><p><span style="font-size:11pt; '
            'font-weight:600">3. Resultados de Análisis de Pico'
            '</span></p></body></html>'
        )
        if not dark_v:
            self.setPixmap(
                QtWidgets.QWizard.BannerPixmap, # 2
                QtGui.QPixmap("icons/banner2.png").scaledToHeight(90)
            )
        lay1 = QtWidgets.QVBoxLayout()
        lay2 = QtWidgets.QHBoxLayout()
        lay3 = QtWidgets.QVBoxLayout()
        lay4 = QtWidgets.QHBoxLayout()
        lay5 = QtWidgets.QHBoxLayout()
        lay6 = QtWidgets.QHBoxLayout()
        lay7 = QtWidgets.QHBoxLayout()
        lay8 = QtWidgets.QHBoxLayout()
        self.setStyleSheet(
            'QDoubleSpinBox{font-size: 15px;};'
            # 'font-size: 16pt;'
        )
        self.label1 = QtWidgets.QLabel(
            '<html><head/><body><p align="justify"><span style=" font-size:'
            f'{fs}pt;">En la presente página se aprecia los resultados del '
            f'análisis del fotopico de {fs}.</span></p></span>'
            f'</p><p align="justify"><span style=" font-size:{fs}pt;">En el '
            'gráfico se aprecian la data con puntos, la curva de fiteo en azul'
            ' y el fondo en gris.</span></p></span></p><p align="justify">'
            f'<span style=" font-size:{fs}pt;">A continuación completar '
            'los datos del muestreo de aire</span></p></body></html>'
        )
        bar_wid = QtWidgets.QWidget()
        bar_wid.setStyleSheet('background-color: black')
        bar_wid.setFixedHeight(25)
        
        # Partes y armado de la barra
        texts = ['Marker : ', '', 'Canal : ', '', 'Energía : ', '', 'Cuentas :', '']
        bar_lay = QtWidgets.QHBoxLayout(bar_wid)
        bar_lay.setContentsMargins(10, 0, 10, 0)
        self.bar = [QtWidgets.QLabel(f'{texts[i]}') for i in range(8)]
        for i in range(8):
            bar_lay.addWidget(self.bar[i])
        for j in range(4):
            self.bar[j*2].setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
            self.bar[j*2].setStyleSheet(
                'color:cyan; font-weight: bold; background-color: black'
            )
            self.bar[j*2+1].setAlignment(
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            )
            self.bar[j*2+1].setStyleSheet(
                'color: yellow; font-weight: bold; background-color: black'
            )
        
        self.label1.setWordWrap(True)
        label2 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Centroide : </span></p></body></html>'
        )
        label2.setMinimumWidth(130)
        label3 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Cuentas Netas : </span></p></body></html>'
        )
        label3.setMinimumWidth(130)
        label4 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Inicio Adq. Espectro : </span></p></body></html>'
        )
        label4.setMinimumWidth(130)
        label7 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Inicio Muestreo Aire : </span></p></body></html>'
        )
        label7.setMinimumWidth(130)
        label8 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Fin Muestreo Aire  : </span></p></body></html>'
        )
        label8.setMinimumWidth(130)
        self.label5 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            '0 keV</span></p></body></html>'
        )
        self.label5.setMinimumWidth(80)
        self.label5.setAlignment(
            QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter
        )
        self.npa = QtWidgets.QDoubleSpinBox()
        # self.npa = MySpinBox()
        self.npa.setMaximum(99999999999)
        self.npa.setDecimals(0)
        self.npa.setMinimumWidth(80)
        self.npa.setAlignment(
            QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter
        )
        self.npa.setSuffix(' cts')
        self.npa.setStyleSheet(
            "QDoubleSpinBox{font-size: 15px}"
        )
        # self.npa.setStyleSheet(
        #     "MySpinBox{font-size: 15px}"
        # )
        self.npa.setButtonSymbols(2)
        self.npa.setReadOnly(True)
        label9 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Caudal inicial  : </span></p></body></html>'
        )
        label9.setMinimumWidth(130)
        label10 = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Caudal Final  : </span></p></body></html>'
        )
        label10.setMinimumWidth(130)
               
        self.iniSpin = QtWidgets.QDoubleSpinBox()
        self.iniSpin.setDecimals(1)
        self.iniSpin.setSingleStep(0.5)
        self.iniSpin.setMaximum(4096)
        self.iniSpin.setAlignment(
            QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter
        )
        self.iniSpin.setMinimumWidth(80)
        self.iniSpin.setSuffix(' L/min')
        self.iniSpin.setValue(50)
        self.finSpin = QtWidgets.QDoubleSpinBox()
        self.finSpin.setDecimals(1)
        self.finSpin.setSingleStep(0.5)
        self.finSpin.setMaximum(4096)
        self.finSpin.setAlignment(
            QtCore.Qt.AlignRight|QtCore.Qt.AlignTrailing|QtCore.Qt.AlignVCenter
        )
        self.finSpin.setMinimumWidth(80)
        self.finSpin.setSuffix(' L/min')
        self.finSpin.setValue(50)
        
        self.defButtom = QtWidgets.QPushButton('Verificación Anemométrica')
        self.defButtom.setStyleSheet(
            "QPushButton{font-size: 15px}"
        )
        self.defButtom.setEnabled(False)
        self.groupAne = QtWidgets.QGroupBox('Verificación Anemométrica')
        self.groupAne.setStyleSheet(
            "QGroupBox{font-size: 15px}"
        )
        labelAne = QtWidgets.QLabel(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            'Velocidad Aire Promedio : </span></p></body></html>'
        )
        self.velAne = QtWidgets.QDoubleSpinBox()
        self.velAne.setMinimum(1)
        self.velAne.setMaximum(100)
        self.velAne.setSuffix(" m/s")
        self.velAne.setDecimals(2)
        self.velAne.setSingleStep(0.5)
        self.velAne.setValue(10.5)
        self.groupAne.setEnabled(False)
        
        self.date1 = QtWidgets.QDateTimeEdit()
        self.date1.setReadOnly(True)
        self.date1.setButtonSymbols(2)
        self.date1.setDisplayFormat('dd/MM/yyyy hh:mm:ss AP')
        self.date2 = QtWidgets.QDateTimeEdit()
        self.date2.setDisplayFormat('dd/MM/yyyy hh:mm:ss AP')
        self.date3 = QtWidgets.QDateTimeEdit()
        self.date3.setDisplayFormat('dd/MM/yyyy hh:mm:ss AP')
        
        spacer1 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer2 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer3 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer4 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer5 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer6 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer7 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer8 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Minimum,
            QtWidgets.QSizePolicy.Expanding
        )
        spacer9 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer10 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer11 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer12 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer13 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        spacer14 = QtWidgets.QSpacerItem(
            40, 20,
            QtWidgets.QSizePolicy.Expanding,
            QtWidgets.QSizePolicy.Minimum
        )
        
        area = DockArea2()
        plotDock = Dock2("Plot", size=(100, 10), hideTitle=True)
        dataDock = Dock2("Datos", size=(100, 50), hideTitle=True)
        self.graf = pg.PlotWidget()
        self.graf.setMinimumHeight(275)
        self.graf.hideAxis('left')
        self.graf.hideAxis('bottom')
        self.lefLine = pg.InfiniteLine(
            angle=90,
            movable=True,
            pen='red',
            hoverPen='orange'
        )
        self.rigLine = pg.InfiniteLine(
            angle=90,
            movable=True,
            pen='blue',
            hoverPen='cyan'
        )
        
        # self.graf.addItem(self.lefLine, ignoreBounds=True)
        # self.graf.addItem(self.rigLine, ignoreBounds=True)
        area.addDock(plotDock, 'top')
        area.addDock(dataDock, 'bottom', plotDock)
        group = QtWidgets.QGroupBox()
        self.radioChi = QtWidgets.QRadioButton('Chimenea')
        self.radioChi.setStyleSheet(
            "QRadioButton{font-size: 15px}"
        )
        self.radioLoc = QtWidgets.QRadioButton('Locales')
        self.radioLoc.setStyleSheet(
            "QRadioButton{font-size: 15px}"
        )
        self.radioLoc.setChecked(True)        
        self.setLayout(lay1)
        lay1.addWidget(self.label1)
        lay1.addWidget(area)
        # plotDock.layout.addLayout(lay2, 0, 0)
        # plotDock.addWidget(bar_wid)
        plotDock.addWidget(self.graf)
        dataDock.layout.addLayout(lay5, 0, 0)
        lay5.addItem(spacer1)
        lay5.addLayout(lay3)
        lay5.addItem(spacer2)
        
        lay3.addItem(spacer3)
        lay3.addLayout(lay2)
        lay3.addItem(spacer4)
        lay3.addLayout(lay4)
        lay3.addItem(spacer5)
        lay3.addLayout(lay6)
        lay3.addItem(spacer6)
        lay3.addLayout(lay7)
        lay3.addItem(spacer8)
        lay3.addWidget(self.groupAne)
        lay3.addItem(spacer7)
        
        lay9 = QtWidgets.QHBoxLayout()
        self.groupAne.setLayout(lay9)
        lay9.addItem(spacer13)
        lay9.addWidget(labelAne)
        lay9.addWidget(self.velAne)
        lay9.addItem(spacer14)
        wids = [
            label2, self.label5, label4, self.date1, label3, self.npa, 
            label7, self.date2, label9, self.iniSpin, label8, self.date3,
            label10, self.finSpin, self.radioChi, self.radioLoc
        ]
        for j,k in enumerate(wids):
            k.setMinimumWidth(140)
            if j<14:
                k.setMinimumHeight(25)
            if j in [3, 7, 11]:
                k.setMinimumWidth(180)
                k.setAlignment(
                    QtCore.Qt.AlignCenter
                )
                if j in [7, 11]:
                    k.setCalendarPopup(True)
                k.setStyleSheet(
                    "QDateTimeEdit{font-size: 13px}"
                )
            elif j in [1, 5, 9, 13]:
                k.setMinimumWidth(100)
            elif j in [0, 4, 8, 12]:
                k.setMinimumWidth(120)
        lay2.addWidget(label2)
        lay2.addWidget(self.label5)
        lay2.addItem(spacer9)
        lay2.addWidget(label4)
        lay2.addWidget(self.date1)
        
        lay4.addWidget(label3)
        lay4.addWidget(self.npa)
        lay4.addItem(spacer10)
        lay4.addWidget(label7)
        lay4.addWidget(self.date2)
        
        lay6.addWidget(label9)
        lay6.addWidget(self.iniSpin)
        lay6.addItem(spacer11)
        lay6.addWidget(label8)
        lay6.addWidget(self.date3)
        
        lay7.addWidget(label10)
        lay7.addWidget(self.finSpin)
        lay7.addItem(spacer12)
        lay7.addWidget(group)
        # lay7.addItem(spacer13)
        group.setLayout(lay8)
        lay8.addWidget(self.radioChi)
        lay8.addWidget(self.radioLoc)
        
        self.radioChi.clicked.connect(self.change_selection)
        self.radioLoc.clicked.connect(self.change_selection)
        self.date2.dateTimeChanged.connect(self.date2_change)
        self.date3.dateTimeChanged.connect(self.date3_change)
        
    def date2_change(self, a):
        self.date3.setMinimumDateTime(a)
    
    def date3_change(self, a):
        self.date2.setMaximumDateTime(a)
        
    def change_selection(self):
        if self.radioChi.isChecked():
            self.groupAne.setEnabled(True)
        else:
            self.groupAne.setEnabled(False)

    def initializePage(self):
        fs = 10
        nuc = self.nucToCalc
        key = [*nuc][0]
        name = nuc[key]['name']
        c = self.sp_obj
        fwhmc = c.fwhm/c.en_coef[2]
        # chann = np.arange(1,4097)
        self.label1.setText(
            '<html><head/><body><p align="justify"><span style=" font-size:'
            f'{fs}pt;">En la presente página se aprecia los resultados del '
            f'análisis del fotopico de {name}.</span></p></span>'
            f'</p><p align="justify"><span style=" font-size:{fs}pt;">En el '
            'gráfico se aprecian la data con puntos, la curva de fiteo en azul'
            ' y el fondo en gris.</span></p></span></p><p align="justify">'
            f'<span style=" font-size:{fs}pt;">A continuación completar con'
            'los datos del muestreo de aire.</span></p></body></html>'
        )
        if self.isManual:
            c.peak_dat, c.bkg = peak_analysis_ind(c, fwhmc, lims=self.limits)
            # self.x1 = c.peak_dat
        else:
            fwhmc = c.fwhm/c.en_coef[2]
            encal = c.en_coef
            pk_en = nuc[key]['gamma'][0][0]
            pk_ch = pk_en/c.en_coef[2]
            c.peaks, c.der_2, c.der_1 = peak_search(
                c.counts,
                fwhmc,
                3,
                encal,
                ch_ini=pk_ch-3*fwhmc[int(pk_ch)],
                ch_end=pk_ch+3*fwhmc[int(pk_ch)]
            )
            c.peaks = np.array(c.peaks)
            c.peak_dat, c.bkg = peak_analysis(c, fwhmc)
            # self.x2 = c.peak_dat
        if self.plot_data is None:
            self.plot_data = self.graf.plot(
                self.sp_obj.channels,
                self.sp_obj.counts,
                pen=None,
                symbolBrush=(255,255,0),
                symbolPen=None,
                symbolSize=3
            )
        else:
            self.plot_data.setData(
                self.sp_obj.channels,
                self.sp_obj.counts,
                pen=None,
                symbolBrush=(255,255,0),
                symbolPen=None,
                symbolSize=3
            )

        pk = self.sp_obj.peak_dat[0]
        if self.plot_fit is None:
            self.plot_fit = self.graf.plot(
                pk.roi_ch,
                pk.curv_fit+pk.bkg,
                pen=(0,0,255)
            )
        else:
            self.plot_fit.setData(
                pk.roi_ch,
                pk.curv_fit+pk.bkg,
                pen=(0,0,255)
            )
        if self.plot_bkg is None:
            self.plot_bkg = self.graf.plot(
                self.sp_obj.channels,
                self.sp_obj.bkg,
                pen=(220,220,220)
            )
        else:
            self.plot_bkg.setData(
                self.sp_obj.channels,
                self.sp_obj.bkg,
                pen=(220,220,220)
            )
        self.plot_data.setLogMode(False, True)
        self.plot_fit.setLogMode(False, True)
        self.plot_bkg.setLogMode(False, True)
        xmin = pk.roi_ch[0]
        xmax = pk.roi_ch[-1]
        pos = round(pk.cen_ch)
        x_0 = (3 * xmin - xmax) / 2
        x_1 = (3 * xmax - xmin) / 2
        y_1 = (np.ceil(np.log10(self.sp_obj.counts[pos])))-0.8
        t = self.sp_obj.counts[int(x_1)]
        if t>0:
            y_0 = (np.log10(t))-0.1
        else:
            y_0 = -0.1
        self.graf.setRange(
            None,
            [x_0, x_1],
            [y_0, y_1],
            padding=0.0
        )
        self.label5.setText(
            '<html><head/><body><p><span style="font-size:12pt;"> '
            f'{pk.cen_ener:.2f} keV</span></p></body></html>'
        )
        self.npa.setValue(pk.npa)
        dt64 = c.start
        # xD = np.datetime64('1970-01-01T00:00:00Z')
        ts = (dt64 - np.datetime64('1970-01-01')) / np.timedelta64(1, 's')
        tstart = datetime.utcfromtimestamp(ts)

        self.date1.setDate(tstart)
        self.date1.setTime(tstart.time())
        self.date3.setDate(tstart)
        self.date3.setTime(tstart.time())
        self.date3.setMaximumDate(tstart)
        self.date3.setMaximumTime(tstart.time())
        self.date2.setDate(tstart)
        prevsec = tstart.time().replace(second=tstart.time().second-1)
        self.date2.setTime(prevsec)
        self.date2.setMaximumDate(tstart)
        self.date2.setMaximumTime(prevsec)
        
    
    def nextId(self):
        # caudal: caudal promedio en L/min
        caudal = (self.iniSpin.value() + self.finSpin.value()) / 2
        
        # t_mues: Tiempo de muestreo
        t_mues =  self.date2.dateTime().secsTo(self.date3.dateTime())
        
        # t_delta: Tiempo entre mitad muestreo y adquisición
        t_delta = self.date2.dateTime().addSecs(int(t_mues/2)).secsTo(
            self.date1.dateTime()
        )
        
        # eFilt : Eficiencia del Filtro
        eFilt = 0.997
        
        # tau : constante tiempo muerto detector en us (microsegundos)
        # t_corr: tiempo vivo corregido
        tau = 17
        t_corr = tau / 10 * self.sp_obj.live - (tau - 10) / 10 * self.sp_obj.real
        
        # eff = eficiencia 511 kev
        eff = 0.0002245/2
        
        if self.radioChi.isChecked():
            # datos de chimenea, area en m² y velocidaden m/s
            area = 0.09
            vel = self.velAne.value()
            self.endAuto.emit(
                self.sp_obj,
                eff,
                [caudal, t_mues, t_delta, t_corr, eFilt, area, vel,
                 self.date2.dateTime(), self.date3.dateTime(),
                 self.date1.dateTime()]
            )
        else:
            self.endAuto.emit(
                self.sp_obj,
                eff,
                [caudal, t_mues, t_delta, t_corr, eFilt, None, None,
                 self.date2.dateTime(), self.date3.dateTime(),
                 self.date1.dateTime()]
            )
        return Cuantif_Wizard.ResultPage
               

class Result_Page(QtWidgets.QWizardPage):
    endResult = QtCore.pyqtSignal(Spec, list)
    
    def __init__(self, parent=None, dark_v=False, sp_name=None):
        QtWidgets.QWizardPage.__init__(self, parent)
        self.nucToCalc = None
        self.sp_obj = None
        self.datos = None
        self.eff = None
        self.sp_name = sp_name
        fs = 10
        self.setTitle(
            '<html><head/><body><p><span style="font-size:16pt; '
            'font-weight:600">Análisis y Cuantificación de Muestras '
            'de Aire</span></p></body></html>'
        )
        self.setSubTitle(
            '<html><head/><body><p><span style="font-size:11pt; '
            'font-weight:600">4. Resultados de Cuantificación'
            '</span></p></body></html>'
        )
        if not dark_v:
            self.setPixmap(
                QtWidgets.QWizard.BannerPixmap, # 2
                QtGui.QPixmap("icons/banner2.png").scaledToHeight(90)
            )
        self.setPixmap(
            QtWidgets.QWizard.WatermarkPixmap, # 0
            QtGui.QPixmap("icons/watermark.png").scaledToWidth(200)
        )
        self.label1 = QtWidgets.QLabel(
            '<html><head/><body><p align="justify"><span style=" font-size:'
            f'{fs}pt;">En la presente página se aprecia los resultados de la '
            'cuantificación del fotopico analizado.</span></p></span>'
            f'</p><p align="justify"><span style=" font-size:{fs}pt;">En la '
            'siguiente tabla se se aprecian dichos resultados, los cuales'
            ' pueden ser seleccionados y copiados.</span></p></span></p>'
        )
        self.label1.setWordWrap(True)
        
        self.spins = [QtWidgets.QDoubleSpinBox() for i in range(5)]
        self.table = MyTable()
        
        lay1 = QtWidgets.QVBoxLayout()
        
        self.setLayout(lay1)
        lay1.addWidget(self.label1)
        lay1.addWidget(self.table)
        # self.table.set_data([['hola', 4], ['lol', 3]])

    def initializePage(self):
        pk = self.sp_obj.peak_dat[0]
        dt = self.datos
        nuc = self.nucToCalc
        key = [*nuc][0]
        yld = nuc[key]['gamma'][0][1]  # yield
        hlt = nuc[key]['hl']['type'] # 0:segs 1:min 2:hrs 3:dias 4:años
        t12 = nuc[key]['hl']['value']
        if hlt == 0:
            t12 = t12
        elif hlt == 1:
            t12 = t12 * 60
        elif hlt == 2:
            t12 = t12 * 3600
        elif hlt == 3:
            t12 = t12 * 3600 * 24
        else:
            t12 = t12 * 365.25 * 24 * 3600
        
        kc = t12 / np.log(2) / self.sp_obj.real * \
            ( 1 - np.exp( -np.log(2) * self.sp_obj.real / t12) )
        # 0.975 es por factor de correccion montecarlo
        act_adq = pk.npa / (self.eff * 0.975 * kc * yld * dt[3]) / dt[4]
        kw = np.exp(-np.log(2) * dt[2] / t12)
        act_mue = act_adq / kw
        # vol: volumen de aire muestreado en m³
        vol = dt[0] * dt[1] / 60000
        # concent = concetración de actividad en filtro a mitad de muestreo
        # se encuentra en Bq/m³
        concent = act_mue / vol
        
        print(concent)
        if dt[5]:
            # emisiopn en kBq
            emis = concent * dt[5] * dt[6] * dt[1] / 1000
            print(emis)
            self.table.set_data([
                ['Archivo', self.sp_name],
                ['Nucleido Analizado', nuc[key]['name']],
                ['Inicio Muestreo Aire', dt[7].toString('dd/mm/yyyy hh:mm:ss ap')],
                ['Fin Muestreo Aire', dt[8].toString('dd/mm/yyyy hh:mm:ss ap')],
                ['Inicio Adquisición', dt[9].toString('dd/mm/yyyy hh:mm:ss ap')],
                ['Caudal Promedio (L/min)', dt[0]],
                ['Duración Muestreo (min)', dt[1]/60],
                ['Concentración Actividad Filtro (Bq/m³)', concent],
                ['Velocidad Aire Chimenea (m/s)', dt[6]],
                ['Volumen Total Emanado (m³)', dt[5] * dt[6] * dt[1]],
                ['Actividad Emanada (kBq)', emis]
            ])
        else:
            # dac : DAC en Bq/m³
            dac = 0.02/(0.000000000093)/2400
            self.table.set_data([
                ['Archivo', self.sp_name],
                ['Nucleido Analizado', nuc[key]['name']],
                ['Inicio Muestreo Aire', dt[7].toString('dd/mm/yyyy hh:mm:ss ap')],
                ['Fin Muestreo Aire', dt[8].toString('dd/mm/yyyy hh:mm:ss ap')],
                ['Inicio Adquisición', dt[9].toString('dd/mm/yyyy hh:mm:ss ap')],
                ['Caudal Promedio (L/min)', dt[0]],
                ['Duración Muestreo (min)', dt[1]/60],
                ['Concentración Actividad (Bq/m³)', concent],
                ['DAC Flúor 18 (Bq/m³)', dac],
                ['Porcentaje de DAC (%)', concent/dac*100],
                ['Fracción de DAC', concent/dac],
            ])


# %%
class MySpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, *args):
       QtWidgets.QDoubleSpinBox.__init__(self, *args)

    def textFromValue(self, value):
       return "%.4E" % value

# %%

class MyTable(pg.TableWidget):
    '''Modificaciones a la widget de pyqtgraph'''
    def __init__(self, *args, **kwds):
        pg.TableWidget.__init__(self, *args, **kwds)
        # self.setFormat('%.2f', 1)
        self.setFormat('%12.2f')
        self.setShowGrid(False)
        

    def set_data(self, data):
        '''Metodo adicional para formatear automaticamente'''
        # self.setStyleSheet("")
        self.setData(data)
        self.setHorizontalHeaderLabels(
            ['Dato',
             'Valor']
        )
        for col_n in range(self.columnCount()):
            for row_n in range(self.rowCount()):
                self.item(row_n, col_n).setTextAlignment(
                    int(QtCore.Qt.AlignCenter | QtCore.Qt.AlignVCenter)
                )
        self.horizontalHeader().setSectionResizeMode(
                        QtGui.QHeaderView.Stretch
                        )

# %%
class DockArea2(DockArea):
    '''
    Change to avoid the collapse of the docks
    '''
    def makeContainer(self, typ):
        # new = super(DockArea, self).makeContainer(typ)
        new = super().makeContainer(typ)
        new.setChildrenCollapsible(False)
        return new

class Dock2(Dock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.nStyle = """
        Dock > QWidget {
            border: 1px solid #000;
            border-radius: 0px;
        }"""
        self.updateStyle()


class NuclidePar(pTypes.GroupParameter):
    '''Modelo para el ParamterTree con la info del Nucleido'''
    def __init__(self, **opts):
        pTypes.GroupParameter.__init__(self, **opts)
        self.nuc = self.addChild(
            {'name': 'Datos del Nucleido', 'type': 'group'}
        )
        self.gam = self.addChild(
            {'name': 'Gammas (Energía: Probabilidad)', 'type': 'group'}
        )
        # self.adq = self.param('Parámetros de Adquisición')
        # self.cal = self.param('Datos de Calibración')
        self.nucchilds = []
        self.gamchilds = []
        nucchilds = [
            {'name': 'Nombre', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Número Atómico (Z)      ', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Número Másico (A)', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Semivida (T)', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'Decaimientos', 'type': 'str', 'value': '', 'readonly': True}
        ]
        for i in nucchilds:
            self.nucchilds.append(self.nuc.addChild(i))
        # self.nuc.removeChild(self.nucchilds[0])

    def addData(self, name, z, a, hl, dec):
        self.nucchilds[0].setValue(name)
        self.nucchilds[1].setValue(z)
        self.nucchilds[2].setValue(a)
        self.nucchilds[3].setValue(hl)
        self.nucchilds[4].setValue(dec)

    def addGammas(self, gammas):
        # gamchilds = list()
        for i in self.gamchilds:
            self.gam.removeChild(i)
        self.gamchilds.clear()
        for i in gammas:
            a = {
                'name': f'{i[0]} keV', 'type': 'str',
                'value': f'{i[1]*100} %', 'readonly': True
            }
            # gamchilds += [a]
            self.gamchilds.append(self.gam.addChild(a))
# %%
if __name__ == '__main__':
    import sys
    print('Hola QT')
    dark_v = True
    app = QtWidgets.QApplication(sys.argv)
    en = [1, 2, 3]
    eff = [0.0001, 120, 0.02]
    file = "config/nuclides.yml"
    effFile = 'cals/airdefault.yml'
    # window = Cuantif_Wizard(None, en, eff, dark_v)
    
    FILENAME = 'f183'
    signif = 50
    c = read_cnf_file('files/'+FILENAME+'.cnf', False)
    fwhmc = c.fwhm/c.en_coef[2] #En canales
    channels = c.channels 
    # c.peaks, c.der_2, c.der_1 = peak_search(c.counts, fwhmc, signif)  # 10 a 12 channel
     
    # window = Cuantif_Wizard(None, c, None, None, None, nucFile=file, dark_v=dark_v)
    window = Cuantif_Wizard(None, c, None, None, file, effFile, dark_v, 'files/'+FILENAME+'.cnf')
    if dark_v:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    else:
        app.setStyleSheet('')
        # p = light.palette.LightPalette()
        # app.setStyleSheet(qdarkstyle.load_stylesheet(qtapi="pyqt5", palette=p))
    window.show()
    sys.exit(app.exec_())
