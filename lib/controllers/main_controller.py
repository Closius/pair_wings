from PySide6.QtCore import QObject, Slot, Qt

from lib.model.main_model import Model


class MainController(QObject):
    def __init__(self, model: Model):
        super().__init__()
        self._model = model

    def init_controller(self):
        self._model.init_data()
        if self._model.auto_connect:
            self._model.connect_to_stock()

    def close(self):
        self._model.backend_api.disconnect_stock()

    @Slot()
    def stockConnect_pushButton_clicked(self):
        if self._model.backend_api.is_stock_connected:
            self._model.disconnect_stock()
        else:
            self._model.connect_to_stock()

    @Slot(str)
    def stockNames_comboBox_currentTextChanged(self, stock_name):
        self._model.stock_name = stock_name

    @Slot(str)
    def accountNames_comboBox_currentTextChanged(self, account_name):
        self._model.account_name = account_name

    @Slot(Qt.CheckState)
    def stockAutoConnect_checkBox_checkStateChanged(self, check_state: Qt.CheckState):
        self._model.auto_connect = True if check_state is Qt.CheckState.Checked else False

    def pairs_listWidget_itemSelectionChanged(self, current_pairs: list):
        self._model.pairs = current_pairs

    @Slot(str)
    def interval_comboBox_currentTextChanged(self, interval):
        self._model.interval = interval
