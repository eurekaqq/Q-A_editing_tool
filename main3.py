import sys
import os
import subprocess
import time
import datetime
import shutil
import unicodedata
import json
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QApplication, QWidget, QVBoxLayout, QFormLayout, \
    QLabel, QLineEdit, QMessageBox, QTabWidget, QComboBox, QCheckBox, QTextEdit, QCompleter, QTableWidget, \
    QTableWidgetItem, QAbstractItemView, QFileDialog
from PyQt5.QtCore import pyqtSlot, QStringListModel
from PyQt5 import QtGui, QtCore
from pymongo import MongoClient


class dig_keyword(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()

        keyword_widget = QFormLayout()
        self.word = QLineEdit()
        self.pos = QComboBox()
        self.pos.addItems(['不知道', '動詞', '名詞'])
        keyword_widget.addRow(QLabel('字'), self.word)
        keyword_widget.addRow(QLabel('詞性'), self.pos)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_btn_method)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.cancel_btn_method)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(keyword_widget)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

    @pyqtSlot()
    def save_btn_method(self):
        def text_to_pos(text):
            if text == '不知道':
                return ''
            elif text == '動詞':
                return 'v'
            else:
                return 'n'

        if self.word.text() != '':
            with open(r'./similarity/jieba_model/dict.txt', 'a', encoding='utf-8') as output:
                output.write(unicodedata.normalize('NFC', self.word.text()).strip() + ' 1000000 ' +
                             unicodedata.normalize('NFC', text_to_pos(
                                 self.pos.text()).strip() + '\n'))

        else:
            QMessageBox.information(self, '警告', '字欄位需填寫內容')

    @pyqtSlot()
    def cancel_btn_method(self):
        self.word.clear()


