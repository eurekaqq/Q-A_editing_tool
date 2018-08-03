import pandas as pd
import numpy as np
import threading
import bottle
import server.web_api_routes
import os
import sys
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QMainWindow, QApplication, QWidget, QAction, QTableWidget, \
    QTableWidgetItem, QVBoxLayout, QHeaderView, QFormLayout, QLabel, QLineEdit, QMessageBox,QTabWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import pyqtSlot
import gc


class QA_system_window(QWidget):
    def __init__(self, title, width=800, height=600):
        super().__init__()
        self.title = title
        self.state = None
        self.width = 800
        self.height = 600
        self.server = None
        self.data_path = r'./data/new_tairo_dataset2.xlsx'
        # self.data = pd.read_excel(r'./data/new_tairo_dataset2.xlsx', keep_default_na=False)
        self.initUI()


    def initUI(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(640,480)
        self.resize(self.width, self.height)

        self.tableWidget = self.createTable()
        self.keyword_layout = self.createKeyword()

        # Add box layout, add table to box layout and add box layout to widget

        self.main_layout = QHBoxLayout()
        button_layout = QVBoxLayout()
        view_data_btn = QPushButton("顯示資料庫資料")
        view_badness_btn = QPushButton("顯示需要改進資料")
        add_keyword_btn = QPushButton('加入關鍵字')
        add_similarity_word_btn = QPushButton('加入相似詞')
        start_server_btn = QPushButton("啟動伺服器")
        start_training_btn = QPushButton("啟動訓練")

        button_layout.addWidget(view_data_btn)
        button_layout.addWidget(view_badness_btn)
        button_layout.addWidget(add_keyword_btn)
        button_layout.addWidget(add_similarity_word_btn)
        button_layout.addWidget(start_server_btn)
        button_layout.addWidget(start_training_btn)

        view_data_btn.clicked.connect(self._swap_to_all_data)
        start_server_btn.clicked.connect(self._swap_to_start_server)
        add_keyword_btn.clicked.connect(self._swap_to_add_keyword)

        table = QVBoxLayout()

        self.main_layout.addLayout(button_layout)
        # self.main_layout.addLayout(self.keyword_layout)
        self.main_layout.addLayout(table)

        self.gg = QTableWidget()

        self.state = self.gg

        table.addWidget(self.gg)
        io_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_method)
        cancel_btn = QPushButton('取消')
        cancel_btn.clicked.connect(self.cancel_method)
        io_layout.addWidget(save_btn)
        io_layout.addWidget(cancel_btn)
        table.addLayout(io_layout)
        # self.main_layout.replaceWidget(QTableWidget(), self.tableWidget)
        self.setLayout(self.main_layout)

        # Show widget
        self.show()

    @pyqtSlot()
    def _swap_to_all_data(self):
        if self.state is not self.tableWidget:
            self.main_layout.children()[1].replaceWidget(self.state, self.tableWidget)
            self.state = self.tableWidget
        else:
            pass


    @pyqtSlot()
    def _swap_to_add_keyword(self):
        self.main_layout.layout().layout

        if self.state is not self.keyword_widget:
            self.main_layout.lay
            self.main_layout.children()[1] = self.keyword_layout
            self.state = self.keyword_widget
        else:
            pass

    @pyqtSlot()
    def _swap_to_add_similarity_word(self):
        if self.state is not self.tableWidget:
            self.state = self.tableWidget
            # self.main_layout.replaceWidget(QTableWidget(), self.tableWidget)
            # print(self.main_layout.children()[1])
            self.main_layout.children()[1].replaceWidget(self.gg, self.tableWidget)
        else:
            pass

    @pyqtSlot()
    def _swap_to_start_server(self):
        def thread_job():
            bottle.run(host="140.118.127.51", port="8080", server='waitress', debug=False)

        if self.server is None:
            self.server = threading.Thread(target=thread_job)
            self.server.start()

        else:
            QMessageBox.information(self, 'Message', '伺服器已啟動!')

    @pyqtSlot()
    def _swap_to_start_training(self):
        if self.state is not self.tableWidget:
            self.state = self.tableWidget
            # self.main_layout.replaceWidget(QTableWidget(), self.tableWidget)
            # print(self.main_layout.children()[1])
            self.main_layout.children()[1].replaceWidget(self.gg, self.tableWidget)
        else:
            pass

    def createTable(self):
        #load data
        self.data = pd.read_excel(self.data_path, keep_default_na=False)

        # Create table
        tableWidget = QTableWidget()
        tableWidget.setRowCount(self.data.shape[0] + 3)
        tableWidget.setColumnCount(self.data.shape[1])

        for index, column in enumerate(self.data.columns):
            tableWidget.setHorizontalHeaderItem(index, QTableWidgetItem(column))

        for column_index in range(self.data.shape[1]):
            for row_index in range(self.data.shape[0]):
                tableWidget.setItem(row_index, column_index,
                                         QTableWidgetItem(str(self.data.iloc[row_index, column_index])))

        # table selection change
        tableWidget.cellChanged.connect(self.add_row)

        return tableWidget


    def createKeyword(self):
        keyword_widget = QFormLayout()
        keyword_widget.addRow(QLabel('字'), QLineEdit())
        keyword_widget.addRow(QLabel('詞性'), QLineEdit())



        return keyword_widget

    @pyqtSlot()
    def add_row(self):
        for selected_item in self.tableWidget.selectedItems():
            if selected_item.text() != "" and self.tableWidget.rowCount() - selected_item.row() < 3:
                self.tableWidget.insertRow(self.tableWidget.rowCount())

    @pyqtSlot()
    def cancel_method(self):
        self.tableWidget = self.createTable()
        self.main_layout.children()[1].replaceWidget(self.state, self.tableWidget)
        self.state = self.tableWidget

    @pyqtSlot()
    def save_method(self):
        for row_index in range(self.tableWidget.rowCount()):
            if self.tableWidget.item(row_index,0) is not None:
                self.data.loc[row_index] = [self.tableWidget.item(row_index, column_index).text()
                                                        for column_index in range(self.tableWidget.columnCount())]

        self.data.to_excel(r'./data/test4444444.xlsx', index=False)
        print('ggg')

    @pyqtSlot()
    def on_click(self):
        print("\n")

        # for currentQTableWidgetItem in self.tableWidget.selectedItems():
        #     self.data.iloc[currentQTableWidgetItem.row(), currentQTableWidgetItem.column()] = currentQTableWidgetItem.text()
        #     print(currentQTableWidgetItem.row(), currentQTableWidgetItem.column(), currentQTableWidgetItem.text())
        #     self.data.to_excel(r'./data/test222.xlsx', index=False)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    main_window = QA_system_window('智慧 QA system')
    sys.exit(app.exec_())
