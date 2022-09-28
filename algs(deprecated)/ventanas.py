# -*- coding: utf-8 -*-
"""
Created on Wed Oct 21 13:07:15 2020

@author: Alejandro Condori

"""
#%%
import sys, re
import io
import csv
from PyQt5 import QtCore, QtGui, uic, QtWidgets
from pyqtgraph.dockarea import Dock, DockArea
import pyqtgraph as pg
from peaksearch import peak_search
import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas


#%% CARGAR ARCHIVOS DEL QTDESIGNER
UI_DERIVATIVE = uic.loadUiType("UI_FILES/der.ui")[0]
UI_PEAKSEARCH = uic.loadUiType("UI_FILES/psearch.ui")[0]
UI_ENERCAL = uic.loadUiType("UI_FILES/enercal.ui")[0]
UI_FWENCALSHOW = uic.loadUiType("UI_FILES/fwencalshow.ui")[0]
UI_ENFWCAL = uic.loadUiType("UI_FILES/enfwcal.ui")[0]
UI_EFFCAL = uic.loadUiType("UI_FILES/effcal.ui")[0]
UI_EFFCALSHOW = uic.loadUiType("UI_FILES/effcalshow.ui")[0]
# %%  VENTANA DE GRAFICOS
# class DockArea(DockArea):
#     def makeContainer(self, typ):
#         new = super(DockArea, self).makeContainer(typ)
#         new.setChildrenCollapsible(False)
#         return new

class Der_Graph(QtGui.QMainWindow, UI_DERIVATIVE):
    '''Ventna donde se visualizan los gráficos de las derivadas'''
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        UI_DERIVATIVE.__init__(self)
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

# %% VENTANA DE BUSQUEDA DE PICOS
class Pk_Search(QtGui.QDialog, UI_PEAKSEARCH):
    '''Ventana para ejecutar la rutina de Busqueda de Picos'''
    def __init__(self, parent, spec = None):
        QtGui.QDialog.__init__(self, parent)
        UI_PEAKSEARCH.__init__(self)
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

#%% VENTANA DE CALIBRACION
class QTableView2(QtGui.QTableView):
    def __init__(self, *args, **kwds):
        QtGui.QTableView.__init__(self, *args, **kwds)
        self.setItemDelegate(my_delegate())
        self.setStyleSheet(
            "QHeaderView::section { background-color:cyan; color:black}\
            QTableCornerButton::section {  background-color:cyan; color:black; border: 1px outset gray;}"
        )

class my_delegate(QtGui.QItemDelegate):

    # def createEditor(self, parent, option, index):
    #     return super(my_delegate, self).createEditor(parent, option, index)

    def setEditorData(self, editor, index):
        text = index.data(QtCore.Qt.EditRole) or index.data(QtCore.Qt.DisplayRole)
        editor.setText(text)

class CalTableModel(QtCore.QAbstractTableModel):
    '''Modelo de Tabla para la ventana de calibracion de energia'''
    def __init__(self, data, fw=False):
        QtCore.QAbstractTableModel.__init__(self)
        self.fw = fw
        self.load_data(data) 

    def load_data(self, data):
        if data.any():
            # data = np.sort(data)
            self.input_channel = data[0]
            self.input_energy = data[1]
            _,ind = np.unique(self.input_channel, return_index=True)
            self.input_channel = self.input_channel[ind]
            self.input_energy = self.input_energy[ind]
            if self.fw:
                self.input_fwhm = data[2][ind]
            self.row_count = len(self.input_energy)
        else:
            self.row_count = 0
            self.input_channel = np.empty(0)
            self.input_energy = np.empty(0)
            if self.fw:
                self.input_fwhm = np.empty(0)
        if self.fw:
            self.column_count = 3
        else:
            self.column_count = 2

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            if self.fw:
                return ("Canal", "Energía\n(keV)", "FWHM\n(keV)")[section]
            else:
                return ("Canal", "Energía\n(keV)")[section]
        else:
            return "{}".format(section+1)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return "{:10.3f}".format(self.input_channel[row])
            elif column == 1:
                return "{:10.3f}".format(self.input_energy[row])
            elif column == 2:
                # if self.fw:
                return "{:10.3f}".format(self.input_fwhm[row])
        elif role == QtCore.Qt.BackgroundRole:
            return QtGui.QColor(QtCore.Qt.white)
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)
        return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        return QtCore.QAbstractItemModel.flags(self, index) | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role):
        if index.isValid() and role == QtCore.Qt.EditRole:
            column = index.column()
            row = index.row()
            try:
                value = float(value)
            except ValueError:
                return False
            if column == 0:
                self.input_channel[row] = value
            elif column == 1:
                self.input_energy[row] = value
            elif column ==2:
                self.input_fwhm[row] = value
            self.dataChanged.emit(index, index)
            _,ind = np.unique(self.input_channel, return_index=True)
            self.input_channel = self.input_channel[ind]
            self.input_energy = self.input_energy[ind]
            self.column_count = 2
            if self.fw:
                self.input_fwhm = self.input_fwhm[ind]
                self.column_count = 3
            self.row_count = len(self.input_energy)
            self.layoutChanged.emit()
            return True
        return False

