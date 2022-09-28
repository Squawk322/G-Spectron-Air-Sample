# -*- coding: utf-8 -*-
"""
Created on Thu Dec 23 14:30:10 2021

TITLE: Widgets para su uso en MainWindow

@author: Alejandro Condori aleja
E-mail: alejandrocondori2@gmail.com
"""
# %%
import numpy as np
import pyqtgraph as pg
import pyqtgraph.parametertree.parameterTypes as pTypes

from pandas import to_datetime
from pyqtgraph.Qt import QtCore, QtGui, uic
from pyqtgraph.dockarea import Dock, DockArea
from pyqtgraph.parametertree import ParameterTree
from readfile import Spec
from dialogs import Der_Graph

#%%

class DockArea2(DockArea):
    '''
    Change to avoid the collapse of the docks
    '''

    def makeContainer(self, typ):
        # new = super(DockArea, self).makeContainer(typ)
        new = super().makeContainer(typ)
        new.setChildrenCollapsible(False)
        return new

# %%

class MyTabWidget(QtGui.QWidget):
    def __init__(self):
        QtGui.QWidget.__init__(self)
        self.central_lay = QtGui.QVBoxLayout(self)

        # Partes de la Widget
        bar_wid = QtGui.QWidget()
        bar_wid.setStyleSheet('background-color: black')
        bar_wid.setFixedHeight(25)
        self.area = DockArea2()

        # Partes y armado de la barra
        texts = ['Canal :', '', 'Energía : ', '', 'Cuentas :', '']
        bar_lay = QtGui.QHBoxLayout(bar_wid)
        bar_lay.setContentsMargins(10, 0, 10, 0)
        self.bar = [QtGui.QLabel(f'{texts[i]}') for i in range(6)]
        for i in range(6):
            bar_lay.addWidget(self.bar[i])

        # Partes y armado del area de visualizacion
        self.data = Spec()
        self.dockgraf = Dock("Total", size=(700, 150), hideTitle=True)
        self.dockzoom = Dock("Zoom", size=(500, 120), hideTitle=True)
        self.dockinfo = Dock("Info Total", size=(700, 80), hideTitle=True)
        self.dockrep = Dock("Area de Reportes", size=(500, 300), hideTitle=True)
        self.graf = pg.PlotWidget()
        self.zoom = pg.PlotWidget()
        self.vscroll = QtGui.QScrollBar()
        self.deriv = Der_Graph()
        self.reporbar = QtGui.QLabel('<b>Resultados</b>')
        self.reportab = TableWidget()
        self.file = []
        self.plot_data = None
        self.zoom_data = None
        self.zoom_state = False
        self.log_state = False
        self.vline = pg.InfiniteLine(angle=90, movable=True)
        self.zline = pg.InfiniteLine(angle=90, movable=True)
        self.roi = pg.ROI([100, 100], [100, 1000])
        self.plt_region = [False, -20, 0, 0, 0] # [Log?, x_0, x_1, y_0, y_1]
        self.roi_region = [False, 0, 0, 0, 0]# [Log?, posx, posy, sizex, sizey]
        self.info = ParameterTree()
        self.infotree = InfoPar(name='par'+str(i))
        self.reportab = TableWidget()
        self.reporbar = QtGui.QLabel('<b>Resultados</b>')

        # Armado de la Widget
        self.central_lay.addWidget(bar_wid)
        self.central_lay.addWidget(self.area)
        self.positionate_widgets()

    def positionate_widgets(self):
        for j in range(3):
            self.bar[j*2].setAlignment(
                QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
            )
            # self.bar[j*2].setMinimumHeight(25)
            self.bar[j*2].setStyleSheet(
                'color:cyan; font-weight: bold; background-color: black'
            )
            self.bar[j*2+1].setAlignment(
                QtCore.Qt.AlignLeft | QtCore.Qt.AlignVCenter
            )
            # self.bar[j*2+1].setMinimumHeight(25)
            self.bar[j*2+1].setStyleSheet(
                'color: yellow; font-weight: bold; background-color: black'
            )
        self.area.addDock(self.dockgraf, 'left')
        # self.dockgraf.hideTitleBar()
        # self.dockzoom.hideTitleBar()
        self.area.addDock(self.dockinfo, 'bottom', self.dockgraf)
        # self.dockinfo.hideTitleBar()
        self.area.addDock(self.dockrep, 'right', self.dockinfo)
        # self.dockrep.hideTitleBar()
        self.roi.maxBounds = QtCore.QRectF(-20, -50, 4136, 20000000)
        #(x_0, y_0, ancho, alto)
        self.roi.addScaleHandle([0, 0.5], [1, 0.5])
        self.roi.addScaleHandle([0.5, 1], [0.5, 0])
        self.roi.addScaleHandle([1, 0.5], [0, 0.5])
        self.roi.addScaleHandle([0.5, 0], [0.5, 1])
        self.roi.addScaleHandle([0, 0], [1, 1])
        self.roi.addScaleHandle([0, 1], [1, 0])
        self.roi.addScaleHandle([1, 0], [0, 1])
        self.roi.addScaleHandle([1, 1], [0, 0])
        self.roi.sigRegionChanged.connect(self.upd_zoom)
        self.dockinfo.addWidget(self.info)
        self.info.setParameters(self.infotree, showTop=False)
        self.dockrep.addWidget(self.reportab, row=1, col=0)
        # self.dockrep.addWidget(self.reporbar, row=0, col=0)
        self.dockgraf.addWidget(self.graf, row=0, col=0)
        self.dockzoom.addWidget(self.zoom, col=0)
        self.graf.showAxis('bottom', False)
        self.graf.showAxis('left', False)
        self.graf.setMouseEnabled(x=False, y=False)
        self.graf.hideButtons()
        self.zoom.showAxis('bottom', False)
        self.zoom.showAxis('left', False)
        self.zoom.setMouseEnabled(x=False, y=False)
        self.zoom.hideButtons()
        self.dockgraf.addWidget(self.vscroll, row=0, col=1)
        self.vscroll.valueChanged.connect(self.upd_slide)
        self.graf.setMinimumHeight(100)
        self.graf.scene().sigMouseClicked.connect(self.v_click1)
        self.zoom.scene().sigMouseClicked.connect(self.v_click2)
        self.graf.addItem(self.vline, ignoreBounds=True)
        self.zoom.addItem(self.zline, ignoreBounds=True)
        self.vline.setPos(100)
        self.zline.setPos(100)
        self.vline.sigPositionChanged.connect(self.upd_vline)
        self.zline.sigPositionChanged.connect(self.upd_zline)

    def v_click1(self, ev_cl):
        '''Accion desencadenada al hacer click en el grafico superior, que reposiciona
        la linea vertical (marcador) a la posicion del click'''
        if ev_cl.button() == QtCore.Qt.LeftButton:
            try:
                a_pos = self.graf.plotItem.vb.mapDeviceToView(
                    QtCore.QPointF(ev_cl.pos())
                )
            except:
                pass
            else:
                ch0 = round(a_pos.x())
                self.real_upd_lines(ch0)

    def v_click2(self, ev_cl):
        '''Accion desencadenada al hacer click en el grafico inferior, que reposiciona
        la linea vertical (marcador) a la posicion del click'''
        if ev_cl.button() == QtCore.Qt.LeftButton:
            try:
                a_pos = self.zoom.plotItem.vb.mapDeviceToView(
                    QtCore.QPointF(ev_cl.pos())
                )
            except:
                pass
            else:
                ch_sel = round(a_pos.x())
                self.real_upd_lines(ch_sel)    

    @QtCore.pyqtSlot()
    def upd_vline(self):
        '''Limita el movimiento de las lineas verticales de la grafica superior
        a modo discreto, es decir de canal en canal.
        Llama a una función de actualizacion'''
        ch0 = round(self.vline.value())
        self.real_upd_lines(ch0)

    @QtCore.pyqtSlot()
    def upd_zline(self):
        '''Limita el movimiento de las lineas verticales de la grafica inferior
        a modo discreto, es decir de canal en canal.
        Llama a una función de actualizacion'''
        ch0 = round(self.zline.value())
        self.real_upd_lines(ch0)

    def real_upd_lines(self, pos):
        '''Funcion que actualiza la info del marcador (linea vertical)'''
        if pos < 1:
            pos = 1
        if pos > 4096:
            pos = 4096
        self.vline.setPos(pos)
        self.zline.setPos(pos)
        self.bar[1].setText(str(pos))
        self.bar[3].setText(
            str(round(self.data.energy[pos-1], 2)) + ' ' + self.data.unit
        )
        self.bar[5].setText(str(int(self.data.counts[pos-1])))

    def upd_zoom_state(self, state):
        self.zoom_state = state
        self.zoom_trigg()

    @QtCore.pyqtSlot()
    def zoom_trigg(self):
        '''Accion al seleccionar/desselecionar el boton de zoom. Añade/elimina
        una ROI rectangular y un Dock con la grafica ampliada en la ROI'''
        if self.zoom_state:
            if self.plot_data is not None:
                self.area.addDock(self.dockzoom, 'bottom', self.dockgraf)
                self.graf.addItem(self.roi)
                self.set_roi()
        else:
            if self.plot_data is not None:
                roi_state = self.roi.getState()
                x_0, y_0 = roi_state['pos']
                roi_width, roi_height = roi_state['size']
                self.roi_region[1:] = [x_0, y_0, roi_width, roi_height]
                self.dockzoom.close()
                self.graf.removeItem(self.roi)

    def upd_log_state(self, state):
        self.log_state = state
        self.log_trigg()

    @QtCore.pyqtSlot()
    def log_trigg(self):
        '''Accion al seleccionar/desseleccionar el boton de escala Logaritmica:
        Convierte a escala logaritmica/linea el eje Y de todas las pestañas y
        ajusta el tamaño de la ROI y de sus límites de movimiento. Del mismo
        modo modifica los parámetros de la barra de "desplazamiento" 
        vertical'''
        if self.plot_data is not None:
            if self.log_state and not self.roi_region[0]:
                if self.zoom_state:
                    roi_state = self.roi.getState()
                    x_0, y_0 = roi_state['pos']
                    roi_width, roi_height = roi_state['size']
                    self.roi_region[1:] = [x_0, y_0, roi_width, roi_height]
                self.plot_data.setLogMode(False, True)
                self.zoom_data.setLogMode(False, True)
                yn0 = self.roi_region[2] / (
                    self.plt_region[4] - self.plt_region[3]
                )
                yn1 = (self.roi_region[2] + self.roi_region[4]) / (
                    self.plt_region[4] - self.plt_region[3]
                )
                self.plt_region[0] = True
                ymax = np.ceil(np.log10(self.data.maxc))
                self.plt_region[3:] = [-0.15, ymax]
                self.upd_plt_zone()
                yn0 *= self.plt_region[4] - self.plt_region[3]
                yn1 *= self.plt_region[4] - self.plt_region[3]
                self.roi_region[0] = True
                self.roi_region[2] = yn0
                self.roi_region[4] = yn1-yn0
                if self.zoom_state:
                    self.set_roi()
                self.vscroll.setMaximum(9)
                self.vscroll.setValue(self.vscroll.maximum() + 1 - int(ymax))
            else:
                if self.roi_region[0]:
                    if self.zoom_state:
                        roi_state = self.roi.getState()
                        x_0, y_0 = roi_state['pos']
                        roi_width, roi_height = roi_state['size']
                        self.roi_region[1:] = [x_0, y_0, roi_width, roi_height]
                    self.plot_data.setLogMode(False, False)
                    self.zoom_data.setLogMode(False, False)
                    yn0 = self.roi_region[2]/(
                        self.plt_region[4] - 
                        self.plt_region[3]
                    )
                    yn1 = (self.roi_region[2] + self.roi_region[4])/\
                        (self.plt_region[4] - self.plt_region[3])
                    self.plt_region[0] = False
                    ymax = 2**(np.ceil(np.log2(self.data.maxc)))
                    if ymax < 16:
                        ymax = 16
                    self.plt_region[3:] = [-0.001*ymax, ymax]
                    self.upd_plt_zone()
                    yn0 *= (self.plt_region[4] - self.plt_region[3])
                    yn1 *= (self.plt_region[4] - self.plt_region[3])
                    self.roi_region[0] = False
                    self.roi_region[2] = yn0
                    self.roi_region[4] = yn1-yn0
                    if self.zoom_state:
                        self.set_roi()
                    self.vscroll.setMaximum(28)
                    self.vscroll.setValue(
                        self.vscroll.maximum() -
                        int(np.log2(ymax/16))
                    )

    @QtCore.pyqtSlot()
    def upd_zoom(self):
        '''Actualiza la region del grafico del zoom cuando la ROI es \
            modificada'''
        roi_state = self.roi.getState()
        x_0, y_0 = roi_state['pos']
        roi_width, roi_height = roi_state['size']
        x_1 = x_0 + roi_width
        y_1 = y_0 + roi_height
        self.zoom.setYRange(y_0, y_1, padding=0)
        self.zoom.setXRange(x_0, x_1, padding=0)

    @QtCore.pyqtSlot()
    def upd_slide(self):
        '''Ajusta el rango vertical del grafico de acuerdo a la posicion de la
        barra de desplazamiento vertical'''
        svalue = self.vscroll.maximum()-self.vscroll.value()
        if self.plt_region[0]:    # True es logaritmico
            if self.zoom_state:
                roi_state = self.roi.getState()
                x_0, y_0 = roi_state['pos']
                roi_width, roi_height = roi_state['size']
            else:
                x_0, y_0, roi_width, roi_height = self.roi_region[1:]
            ymax = 1+svalue
            yn0 = y_0/(self.plt_region[4]-self.plt_region[3])
            yn1 = (y_0+roi_height)/(self.plt_region[4]-self.plt_region[3])
            self.plt_region[4] = ymax
            self.upd_plt_zone()
            yn0 *= (self.plt_region[4]-self.plt_region[3])
            yn1 *= (self.plt_region[4]-self.plt_region[3])
            if self.zoom_state:
                self.roi.setPos((x_0, yn0))
                self.roi.setSize((roi_width, yn1-yn0))
                x_0, x_1, y_0, y_1 = self.plt_region[1:5]
                self.roi.maxBounds = QtCore.QRectF(x_0, y_0, x_1-x_0, y_1-y_0)
                self.upd_zoom()
            else:
                self.roi_region[2] = yn0
                self.roi_region[4] = yn1-yn0
        else:
            if self.zoom_state:
                roi_state = self.roi.getState()
                x_0, y_0 = roi_state['pos']
                roi_width, roi_height = roi_state['size']
            else:
                x_0, y_0, roi_width, roi_height = self.roi_region[1:]
            ymax = 16*2**(svalue)
            yn0 = y_0/(self.plt_region[4]-self.plt_region[3])
            yn1 = (y_0+roi_height)/(self.plt_region[4]-self.plt_region[3])
            self.plt_region[4] = ymax
            self.plt_region[3] = -0.005*ymax
            self.upd_plt_zone()
            yn0 *= (self.plt_region[4]-self.plt_region[3])
            yn1 *= (self.plt_region[4]-self.plt_region[3])
            if self.zoom_state:
                self.roi.setPos((x_0, yn0))
                self.roi.setSize((roi_width, yn1-yn0))
                x_0, x_1, y_0, y_1 = self.plt_region[1:5]
                self.roi.maxBounds = QtCore.QRectF(x_0, y_0, x_1-x_0, y_1-y_0)
                self.upd_zoom()
            else:
                self.roi_region[2] = yn0
                self.roi_region[4] = yn1-yn0

    def upd_plt_zone(self):
        '''Ajusta la region del grafico'''
        self.graf.setRange(
            None,
            self.plt_region[1:3],
            self.plt_region[3:],
            padding=0.0
        )

    def set_spec(self, sp_obj, replace=False):
        '''Almacena la información del archivo como un atributo de la ventana 
        principal. Grafica y acomoda la informacion en la interfaz'''
        self.data = sp_obj
        if self.plot_data is None:
            self.plot_data = self.graf.plot(
                self.data.channels,
                self.data.counts
            )
            self.zoom_data = self.zoom.plot(
                self.data.channels,
                self.data.counts
            )
        else:
            self.plot_data.setData(
                self.data.channels,
                self.data.counts
            )
            self.zoom_data.setData(
                self.data.channels,
                self.data.counts
            )
        self.plot_data.setLogMode(False, False)
        self.zoom_data.setLogMode(False, False)
        x_0 = -20
        x_1 = self.data.n_ch+20
        y_1 = 2**(np.ceil(np.log2(self.data.maxc)))
        y_0 = -0.005*y_1
        if y_1 < 16:
            y_1 = 16
        self.plt_region = [False, x_0, x_1, y_0, y_1]
        self.roi_region = [False, 0.02*x_1, 0.1*y_1, 0.1*x_1, 0.3*y_1]
        self.graf.setRange(
            None,
            self.plt_region[1:3],
            self.plt_region[3:],
            padding=0.0
        )
        self.vscroll.setMaximum(28)
        self.vscroll.setValue(
            self.vscroll.maximum()-int(np.log2(y_1/16))
        )
        if self.log_state:
            self.plot_data.setLogMode(False, True)
            self.zoom_data.setLogMode(False, True)
            y_0 = -0.15
            y_1 = (np.ceil(np.log10(self.data.maxc)))
            self.plt_region = [True, x_0, x_1, y_0, y_1]
            self.roi_region = [True, 0.02*x_1, 0.1*y_1, 0.1*x_1, 0.3*y_1]
            self.vscroll.setMaximum(9)
            self.vscroll.setValue(self.vscroll.maximum()+1-int(y_1))
        if self.zoom_state:
            if not replace:
                self.area.addDock(self.dockzoom, 'bottom', self.dockgraf)
                self.graf.addItem(self.roi)
            self.set_roi()
        x_0, x_1, y_0, y_1 = self.plt_region[1:]
        self.roi.maxBounds = QtCore.QRectF(x_0, y_0, x_1-x_0, y_1-y_0)
        self.upd_plt_zone()
        self.upd_info(sp_obj)

    def set_roi(self):
        '''Posiciona la ROI en el grafico'''
        x_0, y_0, roi_width, roi_height = self.roi_region[1:5]
        self.roi.setPos((x_0, y_0))
        self.roi.setSize((roi_width, roi_height))
        x_0, x_1, y_0, y_1 = self.plt_region[1:5]
        self.roi.maxBounds = QtCore.QRectF(x_0, y_0, x_1-x_0, y_1-y_0)
        self.upd_zoom()

    def upd_info(self, sp_obj):
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
                self.infotree.adqchilds[ind].setValue(new)
            elif ind < 12:
                self.infotree.encalchilds[ind-8].setValue('{:.3E}'.format(new))
            elif ind < 14:
                self.infotree.fwcalchilds[ind-12].setValue('{:.3E}'.format(new))
            else:
                self.infotree.effcalchilds[ind-14].setValue('{:.3E}'.format(new))

