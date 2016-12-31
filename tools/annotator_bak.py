# coding: utf-8
# python2

from __future__ import print_function
import sys
import os.path
from PyQt4 import QtCore, QtGui, uic
from widgets import ImageContainer, ImageWidget
from scipy.io import loadmat


qtCreatorFile = 'GUI.ui'
uiMainWindow, QtBaseClass = uic.loadUiType(qtCreatorFile)
file_type = ['jpg', 'jpeg', 'tif', 'bmp', 'gif']


class MyApp(QtGui.QMainWindow, uiMainWindow):
    def __init__(self, data_root):
        QtGui.QMainWindow.__init__(self)
        uiMainWindow.__init__(self)
        self.setupUi(self)
        self.prevSeq.clicked.connect(self.haha)
        self.datasetRoot = os.path.join(dataRoot, 'benchmarkDatasets')

        # Init sequence list
        self.initSeqList()

        # Init image container
        self.imageContainer = ImageContainer(self.mainLayout)
        self.mainLayout.addWidget(self.imageContainer)
        self.mainLayout.setStretch(1, 6)

    def initSeqList(self):
        self.seq_list = os.listdir(self.datasetRoot)
        for seq in self.seq_list:
            item = QtGui.QListWidgetItem(seq)
            self.seqList.addItem(item)
        self.seqList.itemClicked.connect(self.showSeq)

    def haha(self):
        print(self.datasetRoot)

    def showSeq(self, item):
        self.imageContainer.clearAll()
        seqName = str(item.text())
        seqImgDir = os.path.join(self.datasetRoot, seqName, 'img')
        imgNames = os.listdir(seqImgDir)
        for imgName in imgNames[:20]:
            if imgName.split('.')[-1] in file_type:
                print(imgName)
                try:
                    widget = ImageWidget()
                    widget.displayText = imgName
                    widget.setThumb(os.path.join(seqImgDir, imgName))
                    self.imageContainer.addWidget(widget)
                except Exception, e:
                    print(e)
                    pass
        self.imageContainer.layout()

    def keyPressEvent(self, e):
        if e.key() == QtCore.Qt.Key_Escape:
            self.close()


if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    dataRoot = 'f:\otb'
    window = MyApp(dataRoot)
    window.show()
    sys.exit(app.exec_())