class dig_similarity_word(QWidget):
    def __init__(self):
        super().__init__()
        self.current_index = None
        self.initUI()

    def initUI(self):
        # insert search
        # get synonym
        with(open(r'./data/synonyms_tw.txt', 'r', encoding='utf-8')) as data:
            self.synonym_dict = [line.split() for line in data.readlines()]

        self.all_synonym = set(word for synonym in self.synonym_dict for word in synonym)

        def find_synonym():
            word = self.word1.text()
            for index, words in enumerate(self.synonym_dict):
                if word in words:
                    self.current_index = index
                    self.word2.setText(' '.join(words))
                    break
            else:
                self.current_index = None

        self.main_layout = QVBoxLayout()

        keyword_widget = QFormLayout()
        self.word_layout = QHBoxLayout()
        self.word1 = QLineEdit()
        self.remove_btn = QPushButton('移除同義詞')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        def init_current_index():
            self.current_index = None
            find_synonym()
            if self.current_index is None:
                self.word2.clear()
            # print(self.current_index)

        self.word1.textEdited.connect(init_current_index)

        self.model = QStringListModel()
        self.model.setStringList(self.all_synonym)
        completer = QCompleter()
        completer.setModel(self.model)
        completer.activated.connect(find_synonym)
        self.word1.setCompleter(completer)

        self.word_layout.addWidget(self.word1)
        self.word_layout.addWidget(self.remove_btn)

        self.word2 = QTextEdit()
        self.pos = QComboBox()
        self.pos.addItems(['不知道', '地名', '動詞', '名詞', '關鍵字'])

        keyword_widget.addRow(QLabel('欲尋找的詞'), self.word_layout)
        keyword_widget.addRow(QLabel('其相似詞'), self.word2)
        keyword_widget.addRow(QLabel('詞的種類'), self.pos)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_btn_method)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.cancel_btn_method)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(keyword_widget)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

    @pyqtSlot()
    def save_btn_method(self):
        def find_synonym():
            word = self.word1.text()
            for index, words in enumerate(self.synonym_dict):
                if word in words:
                    return words
            else:
                return []

        if self.word1.text() != '' and self.word2.toPlainText() != '':
            synonym_of_word = find_synonym()
            self.all_synonym.update(self.word2.toPlainText().split(' '))
            for i in set(synonym_of_word) - set(self.word2.toPlainText().split(' ')):
                self.all_synonym.discard(i)
            self.model.setStringList(self.all_synonym)

            with open(r'./data/expend_dict.json', 'r', encoding='utf-8') as jsonFile:
                expend_word = json.load(jsonFile)

            for word in synonym_of_word:
                expend_word.pop(word, None)

            if self.current_index is not None:
                self.synonym_dict[self.current_index] = self.word2.toPlainText().split()
            else:
                self.synonym_dict.append(self.word2.toPlainText().split())
                self.current_index = len(self.synonym_dict) - 1

            shutil.copyfile(r'./data/dict.txt.big', r'./data/dict.txt')

            for word in self.word2.toPlainText().split():
                if self.pos.currentText() == "不知道":
                    expend_word[unicodedata.normalize('NFC', word)] = ''
                elif self.pos.currentText() == '地名':
                    expend_word[unicodedata.normalize('NFC', word)] = 'n'
                    with open(r'./data/user_keyword.txt', 'a', encoding='utf-8') as place_dic:
                        place_dic.write(word + '\n')
                elif self.pos.currentText() == '關鍵字':
                    expend_word[unicodedata.normalize('NFC', word)] = 'n'
                    with open(r'./data/user_keyword.txt', 'a', encoding='utf-8') as place_dic:
                        place_dic.write(word + '\n')
                elif self.pos.currentText() == '名詞':
                    expend_word[unicodedata.normalize('NFC', word)] = 'n'
                else:
                    expend_word[unicodedata.normalize('NFC', word)] = 'v'

            with open(r'./data/dict.txt', 'a', encoding='utf-8') as output:
                for word in expend_word:
                    output.write('{0} 100000000000000 {1}\n'.format(word, expend_word[word]))

            with open(r'./data/expend_dict.json', 'w', encoding='utf-8') as jsonFile:
                json.dump(expend_word, jsonFile, indent=4)

            with open(r'./data/synonyms_tw.txt', 'w', encoding='utf-8') as output:
                for word_list in self.synonym_dict:
                    output.write('{0}\n'.format(' '.join(word_list)))

            QMessageBox.information(self, '提醒', '已新增"{}"至資料庫'.format(self.word2.toPlainText()))

        else:
            QMessageBox.information(self, '警告', '兩欄皆須填寫內容')

    # @pyqtSlot()
    # def save_btn_method(self):
    #     if self.word1.text() != '' and self.word2.toPlainText() != '':
    #         if self.current_index is not None:
    #             self.synonym_dict[self.current_index] = self.word2.toPlainText().split()
    #         else:
    #             self.synonym_dict.append(self.word2.toPlainText().split())
    #
    #         with open(r'./similarity/jieba_model/dict.txt', 'a', encoding='utf-8') as output:
    #             for word in self.word2.toPlainText().split():
    #                 if self.pos.currentText() == "不知道":
    #                     output.write('{0} 100000000000000\n'.format(unicodedata.normalize('NFC', word)))
    #                 elif self.pos.currentText() == '地名':
    #                     output.write('{0} 100000000000000 n\n'.format(unicodedata.normalize('NFC', word)))
    #                     with open(r'./data/place.txt', 'a', encoding='utf-8') as place_dic:
    #                         place_dic.write(word + '\n')
    #                 elif self.pos.currentText() == '名詞':
    #                     output.write('{0} 100000000000000 n\n'.format(unicodedata.normalize('NFC', word)))
    #                 else:
    #                     output.write('{0} 100000000000000 v\n'.format(unicodedata.normalize('NFC', word)))
    #
    #         with open(r'./generation/synonyms_tw.txt', 'w', encoding='utf-8') as output:
    #             for word_list in self.synonym_dict:
    #                 output.write('{0}\n'.format(' '.join(word_list)))
    #
    #         QMessageBox.information(self, '提醒', '已新增"{}"至資料庫'.format(self.word2.toPlainText()))
    #
    #     else:
    #         QMessageBox.information(self, '警告', '兩欄皆須填寫內容')

    @pyqtSlot()
    def remove_btn_method(self):
        if self.current_index != None:
            result = QMessageBox.question(self, '警告', '確定要刪除"{0}"的同義詞嗎?'.format(self.word1.text()),
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)
            if result == QMessageBox.Yes:
                with open(r'./data/expend_dict.json', 'r', encoding='utf-8') as jsonFile:
                    expend_word = json.load(jsonFile)

                for i in self.synonym_dict[self.current_index]:
                    self.all_synonym.discard(i)
                    expend_word.pop(i, None)
                self.model.setStringList(self.all_synonym)

                shutil.copyfile(r'./data/dict.txt.big', r'./data/dict.txt')

                with open(r'./data/dict.txt', 'a', encoding='utf-8') as output:
                    for word in expend_word:
                        output.write('{0} 100000000000000 {1}\n'.format(word, expend_word[word]))

                with open(r'./data/expend_dict.json', 'w', encoding='utf-8') as jsonFile:
                    json.dump(expend_word, jsonFile, indent=4)

                del self.synonym_dict[self.current_index]
                with open(r'./data/synonyms_tw.txt', 'w', encoding='utf-8') as output:
                    for word_list in self.synonym_dict:
                        output.write('{0}\n'.format(' '.join(word_list)))

                self.current_index = None
            else:
                pass
        else:
            QMessageBox.information(self, "提醒", '資料庫中無"{}"的同義詞'.format(self.word1.text()))

    @pyqtSlot()
    def cancel_btn_method(self):
        # self.model.stringList().append(self.word1.text())
        self.word1.clear()
        self.word2.clear()
        self.pos.setCurrentIndex(0)