#%% Parameter Tree Model

class InfoPar(pTypes.GroupParameter):
    '''Modelo para el ParamterTree con la info del Espectro'''
    def __init__(self, **opts):
        pTypes.GroupParameter.__init__(self, **opts)
        self.adq = self.addChild({'name': 'Parámetros de Adquisición', 'type': 'group'})
        self.cal = self.addChild({'name': 'Datos de Calibración', 'type': 'group'})
        # self.adq = self.param('Parámetros de Adquisición')
        # self.cal = self.param('Datos de Calibración')
        self.adqchilds = []
        self.encalchilds = []
        self.fwcalchilds = []
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
            # self.adq.addChild(i)
            self.adqchilds.append(self.adq.addChild(i))
        # self.adqchilds = [self.param('Parámetros de Adquisición', it['name']) for it in adqchilds]
        encalpar = self.cal.addChild({'name': 'Energía (A1*Ch³ + A2*Ch² + A3*Ch + A4)', 'type': 'group'})
        encal = [
            {'name': 'A1', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'A2', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'A3', 'type': 'str', 'value': '', 'readonly': True},
            {'name': 'A4', 'type': 'str', 'value': '', 'readonly': True}
        ]
        for i in encal:
            self.encalchilds.append(encalpar.addChild(i))
        
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