class Ener_Cal(QtGui.QDialog, UI_ENERCAL):
    '''Ventana para introducir los valores de calibracion energetica'''
    def __init__(self, parent=None, data=np.empty(0), imp=False):
        QtGui.QDialog.__init__(self, parent)
        UI_ENERCAL.__init__(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setupUi(self)
        self.tablev = QTableView2()
        self.boxview.addWidget(self.tablev)
        self.can = False
        self.cancel.clicked.connect(self.close)
        self.aceptar.clicked.connect(self.accept_clicked)
        self.canal.setButtonSymbols(2)
        self.energia.setButtonSymbols(2)
        self.horizontal_header = self.tablev.horizontalHeader()
        self.vertical_header = self.tablev.verticalHeader()
        self.horizontal_header.setSectionResizeMode(
                                # QtGui.QHeaderView.ResizeToContents
                                QtGui.QHeaderView.Stretch
                                )
        self.vertical_header.setSectionResizeMode(
                              QtGui.QHeaderView.ResizeToContents
                              )
        self.model = CalTableModel(np.empty(0))
        self.data = data
        self.tablev.setModel(self.model)
        self.autom.setEnabled(imp)
        self.importar.clicked.connect(self.import_data)
        self.add.clicked.connect(self.add_data)
        self.model.layoutChanged.connect(self.tablev.resizeRowsToContents)
        self.borrar.clicked.connect(self.del_data)
        self.selec = self.tablev.selectionModel()
        self.selec.selectionChanged.connect(self.toggle_button)
        self.toggle_button()
        self.aceptar.setEnabled(False)
        self.tablev.installEventFilter(self)
        self.adjustSize()
        geo = self.frameGeometry()
        self.setMaximumWidth(geo.width())

    def accept_clicked(self):
        self.can = True
        self.close()

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.matches(QtGui.QKeySequence.Copy)):
            self.copySelection()
            return True
        return False

    def copySelection(self):
        selection = self.tablev.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                # table[row][column] = index.data()
                if column == 0:
                    table[row][column] = self.model.input_channel[row]
                elif column == 1:
                    table[row][column] = self.model.input_energy[row]
            stream = io.StringIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            QtWidgets.qApp.clipboard().setText(stream.getvalue())
        return

    def import_data(self):
        self.model.load_data(self.data)
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.model.layoutChanged.emit()

    def add_data(self):
        add_ch = self.canal.value()
        add_en = self.energia.value()
        if self.model.row_count == 0:
            self.model.input_channel = np.append(self.model.input_channel, add_ch)
            self.model.input_energy = np.append(self.model.input_energy, add_en)
        else:
            self.model.input_channel = np.insert(self.model.input_channel, 0, add_ch)
            self.model.input_energy = np.insert(self.model.input_energy, 0, add_en)
        _, ind = np.unique(self.model.input_channel, return_index=True)
        self.model.input_channel = self.model.input_channel[ind]
        self.model.input_energy = self.model.input_energy[ind]
        self.model.row_count = len(self.model.input_energy)
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.model.layoutChanged.emit()

    def del_data(self):
        del_row = []
        for i in self.selec.selectedIndexes():
            # if i is not []:
            del_row += [i.row()]
        self.model.input_channel = np.delete(self.model.input_channel, del_row)
        self.model.input_energy = np.delete(self.model.input_energy, del_row)
        _,ind = np.unique(self.model.input_channel, return_index=True)
        self.model.input_channel = self.model.input_channel[ind]
        self.model.input_energy = self.model.input_energy[ind]
        self.model.row_count = len(self.model.input_channel)
        self.tablev.clearSelection()
        self.model.layoutChanged.emit()
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.toggle_button()

    def toggle_button(self):
        self.borrar.setEnabled(self.selec.hasSelection())
        if self.model.row_count == 0:
            self.borrar.setEnabled(False)

