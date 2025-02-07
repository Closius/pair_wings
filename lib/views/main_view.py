from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Slot
from lib.views.ui_mainwindow import Ui_MainWindow

from lightweight_charts.widgets import QtChart

from lib.model.main_model import Model
from lib.controllers.main_controller import MainController


class MainView(QMainWindow):
    def __init__(self, model: Model, main_controller: MainController):
        super().__init__()

        self._model = model
        self._main_controller = main_controller
        self._ui = Ui_MainWindow()
        self._ui.setupUi(self)

        # chart = QtChart()
        # # Columns: time | open | high | low | close | volume
        # df = pd.read_csv('ohlcv.csv')
        # chart.set(df)
        # self._ui.tradingView_gridLayout.addWidget(chart.get_webview(), 0, 0, 1, 1)

        # connect widgets to controller
        self._ui.stockNames_comboBox.currentTextChanged.connect(
            self._main_controller.stockNames_comboBox_currentTextChanged
        )
        self._ui.accountNames_comboBox.currentTextChanged.connect(
            self._main_controller.accountNames_comboBox_currentTextChanged
        )
        self._ui.stockConnect_pushButton.clicked.connect(self._main_controller.stockConnect_pushButton_clicked)
        self._ui.stockDisconnect_pushButton.clicked.connect(self._main_controller.stockDisconnect)

        # # listen for model event signals
        # self._model.amount_changed.connect(self.on_amount_changed)

        # # set a default value
        # self._main_controller.change_amount(42)
        self.init_view()

    def init_view(self):

        self._ui.stockNames_comboBox.addItems(self._model.api_secrets["stocks"])
        self._ui.stockNames_comboBox.setCurrentText(self._model.stock_name)

        self._ui.accountNames_comboBox.addItems(self._model.api_secrets["stocks"][self._model.stock_name]["accounts"])
        self._ui.accountNames_comboBox.setCurrentText(self._model.account_name)

    # @Slot(str)
    # def on_amount_changed(self, value):
    #     self._ui.label_even_odd.setText(value)
