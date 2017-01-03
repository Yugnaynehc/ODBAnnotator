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

validExt = ['jpg', 'JPG', 'jpeg', 'JPEG', 'png', 'PNG']

# Some sequence has 2 ground-truth file
specialSeq = ['Skating2', 'Jogging']


class MyApp(QtGui.QMainWindow, uiMainWindow):

    def __init__(self, data_root):
        QtGui.QMainWindow.__init__(self)
        uiMainWindow.__init__(self)
        self.setupUi(self)
        self.datasetRoot = os.path.join(dataRoot, 'imageFiles')
        self.attrRoot = os.path.join(dataRoot, 'annotateFiles')

        self.log = False

        # Read frame range file
        self.initFrameRange()

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

    def initFrameRange(self):
        self.frameRangeFile = os.path.join(dataRoot, 'frameRange.txt')
        f = open(self.frameRangeFile)
        self.frameRange = {}
        for l in list(f):
            raw = l.split(' ')
            # Every line format is [frame_name, start_frame, end_frame]
            self.frameRange[raw[0]] = [int(raw[1]), int(raw[2])]

    def initSeqList(self):
        self.seq_list = os.listdir(self.datasetRoot)
        for seq in specialSeq:
            self.seq_list.remove(seq)
            for i in range(1, 3):
                self.seq_list.append('%s-%d' % (seq, i))
        self.seq_list = sorted(self.seq_list)
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
        # If some sequence had been loaded before, the attribution changes need
        # to be saved.
        if self.currentSeq is not None:
            self.saveAttrData()

        self.currentSeq = str(item.text())

        # Get current sequence's frames and GTs
        self.initFrameAndGT()

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

    def initFrameAndGT(self):
        '''
        Read the frames and ground-truths of current sequence.
        '''
        # Prepare images of current sequence
        # First check current sequence is special or not
        probe = self.currentSeq.split('-')
        if len(probe) == 2:
            # if current sequence is the special sequence
            self.currentSeqSpecial = True
            self.seqImgDir = os.path.join(self.datasetRoot, probe[0], 'img')
        else:
            self.currentSeqSpecial = False
            self.seqImgDir = os.path.join(self.datasetRoot, self.currentSeq, 'img')
        # Get current sequence's frame range
        frs, fre = self.frameRange[self.currentSeq]

        # Get current sequence's frame names (need filter some files)
        self.imgNames = [fn for fn in os.listdir(self.seqImgDir) if any(
            fn.endswith(ext) for ext in validExt)]
        self.imgNames = sorted(self.imgNames)
        self.firstFrame = int(self.imgNames[0].split('.')[0])
        frs -= self.firstFrame
        fre -= self.firstFrame
        self.imgNames = self.imgNames[frs:fre]
        self.seqLen = len(self.imgNames)

        # Read ground-truth of this sequence
        if self.currentSeqSpecial:
            gtFilePath = os.path.join(
                self.datasetRoot, probe[0], 'groundtruth_rect.%s.txt' % probe[1])
        else:
            gtFilePath = os.path.join(
                self.datasetRoot, self.currentSeq, 'groundtruth_rect.txt')
        f = open(gtFilePath)
        seq_pattern = r'[\d]+'
        # origin gt format is [x, y, w, h]
        self.gts = [map(int, re.findall(seq_pattern, line))
                    for line in list(f)]
        gtrs, gtre = frs, fre
        if self.currentSeq == 'David':
            # Sequence 'David' is very special!
            gtrs -= 299
            gtre -= 299
        self.gts = self.gts[gtrs:gtre]

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
            if self.log:
                print('Succesfully load mat file for %s' % self.currentSeq)
            rawData = [label[0] for label in attrData]
            rawDataLen = len(rawData)
            if rawDataLen < self.seqLen:
                # If some frame have not been annotated, then use 0 to fill it.
                if self.log:
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
                if self.log:
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
    dataRoot = './data'
    window = MyApp(dataRoot)
    window.show()
    sys.exit(app.exec_())
