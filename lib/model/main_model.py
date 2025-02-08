from PySide6.QtCore import QObject, Signal, QSettings, QCoreApplication


from lib.backend import api


class Model(QObject):
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

        self.init_data()

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

    def connect_to_stock(self):
        self.backend_api.connect_stock(
            stock_name=self.stock_name,
            account_name=self.account_name,
            api_key=self.api_secrets["stocks"][self.stock_name]["accounts"][self.account_name]["API_KEY"],
            api_secret=self.api_secrets["stocks"][self.stock_name]["accounts"][self.account_name]["API_SECRET"],
        )
        if self.backend_api.is_stock_connected:
            self.stock_connected.emit()

    def disconnect_stock(self):
        self.backend_api.disconnect_stock()
        QCoreApplication.processEvents()
        self.stock_disconnected.emit()

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

    #
    # @property
    # def amount(self):
    #     return self._amount
    #
    # @amount.setter
    # def amount(self, value):
    #     self._amount = value
    #     self.amount_changed.emit(value)
    #
