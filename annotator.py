# coding: utf-8
# python2

# Attribution mapping:
# 0 -> Not annotated
# 1 -> Occlusion
# 2 -> Deformation
# 3 -> Blur
# 4 -> Occlusion + Blur

from __future__ import print_function
import re
import sys
import os.path
from PyQt4 import QtCore, QtGui, uic
from PyQt4.QtCore import Qt
import numpy as np
from PIL import Image
from PIL.ImageQt import ImageQt
from scipy.io import loadmat, savemat


qtCreatorFile = 'GUI.ui'
uiMainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)


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

        # Init attribution data
        self.seqAttrFile = None
        self.labels = None

        # Init ground-truth data
        self.gts = None

    def initSeqList(self):
        self.seq_list = sorted(os.listdir(self.datasetRoot))
        for seq in self.seq_list:
            if seq == 'anno' or seq == 'MEEM':
                continue
            item = QtGui.QListWidgetItem(seq)
            self.seqList.addItem(item)
        self.seqList.itemClicked.connect(self.initSeq)
        self.seqList.itemActivated.connect(self.initSeq)

    def initAnnotatorWidgets(self):
        self.imageRow = 3
        self.imageCol = 3
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
        '''
        Set all control buttons not clickable, and ignore all key press evnet.
        '''
        self.prevPage.setEnabled(False)
        self.prevPage.keyPressEvent = lambda x: x.ignore()
        self.prevPage.clicked.connect(self.showPrevPage)
        self.nextPage.setEnabled(False)
        self.nextPage.keyPressEvent = lambda x: x.ignore()
        self.nextPage.clicked.connect(self.showNextPage)
        self.prevSeq.setEnabled(False)
        self.prevSeq.keyPressEvent = lambda x: x.ignore()
        self.nextSeq.setEnabled(False)
        self.nextSeq.keyPressEvent = lambda x: x.ignore()
        self.saveButton.setEnabled(False)
        self.saveButton.keyPressEvent = lambda x: x.ignore()
        self.saveButton.clicked.connect(self.saveAttrData)

    def initSeq(self, item):
        '''
        Init and show the first page of the current sequence,
        then read the attribution data of it.
        '''
        self.currentSeq = str(item.text())
        # Read ground-truth of this sequence
        self.readGTs()

        # Prepare images of this sequence
        self.seqImgDir = os.path.join(self.datasetRoot, self.currentSeq, 'img')
        self.imgNames = sorted(os.listdir(self.seqImgDir))
        self.seqLen = len(self.imgNames)

        # Init page indeies
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

        # Read the attribution data
        self.readAttrData()

        # Set attribution button checkable, clean attribution button state and
        # pass attribution list to every annotator widget.
        for annotatorWidget in self.annotatorWidgets:
            annotatorWidget.initAttrButton()
            annotatorWidget.setLabels(self.labels)

        # Show the attribution data
        self.showAttrData()

        # Enable save button
        self.saveButton.setEnabled(True)

    def readGTs(self):
        '''
        Read the ground-truth of current sequence.
        '''
        gtFilePath = os.path.join(
            self.datasetRoot, self.currentSeq, 'groundtruth_rect.txt')
        f = open(gtFilePath)
        seq_pattern = r'[\d]+'
        # origin gt format is [x, y, w, h]
        self.gts = [map(int, re.findall(seq_pattern, line)) for line in list(f)]
        # convert gt format to [x1, y1, x2, y2]
        # self.gts = [[x, y, x + w, y + h] for (x, y, w, h) in self.gts]

    def showImages(self):
        '''
        Show images of the current sequence by start and end index
        '''
        for i in range(self.startIdx, self.endIdx):
            imagePath = os.path.join(self.seqImgDir, self.imgNames[i])
            bbox = self.gts[i]
            self.annotatorWidgets[i - self.startIdx].setImage(imagePath, bbox)
            # frameID = int(self.imgNames[i].split('.')[0]) - 1
            self.annotatorWidgets[i - self.startIdx].setFrameID(i)
        self.update()

    def readAttrData(self):
        '''
        Read the attribution data from mat file.
        If the file does not exist, init it by all 0.
        '''
        self.seqAttrFile = os.path.join(self.attrRoot, self.currentSeq)
        try:
            attrData = loadmat(self.seqAttrFile)['label']
            print('Succesfully load mat file for %s' % self.currentSeq)
            rawData = [label[0] for label in attrData]
            rawDataLen = len(rawData)
            if rawDataLen < self.seqLen:
                # If some frame have not been annotated, then use 0 to fill it.
                print('Only %d frames of sequence %s have been annotated before.' %
                      (rawDataLen, self.currentSeq))
                print('Padding the attribution data by 0')
                self.labels = [0 for i in range(self.seqLen)]
                for i in range(rawDataLen):
                    self.labels[i] = rawData[i]
            else:
                self.labels = rawData
        except IOError, e:
            print('When init sequence %s, no mat file found' % self.currentSeq)
            self.labels = [0 for i in range(self.seqLen)]
            print('Init the attribution data by 0')

    def showAttrData(self):
        '''
        Show attribution data of the current sequence by start and end index
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
        Save attribution data of the current sequence
        '''
        try:
            if self.seqAttrFile is not None:
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
        '''
        Calculate start and end index for previous page.
        Be careful when reach the head point of the sequence.
        '''
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
        '''
        Calculate start and end index for next page.
        Be careful when reach the tail point of the sequence.
        '''
        self.startIdx = self.endIdx
        self.endIdx = self.startIdx + self.pageSize
        if self.endIdx >= self.seqLen:
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
        '''
        Save the attribution changes and quit.
        '''
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


