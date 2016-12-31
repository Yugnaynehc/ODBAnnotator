import sys
import os
import itertools

from PyQt4 import QtCore
from PyQt4 import QtGui

# This is an example of how to make
# a grid of thumbnails

# PyQt 4.8
# Python 3.2


class RectWidget(QtGui.QGraphicsWidget):
    def __init__(self, thumb_path, parent = None):
        QtGui.QGraphicsWidget.__init__(self, parent)

        self.labelheight = 30
        self.bordersize = 1
        self.picdims = [100, 75]
        self.thumb_path = thumb_path
        self.pic = self.getpic(thumb_path)

        self._boundingRect = QtCore.QRect()
        
        self.setAcceptHoverEvents(True)


    def boundingRect(self):
        width = self.pic.rect().width() + self.bordersize * 2
        height = self.pic.rect().height() + self.labelheight + self.bordersize * 2
        
        thumb_widget_rect = QtCore.QRectF(0.0, 0.0, width, height)
        self._boundingRect = thumb_widget_rect

        return thumb_widget_rect


    def sizeHint(self, which, constraint = QtCore.QSizeF()):
        return self._boundingRect.size()


    def getpic(self, thumb_path):
        orpixmap = QtGui.QPixmap()
        orpixmap.load(self.thumb_path)

        return orpixmap    


    def paint(self, painter, option, widget):
        pen = QtGui.QPen()
        pen.setWidth(1)
        pen.setBrush(QtCore.Qt.black)
        painter.setPen(pen)
        
        # Draw border
        painter.drawRect(QtCore.QRect(0, 
                          0, 
                          self.pic.rect().width() + self.bordersize, 
                          self.pic.rect().height() + self.labelheight + self.bordersize))

        # Fill label
        painter.fillRect(QtCore.QRect(self.bordersize, 
                                      self.bordersize + self.pic.rect().height(), 
                                      self.pic.rect().width(), 
                                      self.labelheight), 
                                      QtCore.Qt.gray)

        # Draw image
        painter.drawPixmap(QtCore.QRect(self.bordersize, 
                                        self.bordersize, 
                                        self.pic.rect().width(), 
                                        self.pic.rect().height()), 
                           self.pic, 
                           self.pic.rect())

        # Draw text
        text_rect = QtCore.QRect(0, 
                                 self.pic.rect().y() + self.pic.rect().height(), 
                                 self.pic.rect().width(), 
                                 self.labelheight)
                                 
        painter.drawText(text_rect, QtCore.Qt.AlignCenter, 'hello there')
        
        
    def mousePressEvent(self, event):
        print('Widget Clicked')

    def mouseHoverEvent(self, event):
        print('Widget enter')

    def mouseReleaseEvent(self, event):
        print('Widget release')



class MainWindow(QtGui.QMainWindow):
    def __init__(self):
        QtGui.QMainWindow.__init__(self)
        
        self.appname = "Moving Pictures"
        self.setObjectName('MainWindow')
        self.resize(800, 700)

        self.setWindowTitle(self.appname)

        self.scene = QtGui.QGraphicsScene()
        self.view = QtGui.QGraphicsView(self.scene)
        self.panel = QtGui.QGraphicsWidget()
        self.scene.addItem(self.panel)
        
        layout = QtGui.QGraphicsGridLayout()
        layout.setContentsMargins(50, 100, 50, 50)
        self.panel.setLayout(layout)

        thumbs_path = 'f:/otb/benchmarkDatasets/Car1/img'
        thumbs = []
        
        for root, dirs, files in os.walk(thumbs_path):
            for fn in files:
                fullurl = os.path.join(root, fn)
                filebasename, ext = os.path.splitext(fn)
                thumbs.append(fullurl)
        
        COLUMNS=3
        ROWS=20

        i = 0
        for row, column in itertools.product(range(ROWS),range(COLUMNS)):
            print('Drawing', row, column)

            thumb_widget = RectWidget(thumbs[i])

            layout.addItem(thumb_widget, row, column, 1, 1)
            layout.setColumnSpacing (column, 20)
            layout.setRowSpacing(row, 15)
            i += 1

        self.setCentralWidget(self.view)
        self.view.show()


       
if __name__ == "__main__":

    app = QtGui.QApplication(sys.argv)
    app.setApplicationName("Pyqt Image gallery example")

    main = MainWindow()
    main.show()

    sys.exit(app.exec_())
