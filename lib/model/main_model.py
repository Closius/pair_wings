from PySide6.QtCore import QObject, Slot, Signal, QSettings, QCoreApplication, QTimer


from lib.backend import api


class Model(QObject):
    model_init = Signal()
    stock_connected = Signal()
    stock_disconnected = Signal()

    def __init__(self):
        super().__init__()

        self.settings = QSettings("Pair Wings", "App")

        self.backend_api = api.BackendApi()

        self.api_secrets = None

        self._stock_name = None
        self._account_name = None
        self._auto_connect = False
        self._is_stock_connected = False

        self._pairs = None
        self._interval = None

        self._check_stock_connection_status_timer = QTimer(self)
        self._check_stock_connection_status_timer.setInterval(1000)
        self._check_stock_connection_status_timer.timeout.connect(self.check_stock_connection_status)

    def init_data(self):
        self.api_secrets = self.backend_api.read_api_secrets("api_secrets.json")
        stock_name = self.settings.value("settings/stock_name", None)
        if stock_name and stock_name in self.api_secrets["stocks"]:
            self.stock_name = stock_name
        else:
            self.stock_name = list(self.api_secrets["stocks"].keys())[0]

        account_name = self.settings.value("settings/account_name", None)
        if account_name and account_name in self.api_secrets["stocks"][self.stock_name]["accounts"]:
            self.account_name = account_name
        else:
            self.account_name = list(self.api_secrets["stocks"][self.stock_name]["accounts"].keys())[0]

        _ac = self.settings.value("settings/auto_connect", False)
        if isinstance(_ac, str):
            _ac = True if _ac == "true" else False
        self.auto_connect = _ac

        self.pairs = self.settings.value("settings/pairs", None)
        self.interval = self.settings.value("settings/interval", None)

        self.model_init.emit()

    @Slot()
    def check_stock_connection_status(self):
        if self.backend_api.is_stock_connected:
            if not self._is_stock_connected:
                self.stock_connected.emit()
                self._is_stock_connected = True
        else:
            self.stock_disconnected.emit()
            self._is_stock_connected = False
            self._check_stock_connection_status_timer.stop()

    def connect_to_stock(self):
        self.backend_api.connect_stock(
            stock_name=self.stock_name,
            account_name=self.account_name,
            api_key=self.api_secrets["stocks"][self.stock_name]["accounts"][self.account_name]["API_KEY"],
            api_secret=self.api_secrets["stocks"][self.stock_name]["accounts"][self.account_name]["API_SECRET"],
        )
        self._check_stock_connection_status_timer.start()

    def disconnect_stock(self):
        self.backend_api.disconnect_stock()

    @property
    def stock_name(self):
        return self._stock_name

    @stock_name.setter
    def stock_name(self, value):
        self._stock_name = value
        self.settings.setValue("settings/stock_name", value)

    @property
    def account_name(self):
        return self._account_name

    @account_name.setter
    def account_name(self, value):
        self._account_name = value
        self.settings.setValue("settings/account_name", value)

    @property
    def auto_connect(self):
        return self._auto_connect

    @auto_connect.setter
    def auto_connect(self, value):
        self._auto_connect = value
        self.settings.setValue("settings/auto_connect", value)

    @property
    def pairs(self):
        return self._pairs

    @pairs.setter
    def pairs(self, value):
        self._pairs = value
        self.settings.setValue("settings/pairs", value)

    @property
    def interval(self):
        return self._interval

    @interval.setter
    def interval(self, value):
        self._interval = value
        self.settings.setValue("settings/interval", value)