class ComboBox(QComboBox):
    popupAboutToBeShown = QtCore.pyqtSignal()

    def __init__(self, my_function=None):
        super().__init__()
        self.my_function = my_function

    def showPopup(self):
        self.popupAboutToBeShown.emit()
        if self.my_function is not None:
            self.my_function()
        super(ComboBox, self).showPopup()


# class TableWidget(QTableWidget):
#     def __init__(self):
#         super().__init__()
#
#     def removeRow(self, row: int):


class dig_edit_sentence(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        client = MongoClient('localhost', 27017)
        db = client.taroko
        self.collection = db.origin

        self.main_layout = QVBoxLayout()

        sentence_widget = QFormLayout()
        self.select_layout = QHBoxLayout()

        # self.sentence_list = ComboBox(my_function=self.check_data_update)
        # for row in self.collection.find():
        #     self.sentence_list.addItem(str(row['sentence']))
        # self.sentence_list.currentIndexChanged.connect(self.show_selected_item)

        self.search_text = QLineEdit()
        self.search_text.textChanged.connect(self.search_sentences)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(self.collection.find().count())
        self.tableWidget.setColumnCount(1)
        self.tableWidget.itemSelectionChanged.connect(self.show_selected_item)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.verticalHeader().setVisible(False)
        # self.tableWidget.horizontalHeader().setVisible(False)
        # self.tableWidget.horizontalHeader().setMinimumWidth()

        self.sentence_index_list = []

        # for index, column in enumerate(self.data.columns):
        #     tableWidget.setHorizontalHeaderItem(index, QTableWidgetItem(column))
        self.search_sentences()
        # for index, item in enumerate(self.collection.find()):
        #     self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item['sentence'])))
        #     self.sentence_index_list.append(item['uuid'])
        # self.tableWidget.setItem(index, 1, QTableWidgetItem(str(item['uuid'])))

        self.tableWidget.resizeColumnsToContents()

        self.new_or_not = QCheckBox('新增句子')
        self.new_or_not.stateChanged.connect(self.state_changed)

        self.remove_btn = QPushButton('刪除句子')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        # self.select_layout.addWidget(self.sentence_list)
        self.select_layout.addWidget(self.search_text)
        self.select_layout.addWidget(self.new_or_not)
        self.select_layout.addWidget(self.remove_btn)
        temp = self.collection.find_one({'uuid': 0})
        self.sentence = QTextEdit()
        self.answer = QTextEdit()
        self.url = QLineEdit()
        self.sentence.setText(temp['sentence'])
        self.answer.setText(temp['answer'])
        self.url.setText(temp['url'])

        sentence_widget.addRow(QLabel('搜尋'), self.select_layout)
        sentence_widget.addRow(QLabel('欲編輯句子'), self.tableWidget)
        sentence_widget.addRow(QLabel('問句'), self.sentence)
        sentence_widget.addRow(QLabel('答案'), self.answer)
        sentence_widget.addRow(QLabel('網址'), self.url)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_btn_method)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.cancel_btn_method)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(sentence_widget)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

    # 好像有BUG，會拿到下一句
    @pyqtSlot()
    def show_selected_item(self):
        if len(self.sentence_index_list) > 0:
            data = self.collection.find_one({'uuid': int(self.sentence_index_list[
                                                             min(self.tableWidget.currentIndex().row(),
                                                                 len(self.sentence_index_list) - 1)])})
            if data != None:
                self.sentence.setText(str(data['sentence']))
                self.answer.setText(str(data['answer']))
                self.url.setText(str(data['url']))
        else:
            pass

    @pyqtSlot()
    def search_sentences(self):
        self.tableWidget.clear()
        self.sentence_index_list.clear()

        if not self.search_text.text() == '':
            search_condition = [{'sentence': {'$regex': '{0}'.format(word)}}
                                for word in self.search_text.text().split()]
            # for index, item in enumerate(
            #         self.collection.find({'sentence': {'$regex': '.*{0}*.'.format(self.search_text.text())}})):
            search = self.collection.find({'$and': search_condition})
            self.tableWidget.setRowCount(search.count())

            for index, item in enumerate(search):
                self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item['sentence'])))
                self.sentence_index_list.append(item['uuid'])

        else:
            search = self.collection.find()
            self.tableWidget.setRowCount(search.count())
            for index, item in enumerate(search):
                self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item['sentence'])))
                self.sentence_index_list.append(item['uuid'])

        # self.tableWidget.setRowCount(len(self.sentence_index_list))

    # 未完成，可能要使用者用search來刷新
    @pyqtSlot()
    def check_data_update(self):
        if self.collection.find().count() > len(self.sentence_index_list):
            for row in self.collection.find({'uuid': {'$gte': len(self.sentence_index_list)}}):
                self.sentence_index_list.append(row['uuid'])

                pass

    # finished
    @pyqtSlot()
    def state_changed(self):
        self.sentence.clear()
        self.answer.clear()
        self.url.clear()
        if self.new_or_not.checkState():
            self.tableWidget.setDisabled(True)

        else:
            self.tableWidget.setDisabled(False)
            temp = self.collection.find_one({'uuid': self.sentence_index_list[self.tableWidget.currentIndex().row()]})
            self.sentence.setText(str(temp['sentence']))
            self.answer.setText(str(temp['answer']))
            self.url.setText(str(temp['url']))

    # 清除最後一個好像有BUG
    @pyqtSlot()
    def remove_btn_method(self):
        if self.tableWidget.currentItem() is not None:
            if self.new_or_not.checkState():
                QMessageBox.information(self, "提醒", '請先勾去"新增句子"')

            elif len(self.sentence_index_list) > 0:
                result = QMessageBox.question(self, '警告', '確定要刪除"{0}"嗎?'.format(self.tableWidget.currentItem().text()),
                                              QMessageBox.Yes | QMessageBox.No,
                                              QMessageBox.No)

                if result == QMessageBox.Yes:
                    current_index = self.sentence_index_list[self.tableWidget.currentIndex().row()]
                    for i in range(self.tableWidget.currentIndex().row() + 1, len(self.sentence_index_list)):
                        self.sentence_index_list[i] -= 1
                    self.collection.remove({'uuid': current_index})

                    for row in self.collection.find({'uuid': {'$gt': current_index}}):
                        row['uuid'] -= 1
                        self.collection.save(row)

                    del self.sentence_index_list[self.tableWidget.currentIndex().row()]

                    if self.tableWidget.rowCount() == 1:
                        self.tableWidget.setItem(0, 0, QTableWidgetItem(''))

                    else:
                        self.tableWidget.removeRow(self.tableWidget.currentIndex().row())

                else:
                    pass

            else:
                pass
        else:
            pass

    # finished
    @pyqtSlot()
    def save_btn_method(self):
        if self.new_or_not.checkState():
            data = {'uuid': self.collection.find().count(), 'sentence': self.sentence.toPlainText(),
                    'answer': self.answer.toPlainText(), 'url': self.url.text(),
                    'segmentation': '',
                    'pos': ''}
            self.collection.insert(data)
            # print(len(self.sentence_index_list))
            self.sentence_index_list.append(data['uuid'])
            # print(len(self.sentence_index_list))
            self.tableWidget.insertRow(self.tableWidget.rowCount())
            self.tableWidget.setItem(self.tableWidget.rowCount() - 1, 0, QTableWidgetItem(str(data['sentence'])))
            QMessageBox.information(self, "提醒", '已儲存"{}"'.format(self.sentence.toPlainText()))

        elif len(self.sentence_index_list) > 0:
            data = self.collection.find_one({'uuid': self.sentence_index_list[self.tableWidget.currentIndex().row()]})
            data['sentence'] = self.sentence.toPlainText()
            data['answer'] = self.answer.toPlainText()
            data['url'] = self.url.text()
            data['segmentation'] = ''
            data['pos'] = ''
            self.collection.save(data)
            self.tableWidget.setItem(self.tableWidget.currentIndex().row(), 0, QTableWidgetItem(str(data['sentence'])))
            QMessageBox.information(self, "提醒", '已儲存"{}"'.format(self.sentence.toPlainText()))

        else:
            pass

    @pyqtSlot()
    def cancel_btn_method(self):
        self.sentence.clear()
        self.answer.clear()
        self.url.clear()


