# -*- coding: utf-8 -*-
"""
Created on Mon Dec 27 12:18:36 2021

TITLE: 

@author: Alejandro Condori aleja
E-mail: alejandrocondori2@gmail.com
"""

import sys

# from PyQt5.QtCore import QEvent, QTimer, pyqtSlot
# from PyQt5.QtGui import QTextDocument, QPainter, QFontMetrics
# from PyQt5.QtWidgets import QLabel, QApplication
from pyqtgraph.Qt import QtGui, QtCore


class Marquee(QtGui.QLabel):

    x = 0
    paused = False
    document = None

    def __init__(self, speed=50, width=450):
        QtGui.QLabel.__init__(self)
        self.fm = QtGui.QFontMetrics(self.font())
        self.setFixedSize(width, 25)
        self.speed = speed
        self.ended = False

    def setText(self, value):
        self.x = 0
        self.document = QtGui.QTextDocument(self)
        self.document.setPlainText(value)
        # I multiplied by 1.06 because otherwise the text goes on 2 lines
        self.document.setTextWidth(self.fm.width(value) * 1.06)
        self.document.setUseDesignMetrics(True)
        # self.count = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.translate)

    @QtCore.pyqtSlot()
    def translate(self):
        if not self.paused and not self.ended:
            if self.width() - self.x < self.document.textWidth() and not self.ended:
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

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    w = Marquee(100)
    w.setText('Lorem ipsum dolor sit amet, consecteturasdadadadd adasdsa dasdasdsa dasd as das dadad  adipiscing elit...')
    w.show()
    sys.exit(app.exec_())
    
    
class AniLabel(QtGui.QLabel):

    x = 0
    paused = False
    document = QtGui.QTextDocument()

    def __init__(self, speed=50, width=350):
        QtGui.QLabel.__init__(self, '')
        self.fm = QtGui.QFontMetrics(self.font())
        
        self.setFixedSize(width, 30)
        self.speed = speed
        self.ended = False
        self.count = 0
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.translate)
    def __init__(self, speed=50, width=450):
        QtGui.QLabel.__init__(self)
        self.fm = QtGui.QFontMetrics(self.font())
        self.setFixedSize(width, 25)
        self.speed = speed
        self.ended = False
        

    def setText(self, value):
        self.x = 0
        self.document.setPlainText(value)
        # I multiplied by 1.06 because otherwise the text goes on 2 lines
        self.document.setTextWidth(self.fm.width(value) * 1.06)
        self.document.setUseDesignMetrics(True)
        self.repaint()

    @QtCore.pyqtSlot()
    def translate(self):
        if not self.paused and not self.ended:
            if self.width() - self.x < self.document.textWidth() and not self.ended:
                self.x -= 1
                self.count = 0
            else:
                self.ended = True
            self.repaint()
        else:
            self.count += 1
            if self.count == 100:
                self.x = 20
                self.ended = False
            self.repaint()
        self.repaint()

    def event(self, event):
        if self.width() - self.x < self.document.textWidth():
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