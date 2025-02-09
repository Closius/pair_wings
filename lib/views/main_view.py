import pandas as pd

from PySide6.QtWidgets import QMainWindow
from PySide6.QtCore import Slot, Qt
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

        # connect widgets to controller (direct or indirect)
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
        self._ui.restore_begin_end_checkBox.checkStateChanged.connect(
            self._main_controller.restore_begin_end_checkBox_checkStateChanged
        )
        self._ui.pairs_listWidget.itemSelectionChanged.connect(self.on_pairs_listWidget_itemSelectionChanged)
        self._ui.interval_comboBox.currentTextChanged.connect(
            self._main_controller.interval_comboBox_currentTextChanged
        )
        self._ui.draw_pushButton.clicked.connect(self._main_controller.draw_pushButton_clicked)
        self._ui.begin_dateTimeEdit.dateTimeChanged.connect(self._main_controller.begin_dateTimeEdit_dateTimeChanged)
        self._ui.end_dateTimeEdit.dateTimeChanged.connect(self._main_controller.end_dateTimeEdit_dateTimeChanged)
        self._ui.use_current_end_checkBox.checkStateChanged.connect(
            self._main_controller.use_current_end_checkBox_checkStateChanged
        )

        # listen for model event signals
        self._model.model_init.connect(self.init_view)
        self._model.stock_connected.connect(self.on_stock_connected)
        self._model.stock_disconnected.connect(self.on_stock_disconnected)
        self._model.use_current_end_datetime_changed.connect(self.on_use_current_end_datetime_changed)
        self._model.data_to_draw.connect(self.on_data_to_draw)

        # init Controller
        self._main_controller.init_controller()

    @Slot()
    def init_view(self):
        self.statusBar().showMessage(f"Disconnected")

        self._ui.stockNames_comboBox.blockSignals(True)
        self._ui.stockNames_comboBox.addItems(self._model.api_secrets["stocks"])
        self._ui.stockNames_comboBox.setCurrentText(self._model.stock_name)
        self._ui.stockNames_comboBox.blockSignals(False)

        self._ui.accountNames_comboBox.blockSignals(True)
        self._ui.accountNames_comboBox.addItems(self._model.api_secrets["stocks"][self._model.stock_name]["accounts"])
        self._ui.accountNames_comboBox.setCurrentText(self._model.account_name)
        self._ui.accountNames_comboBox.blockSignals(False)

        self._ui.end_dateTimeEdit.blockSignals(True)
        self._ui.end_dateTimeEdit.setDateTime(self._model.end_datetime)
        self._ui.end_dateTimeEdit.blockSignals(False)

        self._ui.begin_dateTimeEdit.blockSignals(True)
        self._ui.begin_dateTimeEdit.setDateTime(self._model.begin_datetime)
        self._ui.begin_dateTimeEdit.blockSignals(False)

        if self._model.use_current_end_datetime:
            self._ui.use_current_end_checkBox.setCheckState(Qt.CheckState.Checked)
        else:
            self._ui.use_current_end_checkBox.setCheckState(Qt.CheckState.Unchecked)

        if self._model.auto_connect:
            self._ui.stockAutoConnect_checkBox.setCheckState(Qt.CheckState.Checked)
        else:
            self._ui.stockAutoConnect_checkBox.setCheckState(Qt.CheckState.Unchecked)

        if self._model.restore_begin_end_from_settings:
            self._ui.restore_begin_end_checkBox.setCheckState(Qt.CheckState.Checked)
        else:
            self._ui.restore_begin_end_checkBox.setCheckState(Qt.CheckState.Unchecked)

    @Slot()
    def on_stock_connected(self):
        self._ui.stock_status_label.setText("Connected :)")
        self._ui.stockConnect_pushButton.setText("Disconnect")
        self.statusBar().showMessage(f"Connected | {self._model.stock_name} | {self._model.account_name}")

        self._ui.pairs_listWidget.blockSignals(True)
        all_pairs = self._model.backend_api.get_all_pairs()
        self._ui.pairs_listWidget.clear()
        self._ui.pairs_listWidget.addItems(all_pairs)
        self._ui.pairs_listWidget.setCurrentRow(0)
        for pair in self._model.pairs:
            item = self._ui.pairs_listWidget.findItems(pair, Qt.MatchFlag.MatchExactly)[0]
            self._ui.pairs_listWidget.item(self._ui.pairs_listWidget.row(item)).setSelected(True)
            self._ui.pairs_listWidget.scrollToItem(item)
        self._ui.pairs_listWidget.blockSignals(False)

        self._ui.interval_comboBox.blockSignals(True)
        all_intervals = self._model.backend_api.get_available_intervals()
        self._ui.interval_comboBox.clear()
        self._ui.interval_comboBox.addItems(all_intervals)
        self._ui.interval_comboBox.setCurrentIndex(0)
        if self._model.interval:
            self._ui.interval_comboBox.setCurrentText(self._model.interval)
        self._ui.interval_comboBox.blockSignals(False)

        self._ui.stockNames_comboBox.setDisabled(True)
        self._ui.accountNames_comboBox.setDisabled(True)
        self._ui.draw_pushButton.setEnabled(True)
        self._ui.pairs_listWidget.setEnabled(True)
        self._ui.interval_comboBox.setEnabled(True)

    @Slot()
    def on_stock_disconnected(self):
        self._ui.stock_status_label.setText("Disconnected :(")
        self._ui.stockConnect_pushButton.setText("Connect")
        self.statusBar().showMessage("Disconnected")

        self._ui.stockNames_comboBox.setEnabled(True)
        self._ui.accountNames_comboBox.setEnabled(True)
        self._ui.draw_pushButton.setDisabled(True)
        self._ui.pairs_listWidget.setDisabled(True)
        self._ui.interval_comboBox.setDisabled(True)

    def closeEvent(self, event):
        self._main_controller.close()

    @Slot()
    def on_pairs_listWidget_itemSelectionChanged(self):
        self._main_controller.pairs_listWidget_itemSelectionChanged(
            [item.text() for item in self._ui.pairs_listWidget.selectedItems()]
        )

    @Slot()
    def on_use_current_end_datetime_changed(self):
        if self._model.use_current_end_datetime:
            self._ui.end_dateTimeEdit.setDisabled(True)
        else:
            self._ui.end_dateTimeEdit.setEnabled(True)

    @Slot()
    def on_data_to_draw(self):
        data = self._model.data
        df: pd.DataFrame = data[self._model.pairs[0]][self._model.interval]
        df.rename(
            columns={
                "Id": "id",
                "Time": "time",
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Volume": "volume",
                "Turnover": "turnover",
            },
            inplace=True,
        )
        df = df.drop(["turnover", "id"], axis=1)
        df.info()

        chart = QtChart()
        # # Columns: time | open | high | low | close | volume
        chart.set(df)
        self._ui.tradingView_gridLayout.addWidget(chart.get_webview(), 0, 0, 1, 1)