class dig_sentence_log(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        client = MongoClient('localhost', 27017)
        db = client.taroko
        self.collection_log = db.log
        self.collection_ori = db.origin

        self.main_layout = QVBoxLayout()

        sentence_widget = QFormLayout()
        self.select_layout = QHBoxLayout()
        self.show_all_sentences = QCheckBox('顯示所有紀錄')
        self.show_all_sentences.stateChanged.connect(self.state_changed)
        self.sentences_id = []

        self.search_text = QLineEdit()
        self.search_text.textChanged.connect(self.search_sentences)

        self.tableWidget = QTableWidget()
        self.tableWidget.setRowCount(self.collection_log.find({'answer': ''}).count())
        self.tableWidget.setColumnCount(1)
        self.tableWidget.itemSelectionChanged.connect(self.show_selected_item)
        self.tableWidget.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.tableWidget.setSelectionMode(QAbstractItemView.SingleSelection)
        self.tableWidget.verticalHeader().setVisible(False)

        self.sentence_index_list = []
        self.search_sentences()

        self.tableWidget.resizeColumnsToContents()

        self.remove_btn = QPushButton('刪除紀錄')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        self.select_layout.addWidget(self.search_text)
        self.select_layout.addWidget(self.show_all_sentences)
        self.select_layout.addWidget(self.remove_btn)

        temp = self.collection_log.find_one({'answer': ''})
        self.sentence = QTextEdit()
        if temp is not None:
            self.sentence.setText(str(temp['sentence']))
        self.answer = QTextEdit()
        self.url = QLineEdit()

        sentence_widget.addRow(QLabel('搜尋'), self.select_layout)
        sentence_widget.addRow(QLabel('回答紀錄'), self.tableWidget)
        sentence_widget.addRow(QLabel('問句'), self.sentence)
        sentence_widget.addRow(QLabel('答案'), self.answer)
        sentence_widget.addRow(QLabel('網址'), self.url)

        button_layout = QHBoxLayout()
        save_btn = QPushButton("儲存")
        save_btn.clicked.connect(self.save_btn_method)
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.cancel_btn_method)

        button_layout.addWidget(save_btn)
        button_layout.addWidget(cancel_btn)

        self.main_layout.addLayout(sentence_widget)
        self.main_layout.addLayout(button_layout)

        self.setLayout(self.main_layout)

    @pyqtSlot()
    def search_sentences(self):
        self.tableWidget.clear()
        self.sentence_index_list.clear()
        search_condition = []

        if self.show_all_sentences.checkState():
            pass
        else:
            search_condition.append({'answer': ''})

        if not self.search_text.text() == '':
            search_condition += [{'sentence': {'$regex': '{0}'.format(word)}}
                                 for word in self.search_text.text().split()]

        if len(search_condition):
            search = self.collection_log.find({'$and': search_condition})
        else:
            search = self.collection_log.find()

        self.tableWidget.setRowCount(search.count())

        for index, item in enumerate(search):
            self.tableWidget.setItem(index, 0, QTableWidgetItem(str(item['sentence'])))
            self.sentence_index_list.append(item['_id'])

    @pyqtSlot()
    def load_sentence(self):
        for _ in range(len(self.sentences_id)):
            self.log_list.removeItem(0)

        self.sentences_id = []

        if self.show_all_sentences.checkState():
            for row in self.collection_log.find():
                self.sentences_id.append(row['_id'])
                self.log_list.addItem(str(row['sentence']))
            if self.log_list.count() > len(self.sentences_id):
                if len(self.sentences_id) > 0:
                    self.log_list.removeItem(0)

        else:
            for row in self.collection_log.find({'answer': ''}):
                self.sentences_id.append(row['_id'])
                self.log_list.addItem(str(row['sentence']))

    @pyqtSlot()
    def show_selected_item(self):
        if len(self.sentence_index_list) > 0:
            data = self.collection_log.find_one({'_id': self.sentence_index_list[
                min(self.tableWidget.currentIndex().row(), len(self.sentence_index_list) - 1)]})

            if data != None:
                self.sentence.setText(str(data['sentence']))
                self.answer.setText(str(data['answer']))

        else:
            pass

    @pyqtSlot()
    def state_changed(self):
        self.sentence.clear()
        self.answer.clear()
        # self.load_sentence()
        self.search_sentences()

    @pyqtSlot()
    def remove_btn_method(self):
        if self.tableWidget.currentItem() is not None:
            if len(self.sentence_index_list) > 0:
                result = QMessageBox.question(self, '警告', '確定要刪除"{0}"嗎?'.format(self.tableWidget.currentItem().text()),
                                              QMessageBox.Yes | QMessageBox.No,
                                              QMessageBox.No)

                if result == QMessageBox.Yes:
                    current_index = self.sentence_index_list[self.tableWidget.currentIndex().row()]
                    self.collection_log.remove({'_id': current_index})

                    del self.sentence_index_list[self.tableWidget.currentIndex().row()]

                    if self.tableWidget.rowCount() == 1:
                        self.tableWidget.setItem(0, 0, QTableWidgetItem(''))

                    else:
                        self.tableWidget.removeRow(self.tableWidget.currentIndex().row())

                else:
                    pass
            else:
                QMessageBox.information(self, '警告', '目前沒有句子')
        else:
            pass

    def remove_item_from_table(self):
        current_index = self.sentence_index_list[self.tableWidget.currentIndex().row()]
        self.collection_log.remove({'_id': current_index})

        del self.sentence_index_list[self.tableWidget.currentIndex().row()]

        if self.tableWidget.rowCount() == 1:
            self.tableWidget.setItem(0, 0, QTableWidgetItem(''))

        else:
            self.tableWidget.removeRow(self.tableWidget.currentIndex().row())

    @pyqtSlot()
    def save_btn_method(self):
        if len(self.sentence_index_list) > 0:
            data = {'uuid': self.collection_ori.find().count(), 'sentence': self.sentence.toPlainText(),
                    'answer': self.answer.toPlainText(), 'url': '',
                    'segmentation': '',
                    'pos': ''}
            self.collection_ori.insert(data)
            QMessageBox.information(self, '提醒', '已儲存"{}"'.format(self.sentence.toPlainText()))
            self.remove_item_from_table()

        else:
            QMessageBox.information(self, '警告', '目前沒有句子')

    @pyqtSlot()
    def cancel_btn_method(self):
        data = self.collection_log.find_one({'_id': self.sentence_index_list[self.tableWidget.currentIndex().row()]})
        self.sentence.setText(str(data['sentence']))
        self.answer.setText(str(data['answer']))


