from PyQt5 import QtCore, QtWidgets, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QTreeWidgetItem

import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd

from pandasgui.functions import flatten_multiindex
import sys

class BaseDialog(QtWidgets.QDialog):
    def __init__(self, dataframes, parent=None):
        super().__init__(parent)

        self.dataframes = dataframes

        layout = QtWidgets.QVBoxLayout()
        self.setLayout(layout)

        # Create DataFrame picker dropdown
        self.dataframePicker = QtWidgets.QComboBox()
        for df_name in dataframes.keys():
            self.dataframePicker.addItem(df_name)
        self.dataframePicker.currentIndexChanged.connect(self.initColumnPicker)

        # Build column picker
        self.columnPicker = ColumnPicker([])
        self.initColumnPicker()

        # Add button
        btnFinish = QtWidgets.QPushButton("Plot")
        btnFinish.clicked.connect(self.finish)
        btnReset = QtWidgets.QPushButton("Reset")
        btnReset.clicked.connect(self.initColumnPicker)
        buttonLayout = QtWidgets.QHBoxLayout()
        spacer = QtWidgets.QSpacerItem(0, 0, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        buttonLayout.addSpacerItem(spacer)
        buttonLayout.addWidget(btnReset)
        buttonLayout.addWidget(btnFinish)

        # Add all to layout
        layout.addWidget(self.dataframePicker)
        layout.addWidget(self.columnPicker)
        layout.addLayout(buttonLayout)
        self.resize(640,480)

        self.show()

    def initColumnPicker(self):
        selected_dataframe = self.dataframePicker.itemText(self.dataframePicker.currentIndex())

        self.dataframe = self.dataframes[selected_dataframe]['dataframe'].copy()
        self.dataframe.columns = flatten_multiindex(self.dataframe.columns)
        column_names = self.dataframe.columns

        self.columnPicker.resetValues(column_names)

    def finish(self):
        dict = self.columnPicker.getDestinationItems()
        x = dict['X Variable'][0]
        y = dict['Y Variable'][0]
        try:
            c = dict['Color By'][0]
        except IndexError:
            c = None

        print(x,y,c)

        df = pd.read_csv('sample_data/pokemon.csv')
        sns.scatterplot(x,y,c,data=df)
        plt.show()

class ColumnPicker(QtWidgets.QWidget):
    def __init__(self, column_names, categories=None):
        super().__init__()

        # Set up widgets and layout
        layout = QtWidgets.QHBoxLayout()
        self.setLayout(layout)
        self.columnSource = SourceList(column_names)
        self.destinations = []
        self.destinations.append(DestTree("X Variable"))
        self.destinations.append(DestTree("Y Variable"))
        self.destinations.append(DestTree("Color By"))

        # Add buttons
        self.btnMoveRight = QtWidgets.QPushButton(">")
        self.btnMoveLeft = QtWidgets.QPushButton("<")
        # Make button vertical layout
        self.btnLayout = QtWidgets.QVBoxLayout()
        self.btnLayout.addWidget(self.btnMoveRight)
        self.btnLayout.addWidget(self.btnMoveLeft)
        # Connect buttons
        self.btnMoveRight.clicked.connect(self.moveSelectedRight)
        self.btnMoveLeft.clicked.connect(self.moveSelectedLeft)

        # Add column names to source list
        self.columnSource.resetItems()

        # List settings
        self.columnSource.setDragDropMode(QtWidgets.QListWidget.DragDrop)
        self.columnSource.setDefaultDropAction(QtCore.Qt.MoveAction)


        # Add items to layout
        self.destLayout = QtWidgets.QVBoxLayout()
        for dest in self.destinations:
            self.destLayout.addWidget(dest)
        layout.addWidget(self.columnSource)
        layout.addLayout(self.btnLayout)
        layout.addLayout(self.destLayout)


    def resetValues(self, column_names):

        # Clear list
        self.columnSource.columnNames = column_names
        self.columnSource.resetItems()

        # Clear tree
        for dest in self.destinations:
            dest.clear()

    def moveSelectedRight(self, index):
        sourceItems = self.columnSource.selectedItems()

        for item in sourceItems:
            self.addTreeItem(item.text())

            # Remove from list
            self.columnSource.removeItemWidget(item)

    # Takes a list of QTreeWidgetItem items and adds them to the QListWidget
    def moveSelectedLeft(self):

        items = self.columnDestination.selectedItems()


    def addTreeItem(self, label):
        # Add to tree
        destinationSection = self.columnDestination.selectedItems()[0]
        treeItem = QtWidgets.QTreeWidgetItem(destinationSection, [label])
        destinationSection.setExpanded(True)
        treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsDropEnabled)

        print(self.getDestinationItems())

    # Takes a list of QTreeWidgetItem items and removes them from the tree
    def removeTreeItems(self, items):
        for item in items:
            item.parent().removeChild(item)

    def addListItem(self, label):
        pass

    def removeListItem(self, label):
        pass

    # Return a dict of the items in the destination tree
    def getDestinationItems(self):
        items = {}

        for dest in self.destinations:
            items[dest.title] = dest.getItems()
        return items


class DestTree(QtWidgets.QTreeWidget):
    def __init__(self, title='Variable', parent=None):
        super().__init__(parent)
        self.title = title

        # Tree settings
        self.setHeaderLabels([title])
        # self.columnDestination.setSelectionBehavior(self.columnDestination.SelectRows)

        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)

        self.doubleClicked.connect(self.removeSelectedItems)

    def removeSelectedItems(self):
        for item in self.selectedItems():
            self.invisibleRootItem().removeChild(item)

    def dropEvent(self, event):
        QtWidgets.QTreeWidget.dropEvent(self, event)

        # Loop over tree items
        for i in range(self.topLevelItemCount()):
            # Don't allow dropping items inside other items
            treeItem = self.topLevelItem(i)
            treeItem.setFlags(treeItem.flags() & ~QtCore.Qt.ItemIsDropEnabled)

            # Set 2nd column
            treeItem.setData(1,Qt.DisplayRole,"test")

        if type(event.source())==SourceList:
            event.source().resetItems()

        print(self.getItems())

    # Return a list of strings of the items in the tree
    def getItems(self):
        items = []
        for i in range(self.topLevelItemCount()):
            treeItem = self.topLevelItem(i)
            items.append(treeItem.text(0))
        return items

class SourceList(QtWidgets.QListWidget):
    def __init__(self, columnNames=[], parent=None):
        super().__init__(parent)
        self.columnNames = columnNames

        self.resetItems()

        # Settings
        self.setDragDropMode(self.DragDrop)
        self.setSelectionMode(self.ExtendedSelection)
        self.setDefaultDropAction(QtCore.Qt.MoveAction)
        self.setAcceptDrops(True)

    def dropEvent(self, event):
        print('asf')
        QtWidgets.QListWidget.dropEvent(self, event)

        self.resetItems()

    def resetItems(self):
        self.clear()
        for name in self.columnNames:
            self.addItem(name)

if __name__=='__main__':

    dataframes = {}

    pokemon = pd.read_csv('sample_data/pokemon.csv')
    dataframes['pokemon'] = {}
    dataframes['pokemon']['dataframe'] = pokemon

    sample = pd.read_csv('sample_data/sample.csv')
    dataframes['sample'] = {}
    dataframes['sample']['dataframe'] = sample

    ## PyQt
    app = QtWidgets.QApplication(sys.argv)

    win = BaseDialog(dataframes)
    # win = Tree()
    win.show()
    app.exec_()