#%%
class EnFw_Cal(QtGui.QDialog, UI_ENFWCAL):
    '''Ventana para introducir los valores de calibracion energetica'''
    def __init__(self, parent=None, data=np.empty(0), imp=False):
        QtGui.QDialog.__init__(self, parent)
        UI_ENFWCAL.__init__(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setupUi(self)
        self.tablev = QTableView2()
        self.boxview.addWidget(self.tablev)
        self.can = False
        self.cancel.clicked.connect(self.close)
        self.aceptar.clicked.connect(self.accept_clicked)
        self.canal.setButtonSymbols(2)
        self.energia.setButtonSymbols(2)
        self.fwhm.setButtonSymbols(2)
        self.horizontal_header = self.tablev.horizontalHeader()
        self.vertical_header = self.tablev.verticalHeader()
        self.horizontal_header.setSectionResizeMode(
                                # QtGui.QHeaderView.ResizeToContents
                                QtGui.QHeaderView.Stretch
                                )
        self.vertical_header.setSectionResizeMode(
                              QtGui.QHeaderView.ResizeToContents
                              )
        self.model = CalTableModel(np.empty(0), fw=True)
        self.data = data
        self.tablev.setModel(self.model)
        self.autom.setEnabled(imp)
        self.importar.clicked.connect(self.import_data)
        self.add.clicked.connect(self.add_data)
        self.model.layoutChanged.connect(self.tablev.resizeRowsToContents)
        self.borrar.clicked.connect(self.del_data)
        self.selec = self.tablev.selectionModel()
        self.selec.selectionChanged.connect(self.toggle_button)
        self.toggle_button()
        self.aceptar.setEnabled(False)
        self.tablev.installEventFilter(self)
        self.adjustSize()
        geo = self.frameGeometry()
        self.setMaximumWidth(geo.width())

    def accept_clicked(self):
        self.can = True
        self.close()

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.matches(QtGui.QKeySequence.Copy)):
            self.copySelection()
            return True
        return False

    def copySelection(self):
        selection = self.tablev.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                # table[row][column] = index.data()
                if column == 0:
                    table[row][column] = self.model.input_channel[row]
                elif column == 1:
                    table[row][column] = self.model.input_energy[row]
                elif column == 2:
                    table[row][column] = self.model.input_fwhm[row]
            stream = io.StringIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            QtWidgets.qApp.clipboard().setText(stream.getvalue())
        return

    def import_data(self):
        self.model.load_data(self.data)
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.model.layoutChanged.emit()

    def add_data(self):
        add_ch = self.canal.value()
        add_en = self.energia.value()
        add_fw = self.fwhm.value()
        if self.model.row_count == 0:
            self.model.input_channel = np.append(self.model.input_channel, add_ch)
            self.model.input_energy = np.append(self.model.input_energy, add_en)
            self.model.input_fwhm = np.append(self.model.input_fwhm, add_fw)
        else:
            self.model.input_channel = np.insert(self.model.input_channel, 0, add_ch)
            self.model.input_energy = np.insert(self.model.input_energy, 0, add_en)
            self.model.input_fwhm = np.insert(self.model.input_fwhm, 0, add_fw)
        _,ind = np.unique(self.model.input_channel, return_index=True)
        self.model.input_channel = self.model.input_channel[ind]
        self.model.input_energy = self.model.input_energy[ind]
        self.model.input_fwhm = self.model.input_fwhm[ind]
        self.model.row_count = len(self.model.input_channel)
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.model.layoutChanged.emit()

    def del_data(self):
        del_row = []
        for i in self.selec.selectedIndexes():
            # if i is not []:
            del_row += [i.row()]
        self.model.input_channel = np.delete(self.model.input_channel, del_row)
        self.model.input_energy = np.delete(self.model.input_energy, del_row)
        self.model.input_fwhm = np.delete(self.model.input_fwhm, del_row)
        _,ind = np.unique(self.model.input_channel, return_index=True)
        self.model.input_channel = self.model.input_channel[ind]
        self.model.input_energy = self.model.input_energy[ind]
        self.model.input_fwhm = self.model.input_fwhm[ind]
        self.model.row_count = len(self.model.input_channel)
        self.tablev.clearSelection()
        self.model.layoutChanged.emit()
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.toggle_button()

    def toggle_button(self):
        self.borrar.setEnabled(self.selec.hasSelection())
        if self.model.row_count == 0:
            self.borrar.setEnabled(False)

#%% VENTANA PARA MOSTRAR LA CALIBRACION DE ENERGIA Y FWHM
def ener_cal(ch, en, orden, channels):
    fit = np.polyfit(ch, en, orden)
    fit = np.append(np.zeros(4-len(fit)), fit)
    return fit, np.polyval(fit, channels)

def fwhm_cal(en, fw, energy):
    en[en<0] = 0
    fit = np.polyfit(np.sqrt(en), fw, 1)
    energy[energy<0] = 0
    return fit, np.polyval(fit, np.sqrt(energy))

