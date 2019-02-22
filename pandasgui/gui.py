import inspect
import traceback
import sys
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from PyQt5 import QtCore, QtGui, QtWidgets
from pandasgui.dataframe_viewer import DataFrameView

# This fixes lack of stack trace on PyQt exceptions
try:
    import pyqt_fix
except:
    pass

class PandasGUI(QtWidgets.QMainWindow):

    def __init__(self, nonblocking=False, **kwargs):
        """
        Args:
            *args (): Tuple of DataFrame objects
            **kwargs (): Dict of (key, value) pairs of
                         {'DataFrame name': DataFrame object}
        """

        print("Opening PandasGUI...")
        super().__init__()
        self.app = QtWidgets.QApplication.instance()

        # self.df_dicts is a dictionary of all dataframes in the GUI.
        # {dataframe name: objects}

        # The objects are their own dictionary of:
        # {'dataframe': DataFrame object
        # 'view': DataFrameViewer object
        # 'model': DataFrameModel object
        # 'tab_widget': QTabWidget object}
        # 'display_df': DataFrame object
        # This is a truncated version of the dataframe for displaying
        self.df_dicts = {}

        # setupUI() class variable initialization.
        self.main_layout = None
        self.tabs_stacked_widget = None
        self.df_shown = None
        self.splitter = None
        self.main_widget = None

        # Nav bar class variable initialization.
        self.nav_view = None

        # Tab widget class variable initialization.
        self.headers_highlighted = None

        # Adds keyword arguments to df_dict.
        for i, (df_name, df_object) in enumerate(kwargs.items()):

            if type(df_object) == pd.core.series.Series:
                df_object = df_object.to_frame()
                print(f'"{df_name}" was automatically converted from Series to DataFrame')
            self.df_dicts[df_name] = {}
            self.df_dicts[df_name]['dataframe'] = df_object

        # Generates the user interface.
        self.setupUI()

        # Window settings
        if nonblocking:
            self.setWindowTitle('PandasGUI (nonblocking)')
        else:
            self.setWindowTitle('PandasGUI')

        self.app.setWindowIcon(QtGui.QIcon('icon.png'))

        # Create main Widget
        self.show()

        # Center window on screen
        screen = QtWidgets.QDesktopWidget().screenGeometry()
        size = self.geometry()
        self.move(int((screen.width() - size.width()) / 2), int((screen.height() - size.height()) / 2))

    def setupUI(self):
        """
        Creates and adds all widgets to main_layout.
        """

        self.main_layout = QtWidgets.QHBoxLayout()

        # Make the menu bar
        self.make_menu_bar()

        # Make the navigation bar
        self.make_nav()

        # Make the QTabWidgets for each DataFrame
        self.tabs_stacked_widget = QtWidgets.QStackedWidget()

        # Iterate over all dataframe names and make the tab_widgets
        for df_name in self.df_dicts.keys():
            tab_widget = self.make_tab_widget(df_name)
            self.df_dicts[df_name]['tab_widget'] = tab_widget
            self.tabs_stacked_widget.addWidget(tab_widget)

        initial_df_name = list(self.df_dicts.keys())[0]
        initial_tab_widget = self.df_dicts[initial_df_name]['tab_widget']
        self.df_shown = self.df_dicts[initial_df_name]['dataframe']

        self.tabs_stacked_widget.setCurrentWidget(initial_tab_widget)

        # Adds navigation section to splitter.
        self.splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        self.splitter.addWidget(self.nav_view)
        self.splitter.addWidget(self.tabs_stacked_widget)

        # Combines navigation section and main section.
        self.main_layout.addWidget(self.splitter)
        self.main_widget = QtWidgets.QWidget()
        self.main_widget.setLayout(self.main_layout)

        self.setCentralWidget(self.main_widget)

    ####################
    # Menu bar functions

    def make_menu_bar(self):

        # Create a menu for setting the GUI style.
        # Uses radio-style buttons in a QActionGroup.
        menubar = self.menuBar()
        styleMenu = menubar.addMenu('&Set Style')
        styleGroup = QtWidgets.QActionGroup(styleMenu, exclusive=True)

        # Iterate over all GUI Styles that exist for the user's system
        for style in QtWidgets.QStyleFactory.keys():
            styleAction = QtWidgets.QAction(f'&{style}', self, checkable=True)
            styleAction.triggered.connect(lambda state,
                                                 style=style: self.set_style(style))
            styleGroup.addAction(styleAction)
            styleMenu.addAction(styleAction)
        # Set the default style
        styleAction.trigger()

        # Creates a chart menu.
        chartMenu = menubar.addMenu('&Plot Charts')
        # chartGroup = QtWidgets.QActionGroup(chartMenu)

        # Creates a reshaping menu.
        chartMenu = menubar.addMenu('&Reshape Data')

        pivotDialogAction = QtWidgets.QAction('&Scatter Dialog', self)
        pivotDialogAction.triggered.connect(self.pivot_dialog)
        chartMenu.addAction(pivotDialogAction)

    def set_style(self, style):
        print("Setting style to", style)
        self.app.setStyle(style)

    ####################
    # Tab widget functions

    def make_tab_widget(self, df_name):
        """Take a DataFrame and creates tabs for it in self.tab_widget."""

        # Creates the tabs
        dataframe_tab = self.make_dataframe_tab(df_name)
        statistics_tab = self.make_statistics_tab(df_name)
        chart_tab = self.make_tab_charts()

        tab_widget = QtWidgets.QTabWidget()
        # Adds them to the tab_view
        tab_widget.addTab(dataframe_tab, "Dataframe")
        tab_widget.addTab(statistics_tab, "Statistics")
        tab_widget.addTab(chart_tab, "Charts")

        return tab_widget

    def make_dataframe_tab(self, df_name):

        df = self.df_dicts[df_name]['dataframe']

        # Create a smaller version to display so it doesn't lag
        df = df.head(1000)
        self.df_dicts[df_name]['display_df'] = df

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        view = DataFrameView(df)

        layout.addWidget(view)
        tab.setLayout(layout)
        return tab

    def make_statistics_tab(self, df_name):

        df = self.df_dicts[df_name]['dataframe']

        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        tab_df = df.describe(include='all').T
        tab_df.insert(loc=0, column='Type', value=df.dtypes)

        view = DataFrameView(tab_df)

        layout.addWidget(view)

        tab.setLayout(layout)

        return tab

    def make_tab_charts(self):
        tab = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout()

        button = QtWidgets.QPushButton("Print DF")
        # button.clicked.connect(self.printdf)

        layout.addWidget(button)
        tab.setLayout(layout)
        return tab

    ####################
    # Nav bar functions

    def make_nav(self):
        # Create the navigation pane
        df_names = list(self.df_dicts.keys())
        self.nav_view = QtWidgets.QTreeView()

        # Creates the headers.
        model = QtGui.QStandardItemModel(0, 2, self)
        model.setHeaderData(0, QtCore.Qt.Horizontal, 'Name')
        model.setHeaderData(1, QtCore.Qt.Horizontal, 'Shape')
        root_node = model.invisibleRootItem()

        # Adds a dataframe to the navigation sidebar
        main_nav_branch = QtGui.QStandardItem('Master')
        for df_name in df_names:
            # Calculate and format the shape of the DataFrame
            shape = self.df_dicts[df_name]['dataframe'].shape
            shape = str(shape[0]) + ' X ' + str(shape[1])

            df_name_label = QtGui.QStandardItem(df_name)
            shape_label = QtGui.QStandardItem(shape)

            # Disables dropping dataframes on other dataframes in nav pane.
            df_name_label.setFlags(df_name_label.flags() &
                                   ~QtCore.Qt.ItemIsDropEnabled)
            shape_label.setFlags(shape_label.flags() &
                                 ~QtCore.Qt.ItemIsDropEnabled)

            # Disables editing the names of the dataframes.
            df_name_label.setEditable(False)
            shape_label.setEditable(False)

            main_nav_branch.appendRow([df_name_label, shape_label])

        root_node.appendRow([main_nav_branch, None])
        self.nav_view.setModel(model)
        self.nav_view.expandAll()
        self.nav_view.clicked.connect(self.select_dataframe)

    def select_dataframe(self, location_clicked):
        """
        Examines navbar row pressed by user
        and then changes the dataframe shown.

        Args:
            location_clicked: Automatically passed during clicked signal.
                              Instance of QtCore.ModelIndex.
                              Provides information on the location clicked,
                              accessible with methods such as row() or data().
        """

        df_parent_folder_index = location_clicked.parent().row()
        df_clicked_row_index = location_clicked.row()

        # Gets name of dataframe by using index of the row clicked.
        nav_pane = self.nav_view.model()
        df_parent_folder_name = nav_pane.index(df_parent_folder_index, 0)
        df_name = df_parent_folder_name.child(df_clicked_row_index, 0).data()
        df_properties = self.df_dicts.get(df_name)

        # If the dataframe exists, change the tab widget shown.
        if df_properties is not None:
            self.df_shown = df_properties['dataframe']
            tab_widget = df_properties['tab_widget']
            self.tabs_stacked_widget.setCurrentWidget(tab_widget)

    ####################
    # Reshape functions.

    def pivot_dialog(self):
        from pandasgui.chart_dialogs import scatterDialog
        win = scatterDialog(self.df_dicts, parent=self)


