# coding: utf-8
# python2

from __future__ import print_function
import sys
import os.path
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt
from scipy.io import loadmat


qtCreatorFile = 'GUI.ui'
uiMainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
file_type = ['jpg', 'jpeg', 'tif', 'bmp', 'gif']


class MyApp(QtGui.QMainWindow, uiMainWindow):
    def __init__(self, data_root):
        QtGui.QMainWindow.__init__(self)
        uiMainWindow.__init__(self)
        self.setupUi(self)
        self.datasetRoot = os.path.join(dataRoot, 'benchmarkDatasets')
        self.attrRoot = os.path.join(dataRoot, 'otb-1occ-2def-3blur-4OccBlur')

        # Init sequence list
        self.initSeqList()
        self.currentSeq = None

        # Init annotator
        self.initAnnotatorWidgets()

        # Init control buttons
        self.initControlButtons()

    def initSeqList(self):
        self.seq_list = os.listdir(self.datasetRoot)
        for seq in self.seq_list:
            if seq == 'anno':
                continue
            item = QtGui.QListWidgetItem(seq)
            self.seqList.addItem(item)
        self.seqList.itemClicked.connect(self.initSeq)

    def initAnnotatorWidgets(self):
        self.imageRow = 3
        self.imageCol = 4
        self.pageSize = self.imageRow*self.imageCol
        self.annotatorWidgets = []
        # self.labelWidgets = []
        for i in range(self.imageRow):
            for j in range(self.imageCol):
                # idx = i * self.imageCol + j
                annotatorWidget = AnnotatorWidget()
                self.annotatorWidgets.append(annotatorWidget)
                # label = QtGui.QLabel('tset')
                # self.labelWidgets.append(label)
                # tempLayout = QtGui.QVBoxLayout()
                # tempLayout.addWidget(self.imageWidgets[idx])
                # tempLayout.addWidget(self.labelWidgets[idx])
                # tempLayout.setStretch(1, 0)
                # self.imageLayout.addLayout(tempLayout, i, j)
                self.imageLayout.addWidget(annotatorWidget, i, j)
        # Init index of images in certainc sequence
        self.startIdx = None
        self.endIdx = None

    def initControlButtons(self):
        self.prevPage.setEnabled(False)
        self.prevPage.clicked.connect(self.showPrevPage)
        self.nextPage.setEnabled(False)
        self.nextPage.clicked.connect(self.showNextPage)
        self.prevSeq.setEnabled(False)
        self.nextSeq.setEnabled(False)

    def initSeq(self, item):
        '''
        Init and show the first page of the selected sequence,
        then read the attribution data of it.
        '''
        self.currentSeq = str(item.text())
        self.seqImgDir = os.path.join(self.datasetRoot, self.currentSeq, 'img')
        self.imgNames = os.listdir(self.seqImgDir)
        self.seqLen = len(self.imgNames)
        self.startIdx = 0
        self.prevPage.setEnabled(False)
        if self.seqLen <= self.pageSize:
            self.endIdx = self.seqLen
            self.nextPage.setEnabled(False)
        else:
            self.endIdx = self.pageSize
            self.nextPage.setEnabled(True)
        self.showImages()

        # Read the attribution data
        self.seqAttrFile = os.path.join(self.attrRoot, self.currentSeq)
        try:
            attrData = loadmat(self.seqAttrFile)
            self.labels = [label[0] for label in attrData['label']]
            self.showAttrData()
            print(self.labels)
        except Exception, e:
            print(e)

    def showImages(self):
        '''
        Show images of the selected sequence by start and end index
        '''
        for i in range(self.startIdx, self.endIdx):
            imagePath = os.path.join(self.seqImgDir, self.imgNames[i])
            self.annotatorWidgets[i-self.startIdx].setImage(imagePath)
        self.update()

    def showAttrData(self):
        '''
        Show attribution data of the selected sequence by start and end index
        '''
        for i in range(self.startIdx, self.endIdx):
            self.annotatorWidgets[i-self.startIdx].setAttr(self.labels[i])
        # self.update()

    def showPrevPage(self):
        self.endIdx = self.startIdx
        self.startIdx = self.startIdx - self.pageSize
        if self.startIdx <= 0:
            # Reset indeies
            self.startIdx = 0
            self.endIdx = self.pageSize
            self.prevPage.setEnabled(False)
        else:
            self.prevPage.setEnabled(True)
        self.nextPage.setEnabled(True)
        self.showImages()
        self.showAttrData()

    def showNextPage(self):
        self.startIdx = self.endIdx
        self.endIdx = self.startIdx + self.pageSize
        if self.endIdx > self.seqLen:
            # Reset indeies
            self.endIdx = self.seqLen
            self.startIdx = self.endIdx - self.pageSize
            self.nextPage.setEnabled(False)
        else:
            self.nextPage.setEnabled(True)
        self.prevPage.setEnabled(True)
        self.showImages()
        self.showAttrData()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_N and self.startIdx is not None:
            self.showNextPage()
        elif e.key() == Qt.Key_P and self.startIdx is not None:
            self.showPrevPage()
        elif e.key() == Qt.Key_Escape:
            self.close()


class ImageWidget(QtGui.QLabel):
    def __init__(self, img=None):
        super(ImageWidget, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        if img is not None:
            self.setImage(img)
        else:
            self.pixmap = None

    def setImage(self, img):
        self.pixmap = QtGui.QPixmap(img)
        # self.setPixmap(self.pixmap)

    def paintEvent(self, event):
        if self.pixmap is None:
            return
        size = self.size()
        painter = QtGui.QPainter(self)
        point = QtCore.QPoint(0, 0)
        scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio,
                                       transformMode=Qt.SmoothTransformation)
        # start painting the label from left upper corner
        point.setX((size.width() - scaledPix.width())/2)
        point.setY((size.height() - scaledPix.height())/2)
        # print(point.x(), ' ', point.y())
        painter.drawPixmap(point, scaledPix)


class AnnotatorWidget(QtGui.QWidget):

    def __init__(self, frameID=None):
        super(AnnotatorWidget, self).__init__()
        self.frameID = frameID
        self.layout = QtGui.QVBoxLayout()
        self.imageWidget = ImageWidget()

        # Init annotator buttons
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.setSpacing(0)
        self.buttons = []
        labels = ['O', 'D', 'B', 'OB']
        for i in range(0, 4):
            button = QtGui.QRadioButton(labels[i])
            self.buttons.append(button)
            self.buttonLayout.addWidget(button)
        self.layout.addWidget(self.imageWidget)
        self.layout.addLayout(self.buttonLayout)
        self.layout.setStretch(1, 6)
        self.setLayout(self.layout)

    def setImage(self, img):
        self.imageWidget.setImage(img)

    def setAttr(self, attr):
        self.buttons[attr-1].setChecked(True)

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    dataRoot = 'f:\otb'
    window = MyApp(dataRoot)
    window.show()
    sys.exit(app.exec_())
