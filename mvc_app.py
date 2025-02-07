import sys

from PySide6.QtWidgets import QApplication

from lib.model.main_model import Model
from lib.controllers.main_controller import MainController
from lib.views.main_view import MainView

# Important:
# You need to run the following command to convert .ui to .py files:
# python\Scripts\pyside6-uic.exe resources\ui_mainwindow.ui -o views\ui_mainwindow.py

class App(QApplication):
    def __init__(self, sys_argv):
        super(App, self).__init__(sys_argv)
        self.model = Model()
        self.main_controller = MainController(self.model)
        self.main_view = MainView(self.model, self.main_controller)
        self.main_view.show()


if __name__ == '__main__':
    app = App(sys.argv)
    sys.exit(app.exec())