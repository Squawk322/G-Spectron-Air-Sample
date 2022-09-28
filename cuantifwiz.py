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
from pyqtgraph.Qt import QtGui, QtWidgets, QtCore
from pyqtgraph.parametertree import ParameterTree
from pyqtgraph.dockarea import Dock, DockArea


# %%

class Cuantif_Wizard(QtWidgets.QWizard):
    NUM_PAGES = 5
    (StartPage, NuclidePage, ManualPage, AutoPage,
        ResultPage) = range(NUM_PAGES)
    
    def __init__(self, parent=None, en=None, eff=None, dark_v=False, file=None):
        QtWidgets.QWizard.__init__(self, parent)
        self.setPage(self.StartPage, Start_Page(self, dark_v, en, eff))
        self.setPage(self.NuclidePage, Nuclide_Page(self, dark_v, en, eff, file))
        self.setPage(self.ManualPage, Manual_Page(self))
        self.setPage(self.AutoPage, Auto_Page(self))
        self.setPage(self.ResultPage, Result_Page(self))
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

        

class Start_Page(QtWidgets.QWizardPage):
    
    def __init__(self, parent=None, dark_v=False, en=None, eff=None):
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
                QtGui.QPixmap("icons/banner2.png").scaledToHeight(80)
            )
        self.setPixmap(
            QtWidgets.QWizard.WatermarkPixmap, # 0
            QtGui.QPixmap("icons/watermark.png").scaledToWidth(200)
        )
        fs = 10 # Font Size
        self.en = en
        self.eff = eff
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
                QtGui.QPixmap("icons/banner2.png").scaledToHeight(80)
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
        # print(info)
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
        

class Manual_Page(QtWidgets.QWizardPage):
    pass

class Auto_Page(QtWidgets.QWizardPage):
    pass

class Result_Page(QtWidgets.QWizardPage):
    pass

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
            {'name': 'Gammas (Energía: Probabilidad', 'type': 'group'}
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
    dark_v = False
    app = QtWidgets.QApplication(sys.argv)
    en = [1, 2, 3]
    eff = [0.0001, 120, 0.02]
    file = "config/nuclides.yml"
    # window = Cuantif_Wizard(None, en, eff, dark_v)
    window = Cuantif_Wizard(None, None, None, dark_v, file)
    if dark_v:
        app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    else:
        app.setStyleSheet('')
        # p = light.palette.LightPalette()
        # app.setStyleSheet(qdarkstyle.load_stylesheet(qtapi="pyqt5", palette=p))
    window.show()
    sys.exit(app.exec_())
