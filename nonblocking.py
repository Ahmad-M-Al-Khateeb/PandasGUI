import time
import multiprocess

from PyQt5 import QtWidgets
class MainWindow(QtWidgets.QTextEdit):
    def __init__(self):
        # call super class constructor
        super(MainWindow, self).__init__()
        self.show()

def start_gui(*args, **kwargs):
    import sys
    from PyQt5 import QtWidgets
    import pandasgui.pdgui

    # Set up QApplication
    app = QtWidgets.QApplication.instance()
    if not app:
        app = QtWidgets.QApplication(sys.argv)

    # Make GUi
    win = pandasgui.pdgui.PandasGUI(*args, **kwargs, app=app)

    app.exec_()

def show(*args, **kwargs):
    thread = multiprocess.Process(target=start_gui, args=args, kwargs=kwargs)
    thread.start()

if __name__ == '__main__':
    import pandas as pd
    pokemon = pd.read_csv('pokemon.csv')

    sample = pd.read_csv('sample.csv')

    tuples = [('A', 'one', 'x'), ('A', 'one', 'y'), ('A', 'two', 'x'), ('A', 'two', 'y'),
              ('B', 'one', 'x'), ('B', 'one', 'y'), ('B', 'two', 'x'), ('B', 'two', 'y')]
    index = pd.MultiIndex.from_tuples(tuples, names=['first', 'second', 'third'])
    multidf = pd.DataFrame(pd.np.random.randn(8, 8), index=index[:8], columns=index[:8])

    show(sample)