class ResizeImage(QtGui.QLabel):
    '''
    A widget that display a resizable image.
    '''

    def __init__(self, pixmap=None):
        super(ResizeImage, self).__init__()
        self.setFrameStyle(QtGui.QFrame.StyledPanel)
        self.pixmap = pixmap
        # if pixmap is not None:
        #     self.setPixmap(pixmap)

    def paintEvent(self, event):
        if self.pixmap is None:
            super(ResizeImage, self).paintEvent(event)
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


class ImageWindow(QtGui.QDialog):
    '''
    A window that display a resizable image.
    '''

    def __init__(self, pixmap, title):
        super(ImageWindow, self).__init__()
        self.layout = QtGui.QVBoxLayout(self)

        self.imageLabel = ResizeImage(pixmap)
        self.layout.addWidget(self.imageLabel)

        # Init annotator buttons
        # self.buttonLayout = QtGui.QHBoxLayout()
        # self.buttonLayout.setSpacing(0)
        # self.buttonGroup = QtGui.QButtonGroup()
        # self.buttons = []
        # labels = ['O', 'D', 'B', 'OB']
        # label_colors = ['LightCoral', 'Chartreuse', 'Aquamarine', 'CadetBlue']
        # for i in range(0, 4):
        #     button = QtGui.QRadioButton(labels[i])
        #     button.setStyleSheet('QRadioButton:checked { background-color: %s }'
        #                          % label_colors[i])
        #     button.setCheckable(True)
        #     if i == attr - 1:
        #         button.setChecked(True)
        #     self.buttons.append(button)
        #     self.buttonLayout.addWidget(button)
        #     self.buttonGroup.addButton(button, i + 1)
        # self.layout.addLayout(self.buttonLayout)

        self.setWindowTitle(title)
        self.resize(800, 600)


class ImageWidget(ResizeImage):
    '''
    A widget that display a resizable image, and show the origin (big) image when click it.
    '''

    def __init__(self, imagePath=None, bbox=None):
        super(ImageWidget, self).__init__()
        if imagePath is not None:
            self.setImage(imagePath, bbox)
            self.title = imagePath
        else:
            self.pixmap = None
            self.setText('No sequence selected')
            self.title = 'No image data.'

    def setImage(self, imagePath, bbox):
        '''
        Read the image by PIL, and crop this image by input bounding box,
        then covert the result to QPixmap format.
        '''
        self.pixmap = QtGui.QPixmap(imagePath)
        self.title = imagePath
        if bbox is not None:
            # Draw ground-truth as rectangle
            painter = QtGui.QPainter(self.pixmap)
            pen = QtGui.QPen(QtGui.QColor('red'), 2)
            painter.setPen(pen)
            painter.drawRect(*bbox)

    def mouseReleaseEvent(self, event):
        imgWindow = ImageWindow(self.pixmap, self.title)
        imgWindow.exec_()


class AnnotatorWidget(QtGui.QWidget):
    '''
    A widget display the annotated frame image and annotated buttons.
    '''

    def __init__(self, frameID=None, labels=None):
        super(AnnotatorWidget, self).__init__()
        self.frameID = frameID
        self.labels = labels
        self.layout = QtGui.QVBoxLayout()
        self.imageWidget = ImageWidget()

        # Init annotator buttons
        self.buttonLayout = QtGui.QHBoxLayout()
        self.buttonLayout.setSpacing(0)
        self.buttonGroup = QtGui.QButtonGroup()
        self.buttons = []
        labels = ['O', 'D', 'B', 'OB']
        label_colors = ['LightCoral', 'Chartreuse', 'Aquamarine', 'CadetBlue']
        for i in range(0, 4):
            button = QtGui.QRadioButton(labels[i])
            button.setStyleSheet('QRadioButton:checked { background-color: %s }'
                                 % label_colors[i])
            button.setCheckable(False)
            self.buttons.append(button)
            self.buttonLayout.addWidget(button)
            self.buttonGroup.addButton(button, i + 1)
        self.buttonGroup.buttonClicked.connect(self.attrSelected)

        # Tight all widgets together
        self.layout.addWidget(self.imageWidget)
        self.layout.addLayout(self.buttonLayout)
        self.layout.setStretch(1, 6)
        self.setLayout(self.layout)

    def setFrameID(self, frameID):
        self.frameID = frameID

    def setLabels(self, labels):
        '''
        Let this widget can see attribution list of certain sequence.
        '''
        self.labels = labels

    def setImage(self, imagePath, bbox):
        self.imageWidget.setImage(imagePath, bbox)

    def setAttr(self, attr):
        if attr != 0:
            self.buttons[attr - 1].setChecked(True)
        else:
            # Clean attribution button state
            self.buttonGroup.setExclusive(False)
            for button in self.buttons:
                button.setChecked(False)
            self.buttonGroup.setExclusive(True)

    def initAttrButton(self):
        '''
        Set attribution button checkable, and clean attribution button state
        '''
        self.buttonGroup.setExclusive(False)
        for button in self.buttons:
            button.setCheckable(True)
            button.setChecked(False)
            # Disable key event handler for this button
            button.keyPressEvent = lambda x: x.ignore()
        self.buttonGroup.setExclusive(True)

    def attrSelected(self):
        '''
        When some radio button is checked, change the attribution of the
        corresponding frame.

        '''
        if self.labels is not None:
            self.labels[self.frameID] = self.buttonGroup.checkedId()

if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    dataRoot = '/home/feather/Dataset/otb'
    window = MyApp(dataRoot)
    window.show()
    sys.exit(app.exec_())