# %% Table Widget para resultados

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

# %% Label con animación de movimiento
class AniLabel(QtGui.QLabel):

    x = 0
    paused = False
    document = None

    def __init__(self, speed=50, width=450):
        QtGui.QLabel.__init__(self)
        self.fm = QtGui.QFontMetrics(self.font())
        self.setFixedSize(width, 25)
        self.speed = speed
        self.ended = False
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.translate)

    def setText(self, value):
        self.x = 0
        self.document = QtGui.QTextDocument(self)
        self.document.setPlainText(value)
        # I multiplied by 1.06 because otherwise the text goes on 2 lines
        self.document.setTextWidth(self.fm.width(value) * 1.06)
        self.document.setUseDesignMetrics(True)
        self.repaint()

    @QtCore.pyqtSlot()
    def translate(self):
        if not self.paused and not self.ended:
            if self.width() - self.x < self.document.textWidth() \
                and not self.ended:
                self.x -= 1
            else:
                self.ended = True
        else:
            self.ended = False
        self.repaint()

    def event(self, event):
        if event.type() == QtCore.QEvent.Enter:
            self.paused = False
            self.timer.start(int((1 / self.speed) * 1000))
        elif event.type() == QtCore.QEvent.Leave:
            self.paused = True
            self.ended = False
            self.x = 0
            self.timer.stop()
            self.repaint()
        return super().event(event)

    def paintEvent(self, event):
        if self.document:
            p = QtGui.QPainter(self)
            p.translate(self.x, 0)
            self.document.drawContents(p)
        return super().paintEvent(event)


# %%
if __name__ == "__main__":
    import sys
    print('Hola QT')
    app = QtGui.QApplication(sys.argv)
    window = MyTabWidget()
    window.show()
    sys.exit(app.exec_())
