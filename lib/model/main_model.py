from PySide6.QtCore import QObject, Signal, QSettings, QCoreApplication


from lib.backend import api


class Model(QObject):
    # amount_changed = Signal(int)

    def __init__(self):
        super().__init__()

        self.settings = QSettings("Pair Wings", "App")

        self.backend_api = api.BackendApi()

        self.api_secrets = None
        self._stock_name = None
        self._account_name = None

        self.init_data()

    def init_data(self):
        self.api_secrets = self.backend_api.read_api_secrets("api_secrets.json")
        stock_name = self.settings.value("settings/stock_name")
        if stock_name and stock_name in self.api_secrets["stocks"]:
            self.stock_name = stock_name
        else:
            self.stock_name = list(self.api_secrets["stocks"].keys())[0]

        account_name = self.settings.value("settings/account_name")
        if account_name and account_name in self.api_secrets["stocks"][self.stock_name]["accounts"]:
            self.account_name = account_name
        else:
            self.account_name = list(self.api_secrets["stocks"][self.stock_name]["accounts"].keys())[0]

    def connect_to_stock(self):
        self.backend_api.connect_stock(
            stock_name=self.stock_name,
            account_name=self.account_name,
            api_key=self.api_secrets["stocks"][self.stock_name]["accounts"][self.account_name]["API_KEY"],
            api_secret=self.api_secrets["stocks"][self.stock_name]["accounts"][self.account_name]["API_SECRET"],
        )

    def disconnect_stock(self):
        self.backend_api.disconnect_stock()
        QCoreApplication.processEvents()
        QCoreApplication.processEvents()
        QCoreApplication.processEvents()

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
