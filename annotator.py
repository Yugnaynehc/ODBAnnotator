# coding: utf-8
# python2

# Attribution mapping:
# 0 -> Not annotated
# 1 -> Occlusion
# 2 -> Deformation
# 3 -> Blur
# 4 -> Occlusion + Blur

from __future__ import print_function
import sys
import os.path
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt
import numpy as np
from scipy.io import loadmat, savemat


qtCreatorFile = 'GUI.ui'
uiMainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


class MyApp(QtGui.QMainWindow, uiMainWindow):

    def __init__(self, data_root):
        QtGui.QMainWindow.__init__(self)
        uiMainWindow.__init__(self)
        self.setupUi(self)
        self.datasetRoot = os.path.join(dataRoot, 'OTB100')
        self.attrRoot = os.path.join(dataRoot, 'otb-1occ-2def-3blur-4OccBlur')

        # Init sequence list
        self.initSeqList()
        self.currentSeq = None

        # Init annotator
        self.initAnnotatorWidgets()

        # Init control buttons
        self.initControlButtons()

        # Init attribution data
        self.labels = None

    def initSeqList(self):
        self.seq_list = sorted(os.listdir(self.datasetRoot))
        for seq in self.seq_list:
            if seq == 'anno':
                continue
            item = QtGui.QListWidgetItem(seq)
            self.seqList.addItem(item)
        self.seqList.itemClicked.connect(self.initSeq)
        self.seqList.itemActivated.connect(self.initSeq)

    def initAnnotatorWidgets(self):
        self.imageRow = 3
        self.imageCol = 4
        self.pageSize = self.imageRow * self.imageCol
        self.annotatorWidgets = []
        for i in range(self.imageRow):
            for j in range(self.imageCol):
                annotatorWidget = AnnotatorWidget()
                self.annotatorWidgets.append(annotatorWidget)
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
        self.imgNames = sorted(os.listdir(self.seqImgDir))
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

        # If some sequence had been loaded before, the attribution changes need
        # to be saved.
        if self.labels is not None:
            self.saveAttrData()

        # Set attribution button checkable and clean state
        for annotatorWidget in self.annotatorWidgets:
            annotatorWidget.setAttrCheckable()

        # Read and show the attribution data
        self.readAttrData()
        self.showAttrData()

    def showImages(self):
        '''
        Show images of the selected sequence by start and end index
        '''
        for i in range(self.startIdx, self.endIdx):
            imagePath = os.path.join(self.seqImgDir, self.imgNames[i])
            self.annotatorWidgets[i - self.startIdx].setImage(imagePath)
            # frameID = int(self.imgNames[i].split('.')[0]) - 1
            self.annotatorWidgets[i - self.startIdx].setFrameID(i)
        self.update()

    def readAttrData(self):
        self.seqAttrFile = os.path.join(self.attrRoot, self.currentSeq)
        try:
            attrData = loadmat(self.seqAttrFile)['label']
            print('Succesfully load mat file for %s' % self.currentSeq)
            rawData = [label[0] for label in attrData]
            rawDataLen = len(rawData)
            if rawDataLen < self.seqLen:
                print('Only %d frames of sequence %s have been annotated before.' %
                      (rawDataLen, self.currentSeq))
                print('Padding the attribution data by 0')
                self.labels = [0 for i in range(self.seqLen)]
                for i in range(rawDataLen):
                    self.labels[i] = rawData[i]
            else:
                self.labels = rawData
            # print(self.labels)
        except IOError, e:
            print('When init sequence %s, no mat file found' % self.currentSeq)
            self.labels = [0 for i in range(self.seqLen)]
            print('Init the attribution data by 0')

    def showAttrData(self):
        '''
        Show attribution data of the selected sequence by start and end index
        '''
        try:
            for i in range(self.startIdx, self.endIdx):
                self.annotatorWidgets[i - self.startIdx].setAttr(self.labels[i])
            # self.update()
        except Exception, e:
            print('When show attribution data, ')
            print(e)

    def saveAttrData(self):
        '''
        Save attribution data of the selected sequence
        '''
        try:
            # Reshape the attribute list to matrix
            saveData = np.array(self.labels).reshape(-1, 1)
            # print(saveData)
            target = self.seqAttrFile + '.mat'
            savemat(target, {'label': saveData}, do_compression=True)
            print('Save to %s\n' % target)
        except Exception, e:
            print('When save attribution data, ')
            print(e)

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

    def saveAndQuit(self):
        self.saveAttrData()
        self.close()

    def keyPressEvent(self, e):
        if e.key() == Qt.Key_Right and self.endIdx is not None:
            if self.endIdx != self.seqLen:
                self.showNextPage()
        elif e.key() == Qt.Key_Left and self.startIdx is not None:
            if self.startIdx != 0:
                self.showPrevPage()
        elif e.key() == Qt.Key_Backspace:
            if self.windowState() & Qt.WindowFullScreen:
                self.showNormal()
            else:
                self.showFullScreen()
        elif e.key() == Qt.Key_Escape:
            self.saveAndQuit()


class ImageWidget(QtGui.QLabel):

    def __init__(self, img=None):
        super(ImageWidget, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        if img is not None:
            self.setImage(img)
        else:
            self.pixmap = None
            self.setText('No sequence selected')

    def setImage(self, img):
        self.pixmap = QtGui.QPixmap(img)
        # self.setPixmap(self.pixmap)

    def paintEvent(self, event):
        if self.pixmap is None:
            super(ImageWidget, self).paintEvent(event)
            return
        size = self.size()
        painter = QtGui.QPainter(self)
        point = QtCore.QPoint(0, 0)
        scaledPix = self.pixmap.scaled(size, Qt.KeepAspectRatio,
                                       transformMode=Qt.SmoothTransformation)
        # start painting the label from left upper corner
        point.setX((size.width() - scaledPix.width()) / 2)
        point.setY((size.height() - scaledPix.height()) / 2)
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
        self.buttonGroup = QtGui.QButtonGroup()
        self.buttons = []
        labels = ['O', 'D', 'B', 'OB']
        for i in range(0, 4):
            button = QtGui.QRadioButton(labels[i])
            button.setCheckable(False)
            self.buttons.append(button)
            self.buttonLayout.addWidget(button)
            self.buttonGroup.addButton(button, i + 1)
        self.layout.addWidget(self.imageWidget)
        self.layout.addLayout(self.buttonLayout)
        self.layout.setStretch(1, 6)
        self.setLayout(self.layout)

        self.buttonGroup.buttonClicked.connect(self.attrSelected)

    def setFrameID(self, frameID):
        self.frameID = frameID

    def setImage(self, img):
        self.imageWidget.setImage(img)

    def setAttr(self, attr):
        if attr != 0:
            self.buttons[attr - 1].setChecked(True)

    def setAttrCheckable(self):
        self.buttonGroup.setExclusive(False)
        for button in self.buttons:
            button.setCheckable(True)
            button.setChecked(False)
        self.buttonGroup.setExclusive(False)

    def attrSelected(self):
        print(self.frameID, self.buttonGroup.checkedId())

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    dataRoot = '/home/feather/Dataset'
    window = MyApp(dataRoot)
    window.show()
    sys.exit(app.exec_())