class back_up_window(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        self.main_layout = QVBoxLayout()

        self.backup_btn = QPushButton('備份')
        self.backup_btn.clicked.connect(self.backup)
        self.restore_btn = QPushButton('還原')
        self.restore_btn.clicked.connect(self.restore)

        self.main_layout.addWidget(self.backup_btn)
        self.main_layout.addWidget(self.restore_btn)

        self.setLayout(self.main_layout)

    def backup(self):
        # subprocess.check_output(['mongodump', '-d', 'taroko', '-o', './backup/{}'.format(time.strftime(r'%Y-%m-%d'))])
        subprocess.call(['mongodump', '-d', 'taroko', '-o', './backup/{}'.format(time.strftime(r'%Y-%m-%d'))])

        with open(r'./data/backup_log.json', 'w', encoding='utf-8') as config:
            json.dump({'last_backup_date': time.strftime(r'%Y-%m-%d')}, config, indent=4, ensure_ascii=True,
                      sort_keys=True)

        QMessageBox.information(self, '提醒', '備份成功')

    def restore(self):
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dir_name = QFileDialog.getExistingDirectory(self)
        if dir_name:
            subprocess.call(['mongorestore', '-d', 'taroko', '--drop', dir_name])
            QMessageBox.information(self, '提醒', '還原成功')

    @staticmethod
    def auto_backup():
        subprocess.call(['mongodump', '-d', 'taroko', '-o', './backup/{}'.format(time.strftime(r'%Y-%m-%d'))])

        with open(r'./data/backup_log.json', 'w', encoding='utf-8') as config:
            json.dump({'last_backup_date': time.strftime(r'%Y-%m-%d')}, config, indent=4, ensure_ascii=True,
                      sort_keys=True)


class QA_system_window(QTabWidget):
    def __init__(self, title, width=650, height=500):
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(self.width, self.height)
        self.resize(self.width, self.height)

        self.addTab(dig_similarity_word(), '編輯同義詞')
        self.addTab(dig_edit_sentence(), '編輯問句')
        self.addTab(dig_sentence_log(), '回答紀錄')
        self.addTab(back_up_window(), '備份與還原')

        # Show widget
        self.show()

        with open(r'./data/backup_log.json', 'r', encoding='utf-8') as backup_date:
            last_date_json = json.load(backup_date)
            temp = time.strptime(last_date_json['last_backup_date'], '%Y-%m-%d')
            last_date = datetime.datetime(temp[0], temp[1], temp[2])
            datetime.datetime.now()

        if (datetime.datetime.now() - last_date).days > 6:
            back_up_window.auto_backup()
            QMessageBox.information(self, '提醒', '自動備份成功')


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QtGui.QFont('', 12))
    main_window = QA_system_window('問答編輯系統 (Best-answer Editing Tool)')
    sys.exit(app.exec_())