def show(*args, nonblocking=False, **kwargs):
    # Get the variable names in the scope show() was called from
    callers_local_vars = inspect.currentframe().f_back.f_locals.items()

    # Make a dictionary of the DataFrames from the position args and get their variable names using inspect
    dataframes = {}
    for i, df_object in enumerate(args):
        df_name = 'untitled' + str(i + 1)

        for var_name, var_val in callers_local_vars:
            if var_val is df_object:
                df_name = var_name

        dataframes[df_name] = df_object

    # Add the dictionary of positional args to the kwargs
    if (any([key in kwargs.keys() for key in dataframes.keys()])):
        print("Warning! Duplicate DataFrame names were given, duplicates were ignored.")
    kwargs = {**kwargs, **dataframes}

    # Run the GUI in a separate process
    if nonblocking:
        print("Nonblocking mode")
        from pandasgui.nonblocking import show_nonblocking
        show_nonblocking(**kwargs)
        return

    # Creeate the application and PandasGUI window
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)
    win = PandasGUI(**kwargs)
    app.exec_()


if __name__ == '__main__':
    pokemon = pd.read_csv('sample_data/pokemon.csv')
    sample = pd.read_csv('sample_data/sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])
    # big = pd.read_csv('sample_data/1500000 Sales Records.csv')
    # show(big)
    show(pokemon, sample, multidf)
    # show(sample)
    # show(sample, multidf=multidf, pokemon=pokemon)
