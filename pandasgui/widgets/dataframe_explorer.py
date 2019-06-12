from PyQt5 import QtGui, QtCore, QtWidgets
from PyQt5.QtCore import QAbstractItemModel, QModelIndex, QSize, QRect, Qt, QPoint, QItemSelectionModel
from PyQt5.QtGui import QPainter, QFont, QFontMetrics, QPalette, QBrush, QColor, QTransform
from PyQt5.QtWidgets import QSizePolicy
import pandas as pd
import numpy as np
import datetime
import sys
import matplotlib.pyplot as plt
import seaborn as sns

sns.set()

from pandasgui.dataframe_viewer import DataFrameViewer
from pandasgui.extended_combobox import ExtendedComboBox
from pandasgui.image_viewer import FigureViewer

try:
    import pyqt_fix
except:
    pass


class DataFrameExplorer(QtWidgets.QTabWidget):
    """
    This is a container for the DataTableView and two DataFrameHeaderViews in a QGridLayout
    """

    def __init__(self, df):
        super().__init__()

        df = df.copy()
        self.df = df

        # Creates the tabs
        dataframe_tab = DataFrameViewer(df)
        statistics_tab = self.make_statistics_tab(df)

        # Adds them to the tab_view
        self.addTab(dataframe_tab, "Dataframe")
        self.addTab(statistics_tab, "Statistics")

        if not (type(df.index) == pd.MultiIndex or type(df.columns) == pd.MultiIndex):
            histogram_tab = self.make_histogram_tab(df)
            self.addTab(histogram_tab, "Histogram")

        self.dataframe_viewer = DataFrameViewer(df)

    def make_statistics_tab(self, df):
        stats_df = pd.DataFrame({
            'Type': df.dtypes.replace('object', 'string'),
            'Count': df.count(numeric_only=True).astype(pd.Int64Dtype()),
            'Mean': df.mean(numeric_only=True),
            'StdDev': df.std(numeric_only=True),
            'Min': df.min(numeric_only=True),
            'Max': df.max(numeric_only=True),
        })
        w = DataFrameViewer(stats_df)
        w.setAutoFillBackground(True)
        return w

    def make_histogram_tab(self, df):
        return self.HistogramTab(df)

    class HistogramTab(QtWidgets.QWidget):
        def __init__(self, df):
            super().__init__()

            self.df = df.copy()

            self.picker = QtWidgets.QComboBox()
            self.picker.addItems(df.columns)
            self.picker.currentIndexChanged.connect(self.update_plot)
            self.figure_viewer = FigureViewer()

            self.layout = QtWidgets.QVBoxLayout()

            self.layout.addWidget(self.picker)
            self.layout.addWidget(self.figure_viewer)

            self.setLayout(self.layout)
            self.update_plot()

        def update_plot(self):
            col = self.picker.currentText()

            fig = plt.figure()

            arr = self.df[col].dropna()
            if self.df[col].dtype.name in ['object', 'bool']:
                ax = sns.countplot(y=arr, color='grey', order=arr.value_counts().iloc[:10].index)

            else:
                ax = sns.distplot(arr, color='black', hist_kws=dict(color='grey', alpha=1))

            self.figure_viewer.setFigure(ax.figure)


# Examples
if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)

    # Sample data sets
    import seaborn as sns
    iris = sns.load_dataset('iris')
    flights = sns.load_dataset('flights')
    multi = flights.set_index(['year', 'month']).unstack()  # MultiIndex example

    # Create and show widget
    view = DataFrameViewer(iris)
    view.show()

    dfe = DataFrameExplorer(pokemon)
    dfe.show()
    sys.exit(app.exec_())

plt.figure().autofmt_xdate
