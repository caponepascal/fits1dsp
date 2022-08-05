__author__ = 'pascal capone'

'''Required packages'''
# General:
import numpy as np
# PyQt5:
from PyQt5 import QtGui, QtCore, QtWidgets

'''Detachable Tab'''
class DetachableTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent = None):
        QtWidgets.QTabWidget.__init__(self, parent)
        
        self.move(640, 239)
        self.resize(631, 411)
        
        self.tabBar = TabBar(self)
        self.setTabBar(self.tabBar)
        self.tabBar.on_detach_tab_Signal.connect(self.detach_tab)
        self.detached_tabs = {} #Use a dictionary instead of list ot access the detached tabs via their name

    #@QtCore.pyqtSlot(int, QtCore.QPoint)
    def detach_tab(self, index, point):
        widget = self.widget(index)
        name = self.tabText(index)
        
        detached_tab = DetachedTab(widget, index, name)
        detached_tab.move(point)
        detached_tab.on_close_Signal.connect(self.attach_tab)
        detached_tab.show()
        self.detached_tabs[name] = detached_tab
        
        widget_sub = SubstituteTab(name)
        self.insertTab(index, widget_sub, name)
        self.setCurrentIndex(index)

    #QtCore.pyqtpyqtSlot(QtGui.QWidget, QtCore.QString)
    def attach_tab(self, widget, name):
        widget.setParent(self)
        index = np.where(name == np.array([self.tabText(i) for i in range(self.count())]))[0][0]
        self.insertTab(index, widget, name)
        self.removeTab(index + 1)
        del self.detached_tabs[name]
        self.setCurrentIndex(index)

    def close_detached_tabs(self):
        for item in [self.detached_tabs[key] for key in self.detached_tabs]:
            item.close()

class DetachedTab(QtWidgets.QMainWindow):
    on_close_Signal = QtCore.pyqtSignal(QtWidgets.QWidget, str, int)
    def __init__(self, widget, index, name, parent = None):
        QtWidgets.QMainWindow.__init__(self, parent)
        
        self.resize(631, 391)
        self.widget = widget
        self.index = index
        self.name = name
        self.setObjectName("detached_tab_plot_" + str(index))
        self.setWindowTitle("Plot - " + self.name)
        self.setCentralWidget(self.widget)
        self.widget.show()

    def closeEvent(self, event):
        self.on_close_Signal.emit(self.widget, self.name, self.index)
        
class SubstituteTab(QtWidgets.QTabWidget):
    def __init__(self, name, parent = None):
        QtWidgets.QTabWidget.__init__(self, parent)
        
        #self.resize(631, 391)
        self.layout = QtWidgets.QVBoxLayout()
        self.label = QtWidgets.QLabel()
        self.label.setAlignment(QtCore.Qt.AlignCenter)
        self.label.setText("This tab is currently displayed in the window \"Plot - " + name +"\"")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)

class TabBar(QtWidgets.QTabBar):
    on_detach_tab_Signal = QtCore.pyqtSignal(int, QtCore.QPoint)
    def __init__(self, parent = None):
        QtWidgets.QTabBar.__init__(self, parent)
        
        self.setElideMode(QtCore.Qt.ElideRight)
        self.setUsesScrollButtons(True)
        self.setDocumentMode(True)
        self.setMovable(False)
        self.setSelectionBehaviorOnRemove(QtWidgets.QTabBar.SelectLeftTab)

        self.drag_old_position = QtCore.QPoint()
        self.drag_new_position = QtCore.QPoint()
        self.mouseCursor = QtGui.QCursor()
        self.dragInitiated = False
    
    # Detach via mouse double click
    def mouseDoubleClickEvent(self, event):
        event.accept()
        self.on_detach_tab_Signal.emit(self.tabAt(event.pos()), self.mouseCursor.pos())
    
    # Detach via mouse click and drag
    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.LeftButton:
            self.drag_old_position = event.pos()
            
        self.drag_new_position.setX(0)
        self.drag_new_position.setY(0)
        self.dragInitiated = False

        QtWidgets.QTabBar.mousePressEvent(self, event)

    def mouseMoveEvent(self, event):
        if not self.drag_old_position.isNull() and ((event.pos() - self.drag_old_position).manhattanLength() > QtWidgets.QApplication.startDragDistance()*2):
            self.dragInitiated = True

        if ((event.buttons() & QtCore.Qt.LeftButton)) and self.dragInitiated:
            mouseMoveEvent_end = QtGui.QMouseEvent(QtCore.QEvent.MouseMove, event.pos(), QtCore.Qt.NoButton, QtCore.Qt.NoButton, QtCore.Qt.NoModifier)
            QtWidgets.QTabBar.mouseMoveEvent(self, mouseMoveEvent_end)

            drag = QtGui.QDrag(self)
            mimeData = QtCore.QMimeData()
            mimeData.setData("action", QtCore.QByteArray(b"application/tab-detach"))
            drag.setMimeData(mimeData)
            
            # Create the appearance of dragging the tab content
            pixmap = self.parent().widget(self.tabAt(self.drag_old_position)).grab()
            targetPixmap = QtGui.QPixmap(pixmap.size())
            targetPixmap.fill(QtCore.Qt.transparent)
            painter = QtGui.QPainter(targetPixmap)
            painter.setOpacity(0.85)
            painter.drawPixmap(0, 0, pixmap)
            painter.end()
            drag.setPixmap(targetPixmap)

            # Initiate the drag outside the tab bar
            dropAction = drag.exec_( QtCore.Qt.CopyAction | QtCore.Qt.MoveAction, QtCore.Qt.CopyAction)
            if self.drag_new_position.x() != 0 and self.drag_new_position.y() != 0: #For Linux: drag.exec_() does not return MoveAction and must be set manually
                dropAction = QtCore.Qt.MoveAction
            if dropAction == QtCore.Qt.IgnoreAction:
                event.accept()
                self.on_detach_tab_Signal.emit(self.tabAt(self.drag_old_position), self.mouseCursor.pos())
        else:
            QtWidgets.QTabBar.mouseMoveEvent(self, event)

    def dropEvent(self, event):
        self.drag_new_position = event.pos()
        QtWidgets.QTabBar.dropEvent(self, event)
    