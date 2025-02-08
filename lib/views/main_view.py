from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Slot, QTimer, Qt
from PySide6.QtGui import QIcon
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
        # set init values in View. Before the widgets connections are set
        self.init_view()

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
        self._ui.stockAutoConnect_checkBox.checkStateChanged.connect(
            self._main_controller.stockAutoConnect_checkBox_checkStateChanged
        )

        # listen for model event signals
        self._model.stock_connected.connect(self.on_stock_connected)
        self._model.stock_disconnected.connect(self.on_stock_disconnected)

        self._check_stock_connection_status_timer = QTimer(self)
        self._check_stock_connection_status_timer.setInterval(1000)
        self._check_stock_connection_status_timer.timeout.connect(self.check_stock_connection_status)

        # init Controller once all widget connections in View are set
        self._main_controller.init_controller()

    def init_view(self):
        self.statusBar().showMessage(f"Disconnected")
        self._ui.stockNames_comboBox.addItems(self._model.api_secrets["stocks"])
        self._ui.stockNames_comboBox.setCurrentText(self._model.stock_name)
        self._ui.accountNames_comboBox.addItems(self._model.api_secrets["stocks"][self._model.stock_name]["accounts"])
        self._ui.accountNames_comboBox.setCurrentText(self._model.account_name)
        if self._model.auto_connect:
            self._ui.stockAutoConnect_checkBox.setCheckState(Qt.CheckState.Checked)
        else:
            self._ui.stockAutoConnect_checkBox.setCheckState(Qt.CheckState.Unchecked)

    @Slot()
    def check_stock_connection_status(self):
        if self._model.backend_api.is_stock_connected:
            self._ui.stock_status_label.setText("Connected :)")
            self._ui.stockConnect_pushButton.setText("Disconnect")
            self.statusBar().showMessage(f"Connected | {self._model.stock_name} | {self._model.account_name}")
        else:
            self._ui.stock_status_label.setText("Disconnected :(")
            self._ui.stockConnect_pushButton.setText("Connect")
            self.statusBar().showMessage(f"Disconnected")
            self._check_stock_connection_status_timer.stop()

    @Slot()
    def on_stock_connected(self):
        all_pairs = self._model.backend_api.get_all_pairs()
        self._ui.pairs_listWidget.addItems(all_pairs)
        self._ui.pairs_listWidget.setCurrentRow(0)
        self._ui.stockNames_comboBox.setDisabled(True)
        self._ui.accountNames_comboBox.setDisabled(True)
        self._check_stock_connection_status_timer.start()

    @Slot()
    def on_stock_disconnected(self):
        self._ui.pairs_listWidget.clear()
        self._ui.stockNames_comboBox.setEnabled(True)
        self._ui.accountNames_comboBox.setEnabled(True)

    def closeEvent(self, event):
        self._model.backend_api.disconnect_stock()
