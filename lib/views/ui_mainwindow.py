# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'ui_mainwindow.ui'
##
## Created by: Qt User Interface Compiler version 6.8.2
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QGridLayout,
    QLabel, QListWidget, QListWidgetItem, QMainWindow,
    QMenuBar, QPushButton, QSizePolicy, QSpacerItem,
    QStatusBar, QTabWidget, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(1543, 897)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.gridLayout = QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName(u"gridLayout")
        self.tabWidget_2 = QTabWidget(self.centralwidget)
        self.tabWidget_2.setObjectName(u"tabWidget_2")
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.tabWidget_2.sizePolicy().hasHeightForWidth())
        self.tabWidget_2.setSizePolicy(sizePolicy)
        self.tab_3 = QWidget()
        self.tab_3.setObjectName(u"tab_3")
        self.gridLayout_2 = QGridLayout(self.tab_3)
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_2 = QLabel(self.tab_3)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 2, 0, 1, 1)

        self.draw_pushButton = QPushButton(self.tab_3)
        self.draw_pushButton.setObjectName(u"draw_pushButton")

        self.gridLayout_2.addWidget(self.draw_pushButton, 3, 0, 1, 1)

        self.interval_comboBox = QComboBox(self.tab_3)
        self.interval_comboBox.setObjectName(u"interval_comboBox")

        self.gridLayout_2.addWidget(self.interval_comboBox, 2, 2, 1, 1)

        self.label = QLabel(self.tab_3)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 1, 0, 1, 1)

        self.pairs_listWidget = QListWidget(self.tab_3)
        self.pairs_listWidget.setObjectName(u"pairs_listWidget")

        self.gridLayout_2.addWidget(self.pairs_listWidget, 1, 2, 1, 1)

        self.tabWidget_2.addTab(self.tab_3, "")
        self.tab_4 = QWidget()
        self.tab_4.setObjectName(u"tab_4")
        self.gridLayout_3 = QGridLayout(self.tab_4)
        self.gridLayout_3.setObjectName(u"gridLayout_3")
        self.stockNames_comboBox = QComboBox(self.tab_4)
        self.stockNames_comboBox.setObjectName(u"stockNames_comboBox")

        self.gridLayout_3.addWidget(self.stockNames_comboBox, 0, 1, 1, 1)

        self.accountNames_comboBox = QComboBox(self.tab_4)
        self.accountNames_comboBox.setObjectName(u"accountNames_comboBox")

        self.gridLayout_3.addWidget(self.accountNames_comboBox, 1, 1, 1, 1)

        self.label_3 = QLabel(self.tab_4)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_3.addWidget(self.label_3, 0, 0, 1, 1)

        self.label_4 = QLabel(self.tab_4)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_3.addWidget(self.label_4, 1, 0, 1, 1)

        self.stockConnect_pushButton = QPushButton(self.tab_4)
        self.stockConnect_pushButton.setObjectName(u"stockConnect_pushButton")

        self.gridLayout_3.addWidget(self.stockConnect_pushButton, 4, 0, 1, 2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.gridLayout_3.addItem(self.verticalSpacer, 5, 0, 1, 1)

        self.stockAutoConnect_checkBox = QCheckBox(self.tab_4)
        self.stockAutoConnect_checkBox.setObjectName(u"stockAutoConnect_checkBox")

        self.gridLayout_3.addWidget(self.stockAutoConnect_checkBox, 2, 0, 1, 1)

        self.stock_status_label = QLabel(self.tab_4)
        self.stock_status_label.setObjectName(u"stock_status_label")

        self.gridLayout_3.addWidget(self.stock_status_label, 3, 0, 1, 1)

        self.tabWidget_2.addTab(self.tab_4, "")

        self.gridLayout.addWidget(self.tabWidget_2, 0, 0, 1, 1)

        self.tradingView_tabWidget = QTabWidget(self.centralwidget)
        self.tradingView_tabWidget.setObjectName(u"tradingView_tabWidget")
        self.tradingView_tab = QWidget()
        self.tradingView_tab.setObjectName(u"tradingView_tab")
        self.gridLayout_4 = QGridLayout(self.tradingView_tab)
        self.gridLayout_4.setObjectName(u"gridLayout_4")
        self.tradingView_gridLayout = QGridLayout()
        self.tradingView_gridLayout.setObjectName(u"tradingView_gridLayout")

        self.gridLayout_4.addLayout(self.tradingView_gridLayout, 0, 0, 1, 1)

        self.tradingView_tabWidget.addTab(self.tradingView_tab, "")

        self.gridLayout.addWidget(self.tradingView_tabWidget, 0, 1, 1, 1)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 1543, 26))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        self.tabWidget_2.setCurrentIndex(0)
        self.tradingView_tabWidget.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"Pair Wings", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Interval", None))
        self.draw_pushButton.setText(QCoreApplication.translate("MainWindow", u"Draw", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Pairs", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_3), QCoreApplication.translate("MainWindow", u"Trading", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Stock", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Account", None))
        self.stockConnect_pushButton.setText(QCoreApplication.translate("MainWindow", u"Connect", None))
        self.stockAutoConnect_checkBox.setText(QCoreApplication.translate("MainWindow", u"Connect automatically on start the app", None))
        self.stock_status_label.setText(QCoreApplication.translate("MainWindow", u"Status: ", None))
        self.tabWidget_2.setTabText(self.tabWidget_2.indexOf(self.tab_4), QCoreApplication.translate("MainWindow", u"Settings", None))
        self.tradingView_tabWidget.setTabText(self.tradingView_tabWidget.indexOf(self.tradingView_tab), QCoreApplication.translate("MainWindow", u"Trading View", None))
    # retranslateUi