def solve_for_y(poly_coeffs, y):
    pc = poly_coeffs.copy()
    pc[-1] -= y
    return np.roots(pc)

class MathTextLabel(QtGui.QWidget):
    def __init__(self, parent=None, mathText='', **kwargs):
        QtGui.QWidget.__init__(self, parent, **kwargs)

        l=QtGui.QVBoxLayout(self)
        l.setContentsMargins(0,0,0,0)

        r,g,b,a=self.palette().base().color().getRgbF()

        self._figure=Figure(edgecolor=(r,g,b), facecolor=(r,g,b))
        self._canvas=FigureCanvas(self._figure)
        l.addWidget(self._canvas)
        self.set_equation(mathText)

    def set_equation(self, mathText):
        self._figure.clear()
        text=self._figure.suptitle(
            mathText,
            x=0.0,
            y=1.0,
            horizontalalignment='left',
            verticalalignment='top',
            size = QtWidgets.qApp.font().pointSize()*2)
        self._canvas.draw()
        (x0,y0),(x1,y1)=text.get_window_extent().get_points()
        w=x1-x0; h=y1-y0
        self._figure.set_size_inches(w/80, h/80)
        self.setFixedSize(w,h)
        
#Uso en codigo:
# self.enlabel = MathTextLabel(self, r'Energia = ')
# self.equlay.addWidget(self.enlabel, alignment=QtCore.Qt.AlignHCenter)


