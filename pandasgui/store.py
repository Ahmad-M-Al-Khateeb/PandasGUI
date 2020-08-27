from dataclasses import dataclass, field, asdict
from typing import Dict, List, Union
import pandas as pd
from pandas import DataFrame
from PyQt5 import QtCore, QtGui, QtWidgets, sip
from PyQt5.QtCore import Qt
import traceback


@dataclass
class Settings:
    editable: bool = True  # Are table cells editable
    block: bool = False


@dataclass
class Filter:
    expr: str
    enabled: bool
    failed: bool


class PandasGuiDataFrame:
    def __init__(self, df: DataFrame, name: str = 'Untitled'):
        super().__init__()

        self.dataframe_unfiltered = df
        self.dataframe = df
        self.name = name
        self.initial_index = df.index.copy()

        self.dataframe_explorer: Union["DataFrameExplorer", None] = None
        self.dataframe_viewer: Union["DataFrameViewer", None] = None
        self.filter_viewer: Union["FilterViewer", None] = None

        self.column_sorted: Union[int, None] = None
        self.index_sorted: Union[int, None] = None
        self.sort_is_descending: Union[bool, None] = None

        self.filters: List[Filter] = []

    def update(self):
        models = []
        if self.dataframe_viewer is not None:
            models += [self.dataframe_viewer.dataView.model(),
                       self.dataframe_viewer.columnHeader.model(),
                       self.dataframe_viewer.indexHeader.model(),
                       self.dataframe_viewer.columnHeaderNames.model(),
                       self.dataframe_viewer.indexHeaderNames.model(),
                       ]

        if self.filter_viewer is not None:
            models += [self.filter_viewer.list_model,
                       ]

        for model in models:
            model.beginResetModel()
            model.endResetModel()

    def update_inplace(self, df):
        self.dataframe._update_inplace(df)

    def edit_data(self, row, col, value):
        self.dataframe_unfiltered.iloc[self.dataframe.index[row], col] = value
        self.apply_filters()
        self.update()

    def sort_by(self, ix: int, is_index=False):
        if is_index:

            # Clicked an unsorted index
            if ix != self.index_sorted:
                self.dataframe.sort_index(level=ix, ascending=True, kind="mergesort", inplace=True)

                self.index_sorted = ix
                self.sort_is_descending = False

            # Clicked a sorted index level
            elif ix == self.index_sorted and not self.sort_is_descending:
                self.dataframe.sort_index(level=ix, ascending=False, kind="mergesort", inplace=True)

                self.index_sorted = ix
                self.sort_is_descending = True

            # Clicked a reverse sorted index level
            elif ix == self.index_sorted and self.sort_is_descending:
                temp = self.dataframe.reindex(self.initial_index)
                self.update_inplace(temp)

                self.index_sorted = None
                self.sort_is_descending = None

            self.column_sorted = None

        else:
            col_name = self.dataframe.columns[ix]

            # Clicked an unsorted column
            if ix != self.column_sorted:
                self.dataframe.sort_values(col_name, ascending=True, kind="mergesort", inplace=True)

                self.column_sorted = ix
                self.sort_is_descending = False

            # Clicked a sorted column
            elif ix == self.column_sorted and not self.sort_is_descending:
                self.dataframe.sort_values(col_name, ascending=False, kind="mergesort", inplace=True)

                self.column_sorted = ix
                self.sort_is_descending = True

            # Clicked a reverse sorted column
            elif ix == self.column_sorted and self.sort_is_descending:
                temp = self.dataframe.reindex(self.initial_index)
                self.update_inplace(temp)

                self.column_sorted = None
                self.sort_is_descending = None

            self.index_sorted = None

        self.update()

    def add_filter(self, expr: str, enabled=True):
        filt = Filter(expr=expr, enabled=enabled, failed=False)
        self.filters.append(filt)
        self.apply_filters()

    def remove_filter(self, index: int):
        self.filters.pop(index)
        self.apply_filters()

    def edit_filter(self, index: int, expr: str):
        filt = self.filters[index]
        filt.expr = expr
        filt.failed = False
        self.apply_filters()

    def toggle_filter(self, index: int):
        self.filters[index].enabled = not self.filters[index].enabled
        self.apply_filters()

    def apply_filters(self):

        df = self.dataframe_unfiltered
        for ix, filt in enumerate(self.filters):
            if filt.enabled and not filt.failed:
                try:
                    df = df.query(filt.expr)
                except Exception as e:
                    self.filters[ix].failed = True
                    traceback.print_exc()
        self.dataframe = df
        self.update()

    @staticmethod
    def cast(x: Union["PandasGuiDataFrame", pd.DataFrame, pd.Series]):
        if type(x) == PandasGuiDataFrame:
            return x
        if type(x) == pd.DataFrame:
            return PandasGuiDataFrame(x)
        elif type(x) == pd.Series:
            return PandasGuiDataFrame(pd.DataFrame(x))
        else:
            raise TypeError


@dataclass
class Store:
    settings: Settings = Settings()
    data: List[PandasGuiDataFrame] = field(default_factory=list)

    def get_dataframe(self, name):
        return next((x for x in self.data if x.name == name), None)

    def to_dict(self):
        import json
        return json.loads(json.dumps(self, default=lambda o: o.__dict__))
