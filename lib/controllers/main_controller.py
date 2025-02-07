from PySide6.QtCore import QObject, Slot

from lib.model.main_model import Model


class MainController(QObject):
    def __init__(self, model: Model):
        super().__init__()
        self._model = model


    @Slot(str)
    def stockNames_comboBox_currentTextChanged(self, stock_name):
        self._model.stock_name = stock_name

    @Slot(str)
    def accountNames_comboBox_currentTextChanged(self, account_name):
        self._model.account_name = account_name

    @Slot()
    def stockConnect_pushButton_clicked(self):
        self._model.connect_to_stock()

    @Slot()
    def stockDisconnect(self):
        self._model.disconnect_stock()