class EnFw_CalShow(QtGui.QDialog, UI_FWENCALSHOW):
    '''Venatana que muestra los valores de calibración de energia y fwhm'''
    def __init__(self,
                 parent=None,
                 cal_data=np.empty(0),
                 spec_info=None,
                 from_diag='eneronly',
                 fname=''
        ):
        QtGui.QDialog.__init__(self, parent)
        UI_FWENCALSHOW.__init__(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setupUi(self)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        self.from_diag = from_diag
        self.graf = [pg.PlotWidget() for _ in range(2)]
        self.pld = [None for _ in range(4)]  #plotdata
        self.layener.addWidget(self.graf[0])
        self.layfwhm.addWidget(self.graf[1])
        for i in range(2):
            self.graf[i].setBackground('w')
            self.graf[i].setMouseEnabled(x=False, y=False)
            self.graf[i].hideButtons()
            self.graf[i].showGrid(x=True, y=True)
        self.graf[0].setLabel('bottom', 'Canal', color='black')
        self.graf[0].setLabel('left', 'Energia', 'eV', color='black')
        self.graf[0].setTitle('Energía vs Canales')
        self.graf[0].addLegend()
        self.graf[1].setLabel('bottom', 'Energia', 'eV', color='black')
        self.graf[1].setLabel('left', 'FWHM', 'eV', color='black')
        self.graf[1].setTitle('FWHM vs Energía')
        self.graf[1].addLegend()
        self.can = False
        self.cancel.clicked.connect(self.close)
        self.cal_data = cal_data
        self.chs = spec_info.channels
        self.en_coef = spec_info.en_coef
        self.fw_coef = spec_info.fw_coef
        self.new_en_data = self.cal_data[1]
        self.new_fw_data = self.cal_data[2]
        self.file.setText('<b>{:s}</b>'.format(fname))
        ord_in = len(np.roots(self.en_coef))
        self.orden.setValue(ord_in)
        self.orden2.setValue(ord_in)
        self.re_calc()
        self.orden.valueChanged.connect(self.orden_changed)
        self.orden2.valueChanged.connect(self.orden2_changed)
        self.aceptar.clicked.connect(self.acept_clicked)
        if len(self.cal_data[0]) < 4:
            self.orden.setMaximum(2)
            self.orden2.setMaximum(2)

    def orden_changed(self):
        orden = self.orden.value()
        self.orden2.setValue(orden)
        self.re_calc()
        self.orden.lineEdit().deselect()

    def orden2_changed(self):
        orden = self.orden2.value()
        self.orden.setValue(orden)

        self.re_calc()
        self.orden2.lineEdit().deselect()
        self.orden.lineEdit().deselect()

    def re_calc(self):
        orden = self.orden.value()
        if self.from_diag == 'eneronly':
            temp_fw = self.fw_coef[1]+self.fw_coef[0]*np.sqrt(self.new_en_data)
            fw_ch = temp_fw/self.en_coef[-2]
            # a = self.cal_data[1]-temp_fw/2
            # b = self.cal_data[1]+temp_fw/2
        elif self.from_diag == 'enerfwhm':
            fw_ch = self.new_fw_data/self.en_coef[-2]
            # a = self.cal_data[1]-self.new_fw_data/2
            # b = self.cal_data[1]+self.new_fw_data/2
        # leng = len(self.cal_data[1])
        # a_c = np.zeros(leng)
        # b_c = np.zeros(leng)
        # for i in range(leng):
            # roots = solve_for_y(self.en_coef, a[i])
            # var = roots[np.isreal(roots)].real
            # a_c[i] = var[(var >= 0) & (var <= 4096)]
            # roots = solve_for_y(self.en_coef, b[i])
            # var = roots[np.isreal(roots)].real
            # b_c[i] = var[(var >= 0) & (var <= 4096)]
        self.en_coef,self.energy = ener_cal(self.cal_data[0], self.cal_data[1], orden, self.chs)
        # a_e = np.polyval(self.en_coef, a_c)
        # b_e = np.polyval(self.en_coef, b_c)
        # # new_fwhm = b_e-a_e
        new_fwhm = fw_ch*self.en_coef[-2]
        self.new_en_data = np.polyval(self.en_coef, self.cal_data[0])
        self.fw_coef,self.fwhm = fwhm_cal(
            self.new_en_data,
            new_fwhm,
            self.energy
        )
        self.new_fw_data = np.polyval(self.fw_coef, np.sqrt(self.new_en_data))
        if self.pld[0] is None:
            self.pld[0] = self.graf[0].plot(
                self.chs,self.energy*1000,
                pen=(0,0,200), name='Ajuste'
            )
            self.pld[1] = self.graf[0].plot(
                self.cal_data[0], self.cal_data[1]*1000,
                symbol='s', symbolSize=6.5, pen=None,
                symbolBrush=(255,211,0), symbolPen='k',
                name='Datos'
            )
        else:
            self.pld[0].setData(self.chs, self.energy*1000)
            self.pld[1].setData(self.cal_data[0], self.cal_data[1]*1000)
        if self.pld[2] is None:
            self.pld[2] = self.graf[1].plot(
                self.energy*1000, self.fwhm*1000,
                pen=(0,0,0), name='Ajuste'
            )
            if self.from_diag == 'enerfwhm':
                self.pld[3] = self.graf[1].plot(
                    self.cal_data[1]*1000, self.cal_data[2]*1000,
                    symbol='s', symbolSize=6.5, pen=None,
                    symbolBrush=(255,255,0), symbolPen='k',
                    name='Datos'
                )
        else:
            self.pld[2].setData(self.energy*1000, self.fwhm*1000)
            if self.from_diag == 'enerfwhm':
                self.pld[3].setData(self.cal_data[1]*1000, self.cal_data[2]*1000)
        self.upd_enlabel()
        self.upd_fwlabel()
    
    def upd_enlabel(self):
        en_str = []
        for i,j in enumerate(self.en_coef):
            if i == 0:
                en_str += ['<b>{:.3E}</b>'.format(j)]
            elif j >= 0:
                en_str += ['<b>+ {:.3E}</b>'.format(j)]
            else:
                en_str += ['<b>- {:.3E}</b>'.format(abs(j))]
        self.enlabel.setText(
            "Energia (keV) = {} \u2219 Canal³ {} \u2219 Canal² {} \u2219 Canal {}".format(
                *en_str            
            )
        )

    def upd_fwlabel(self):
        fw_str = []
        for i,j in enumerate(self.fw_coef):
            if i == 0:
                fw_str += ['<b>{:.3E}</b>'.format(j)]
            elif j >= 0:
                fw_str += ['<b>+ {:.3E}</b>'.format(j)]
            else:
                fw_str += ['<b>- {:.3E}</b>'.format(abs(j))]
        self.fwlabel.setText(
            "FWHM (keV) = {} \u221a Energia {}".format(
                *fw_str            
            )
        )

    def acept_clicked(self):
        self.can = True
        pg.setConfigOption('background', 'k')
        pg.setConfigOption('foreground', 'd')
        self.close()

#%% VENTANA PARA INTRODUCIR LOS VALORES DE CAL DE EFICIENCIA

class CalTableModel2(QtCore.QAbstractTableModel):
    '''Modelo de Tabla para la ventana de calibracion de eficiencias'''
    def __init__(self, data):
        QtCore.QAbstractTableModel.__init__(self)
        self.load_data(data) 

    def load_data(self, data):
        if data.any():
            # data = np.sort(data)
            self.input_energy = data[0]
            self.input_effi = data[1]
            self.input_err = data[2]
            _,ind = np.unique(self.input_energy, return_index=True)
            self.input_energy = self.input_energy[ind]
            self.input_effi = self.input_effi[ind]
            self.input_err = self.input_err[ind]
            self.row_count = len(self.input_energy)
        else:
            self.row_count = 0
            self.input_energy = np.empty(0)
            self.input_effi = np.empty(0)
            self.input_err = np.empty(0)
            self.column_count = 3

    def rowCount(self, parent=QtCore.QModelIndex()):
        return self.row_count

    def columnCount(self, parent=QtCore.QModelIndex()):
        return self.column_count

    def headerData(self, section, orientation, role):
        if role != QtCore.Qt.DisplayRole:
            return None
        if orientation == QtCore.Qt.Horizontal:
            return ("Energía\n(keV)", "Eficiencia", "Error\n(%)")[section]
        else:
            return "{}".format(section+1)

    def data(self, index, role=QtCore.Qt.DisplayRole):
        column = index.column()
        row = index.row()
        if role == QtCore.Qt.DisplayRole:
            if column == 0:
                return "{:10.3f}".format(self.input_energy[row])
            elif column == 1:
                return "{:.3E}".format(self.input_effi[row])
            elif column == 2:
                return "{:10.3f}".format(self.input_err[row])
        elif role == QtCore.Qt.BackgroundRole:
            return QtGui.QColor(QtCore.Qt.white)
        elif role == QtCore.Qt.TextAlignmentRole:
            return int(QtCore.Qt.AlignRight | QtCore.Qt.AlignCenter)
        return None

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled
        return QtCore.QAbstractItemModel.flags(self, index) | QtCore.Qt.ItemIsEditable

    def setData(self, index, value, role):
        if index.isValid() and role == QtCore.Qt.EditRole:
            column = index.column()
            row = index.row()
            try:
                value = float(value)
            except ValueError:
                return False
            if column == 0:
                self.input_energy[row] = value
            elif column == 1:
                self.input_effi[row] = value
            elif column ==2:
                self.input_err[row] = value
            self.dataChanged.emit(index, index)
            _,ind = np.unique(self.input_energy, return_index=True)
            self.input_energy = self.input_energy[ind]
            self.input_effi = self.input_effi[ind]
            self.input_err = self.input_err[ind]
            self.column_count = 3
            self.row_count = len(self.input_energy)
            self.layoutChanged.emit()
            return True
        return False

class Eff_Cal(QtGui.QDialog, UI_EFFCAL):
    '''Ventana para introducir los valores de calibracion de eficiencia'''
    def __init__(self, parent=None, data = np.empty(0),  imp=False):
        QtGui.QDialog.__init__(self,  parent)
        UI_EFFCAL.__init__(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setupUi(self)
        self.tablev = QTableView2()
        self.effic = SciDoubleSpinBox()
        self.energia = MySpinBox(123.456, Max=9999)
        self.incert = MySpinBox(12.345, Max=999)
        self.lay.addWidget(self.energia)
        self.lay.addWidget(self.effic)
        self.lay.addWidget(self.incert)
        self.boxview.addWidget(self.tablev)
        self.can = False
        self.cancel.clicked.connect(self.close)
        self.aceptar.clicked.connect(self.accept_clicked)
        # self.energia.setButtonSymbols(2)
        # self.effic.setButtonSymbols(2)
        # self.incert.setButtonSymbols(2)
        self.horizontal_header = self.tablev.horizontalHeader()
        self.vertical_header = self.tablev.verticalHeader()
        self.horizontal_header.setSectionResizeMode(
                                QtGui.QHeaderView.Stretch
                                )
        self.vertical_header.setSectionResizeMode(
                              QtGui.QHeaderView.ResizeToContents
                              )
        self.model = CalTableModel2(np.empty(0))
        self.data = data
        self.tablev.setModel(self.model)
        self.add.clicked.connect(self.add_data)
        self.model.layoutChanged.connect(self.tablev.resizeRowsToContents)
        self.borrar.clicked.connect(self.del_data)
        self.selec = self.tablev.selectionModel()
        self.selec.selectionChanged.connect(self.toggle_button)
        self.toggle_button()
        self.aceptar.setEnabled(False)
        self.tablev.installEventFilter(self)
        self.autom.setEnabled(imp)
        self.importar.clicked.connect(self.import_data)

    def import_data(self):
        self.model.load_data(self.data)
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.model.layoutChanged.emit()

    def accept_clicked(self):
        self.can = True
        self.close()

    def eventFilter(self, source, event):
        if (event.type() == QtCore.QEvent.KeyPress and
            event.matches(QtGui.QKeySequence.Copy)):
            self.copySelection()
            return True
        return False

    def copySelection(self):
        selection = self.tablev.selectedIndexes()
        if selection:
            rows = sorted(index.row() for index in selection)
            columns = sorted(index.column() for index in selection)
            rowcount = rows[-1] - rows[0] + 1
            colcount = columns[-1] - columns[0] + 1
            table = [[''] * colcount for _ in range(rowcount)]
            for index in selection:
                row = index.row() - rows[0]
                column = index.column() - columns[0]
                # table[row][column] = index.data()
                if column == 0:
                    table[row][column] = self.model.input_energy[row]
                elif column == 1:
                    table[row][column] = self.model.input_effi[row]
                elif column == 2:
                    table[row][column] = self.model.input_err[row]
            stream = io.StringIO()
            csv.writer(stream, delimiter='\t').writerows(table)
            QtWidgets.qApp.clipboard().setText(stream.getvalue())
        return

    def add_data(self):
        add_en = self.energia.value()
        add_eff = self.effic.value()
        add_inc = self.incert.value()
        if self.model.row_count == 0:
            self.model.input_energy = np.append(self.model.input_energy, add_en)
            self.model.input_effi = np.append(self.model.input_effi, add_eff)
            self.model.input_err = np.append(self.model.input_err, add_inc)
        else:
            self.model.input_energy = np.insert(self.model.input_energy, 0, add_en)
            self.model.input_effi = np.insert(self.model.input_effi, 0, add_eff)
            self.model.input_err = np.insert(self.model.input_err, 0, add_inc)
        _,ind = np.unique(self.model.input_energy, return_index=True)
        self.model.input_energy = self.model.input_energy[ind]
        self.model.input_effi = self.model.input_effi[ind]
        self.model.input_err = self.model.input_err[ind]
        self.model.row_count = len(self.model.input_energy)
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.model.layoutChanged.emit()

    def del_data(self):
        del_row = []
        for i in self.selec.selectedIndexes():
            # if i is not []:
            del_row += [i.row()]
        self.model.input_energy = np.delete(self.model.input_energy, del_row)
        self.model.input_effi = np.delete(self.model.input_effi, del_row)
        self.model.input_err = np.delete(self.model.input_err, del_row)
        _,ind = np.unique(self.model.input_energy, return_index=True)
        self.model.input_energy = self.model.input_energy[ind]
        self.model.input_effi = self.model.input_effi[ind]
        self.model.input_err = self.model.input_err[ind]
        self.model.row_count = len(self.model.input_energy)
        self.tablev.clearSelection()
        self.model.layoutChanged.emit()
        if self.model.row_count >= 3:
            self.aceptar.setEnabled(True)
        else:
            self.aceptar.setEnabled(False)
        self.toggle_button()

    def toggle_button(self):
        self.borrar.setEnabled(self.selec.hasSelection())
        if self.model.row_count == 0:
            self.borrar.setEnabled(False)

_float_re = re.compile(r'(([+-]?\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?)')

def valid_float_string(string):
    match = _float_re.search(string)
    return match.groups()[0] == string if match else False

class FloatValidator(QtGui.QValidator):
    # def __init__(self):
    #     QtGui.QValidator.__init__(self)

    def validate(self, string, position):
        if valid_float_string(string):
            state = QtGui.QValidator.Acceptable
        elif string == "" or string[position-1] in 'Ee.-+':
            state = QtGui.QValidator.Intermediate
        else:
            state = QtGui.QValidator.Invalid
        return (state, string, position)

    def fixup(self, text):
        match = _float_re.search(text)
        return match.groups()[0] if match else ""

class MySpinBox(QtGui.QDoubleSpinBox):
    def __init__(self, value, Min=0, Max=1):
        QtGui.QDoubleSpinBox.__init__(self)
        self.setMinimum(Min)
        self.setMaximum(Max)
        self.setDecimals(3)
        self.setButtonSymbols(2)
        self.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )
        self.setValue(value)

class SciDoubleSpinBox(QtGui.QDoubleSpinBox):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setMinimum(0)
        self.setMaximum(1)
        self.validator = FloatValidator()
        self.setDecimals(100)
        self.setValue(1.23e-4)
        self.setButtonSymbols(2)
        self.setAlignment(
                    QtCore.Qt.AlignRight | QtCore.Qt.AlignVCenter
                )

    def validate(self, text, position):
        return self.validator.validate(text, position)

    def fixup(self, text):
        return self.validator.fixup(text)

    def valueFromText(self, text):
        return float(text)

    def textFromValue(self, value):
        return format_float(value)

    def stepBy(self, steps):
        text = self.cleanText()
        groups = _float_re.search(text).groups()
        decimal = float(groups[1])
        decimal += steps
        new_string = "{:g}".format(decimal) + (groups[3] if groups[3] else "")
        self.lineEdit().setText(new_string)


def format_float(value):
    """Modified form of the 'g' format specifier."""
    string = "{:.3E}".format(value).replace("E+", "e+")
    string = re.sub("e(-?)0*(\d+)", r"e\1\2", string)
    return string

#%%
## visualizador de calibracion de eficiencia
def eff_cal(en, eff, orden, energy):
    ln_en = np.log(en)
    ln_eff = np.log(eff)
    fit = np.polyfit(ln_en, ln_eff, orden)
    eff_ret = np.exp(np.polyval(fit, np.log(energy)))
    return fit, eff_ret

class Eff_CalShow(QtGui.QDialog, UI_EFFCALSHOW):
    '''Venatana que muestra los valores de calibración de eficiencia'''
    def __init__(self,
                 parent=None,
                 cal_data=np.empty(0),
                 spec_info=None,  # from_diag='values',
                 
                 fname=''
        ):
        QtGui.QDialog.__init__(self, parent)
        UI_EFFCALSHOW.__init__(self)
        self.setWindowModality(QtCore.Qt.ApplicationModal)
        self.setupUi(self)
        pg.setConfigOption('background', 'w')
        pg.setConfigOption('foreground', 'k')
        # self.from_diag = from_diag
        self.graf = pg.PlotWidget()
        self.pld = [None, None]  #plotdata
        self.layeff.addWidget(self.graf)
        self.graf.setBackground('w')
        self.graf.setMouseEnabled(x=False, y=False)
        self.graf.hideButtons()
        self.graf.showGrid(x=True, y=True)
        self.graf.setLabel('bottom', 'Energía', 'eV', color='black')
        self.graf.setLabel('left', 'Eficiencia', color='black')
        self.graf.setTitle('Eficiencia vs Energía')
        self.graf.setLogMode(False, True)
        self.graf.addLegend()
        self.can = False
        self.cancel.clicked.connect(self.close)
        self.cal_data = cal_data
        self.ener = spec_info.energy
        # self.en_coef = spec_info.en_coef
        # self.fw_coef = spec_info.fw_coef
        self.en_data = self.cal_data[0]
        self.eff_data = self.cal_data[1]
        self.file.setText('<b>{:s}</b>'.format(fname))
        ord_in = 2 #  len(np.roots(self.en_coef))
        self.orden.setValue(ord_in)
        self.re_calc()
        self.orden.valueChanged.connect(self.orden_changed)
        self.aceptar.clicked.connect(self.acept_clicked)
        self.orden.setMaximum(len(self.cal_data[0])-1)

    def orden_changed(self):
        self.re_calc()
        self.orden.lineEdit().deselect()

    def re_calc(self):
        orden = self.orden.value()
        self.eff_coef, self.effic = eff_cal(
            self.en_data, self.eff_data, orden, self.ener
        )
        print(self.eff_coef)        
       
        if self.pld[0] is None:
            self.pld[0] = self.graf.plot(
                self.ener*1000, self.effic,
                pen=(0,0,200), name='Ajuste'
            )
            self.pld[1] = self.graf.plot(
                self.en_data*1000, self.eff_data,
                symbol='s', symbolSize=6.5, pen=None,
                symbolBrush=(255,211,0), symbolPen='k',
                name='Datos'
            )
        else:
            self.pld[0].setData(self.ener*1000, self.effic)
            self.pld[1].setData(self.en_data*1000, self.eff_data)
        
        self.upd_efflabel()
    
    def upd_efflabel(self):
        en_str = ['ln(Eficiencia) = ']
        orden = len(self.eff_coef)-1
        for i,j in enumerate(self.eff_coef):
            if i == 0:
                en_str += ['<b>{:.3E}</b> \u2219 ln(Energía)^{:d} '.format(j, orden-i)]
            elif i == orden:
                if j < 0:
                    en_str += ['<b>- {:.3E}</b>'.format(abs(j))]
                else:
                    en_str += ['<b>+ {:.3E}</b>'.format(j)]
            elif j >= 0:
                en_str += ['<b>+ {:.3E}</b> \u2219 ln(Energía)^{:d} '.format(j, orden-i)]
            else:
                en_str += ['<b>- {:.3E}</b> \u2219 ln(Energía)^{:d} '.format(abs(j), orden-i)]
        
        self.efflabel.setText(''.join(en_str))

    def acept_clicked(self):
        self.can = True
        pg.setConfigOption('background', 'k')
        pg.setConfigOption('foreground', 'd')
        self.close()

#%%
if __name__ == "__main__":
    print('Hola QT')
    app = QtGui.QApplication(sys.argv)
    window = Eff_Cal()
    window.show()
    sys.exit(app.exec_())        
