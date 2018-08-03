import sys
import os
import shutil
import unicodedata
import json
from PyQt5.QtWidgets import QHBoxLayout, QPushButton, QApplication, QWidget, QVBoxLayout, QFormLayout, \
    QLabel, QLineEdit, QMessageBox, QTabWidget, QComboBox, QCheckBox, QTextEdit, QCompleter
from PyQt5.QtCore import pyqtSlot, QStringListModel
from PyQt5 import QtGui, QtCore
from pymongo import MongoClient

import similarity.similarity_function_cn


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
        with(open(r'./generation/synonyms_tw.txt', 'r', encoding='utf-8')) as data:
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
            print(self.current_index)

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
        self.pos.addItems(['不知道', '地名', '動詞', '名詞'])

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
                    print(words)
                    return words
            else:
                return []

        if self.word1.text() != '' and self.word2.toPlainText() != '':
            synonym_of_word = find_synonym()
            self.all_synonym.update(self.word2.toPlainText().split(' '))
            for i in set(synonym_of_word) - set(self.word2.toPlainText().split(' ')):
                self.all_synonym.discard(i)
            self.model.setStringList(self.all_synonym)

            with open(r'./similarity/jieba_model/expend_dict.json', 'r', encoding='utf-8') as jsonFile:
                expend_word = json.load(jsonFile)

            for word in synonym_of_word:
                expend_word.pop(word, None)

            if self.current_index is not None:
                self.synonym_dict[self.current_index] = self.word2.toPlainText().split()
            else:
                self.synonym_dict.append(self.word2.toPlainText().split())
                self.current_index = len(self.synonym_dict) - 1

            shutil.copyfile(r'./similarity/jieba_model/dict.txt.big', r'./similarity/jieba_model/dict.txt')

            for word in self.word2.toPlainText().split():
                if self.pos.currentText() == "不知道":
                    expend_word[unicodedata.normalize('NFC', word)] = ''
                elif self.pos.currentText() == '地名':
                    expend_word[unicodedata.normalize('NFC', word)] = 'n'
                    with open(r'./data/place.txt', 'a', encoding='utf-8') as place_dic:
                        place_dic.write(word + '\n')
                elif self.pos.currentText() == '名詞':
                    expend_word[unicodedata.normalize('NFC', word)] = 'n'
                else:
                    expend_word[unicodedata.normalize('NFC', word)] = 'v'

            with open(r'./similarity/jieba_model/dict.txt', 'a', encoding='utf-8') as output:
                for word in expend_word:
                    output.write('{0} 100000000000000 {1}\n'.format(word, expend_word[word]))

            with open(r'./similarity/jieba_model/expend_dict.json', 'w', encoding='utf-8') as jsonFile:
                json.dump(expend_word, jsonFile, indent=4)

            with open(r'./generation/synonyms_tw.txt', 'w', encoding='utf-8') as output:
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
                with open(r'./similarity/jieba_model/expend_dict.json', 'r', encoding='utf-8') as jsonFile:
                    expend_word = json.load(jsonFile)

                for i in self.synonym_dict[self.current_index]:
                    self.all_synonym.discard(i)
                    expend_word.pop(i,None)
                self.model.setStringList(self.all_synonym)

                shutil.copyfile(r'./similarity/jieba_model/dict.txt.big', r'./similarity/jieba_model/dict.txt')

                with open(r'./similarity/jieba_model/dict.txt', 'a', encoding='utf-8') as output:
                    for word in expend_word:
                        output.write('{0} 100000000000000 {1}\n'.format(word, expend_word[word]))

                with open(r'./similarity/jieba_model/expend_dict.json', 'w', encoding='utf-8') as jsonFile:
                    json.dump(expend_word, jsonFile, indent=4)

                del self.synonym_dict[self.current_index]
                with open(r'./generation/synonyms_tw.txt', 'w', encoding='utf-8') as output:
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

        self.sentence_list = ComboBox(my_function=self.check_data_update)
        for row in self.collection.find():
            self.sentence_list.addItem(row['sentence'])
        self.sentence_list.currentIndexChanged.connect(self.show_selected_item)

        self.new_or_not = QCheckBox('新增句子')
        self.new_or_not.stateChanged.connect(self.state_changed)

        self.remove_btn = QPushButton('刪除句子')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        self.select_layout.addWidget(self.sentence_list)
        self.select_layout.addWidget(self.new_or_not)
        self.select_layout.addWidget(self.remove_btn)
        temp = self.collection.find_one({'uuid':0})
        self.sentence = QTextEdit()
        self.answer = QTextEdit()
        self.url = QLineEdit()
        self.sentence.setText(temp['sentence'])
        self.answer.setText(temp['answer'])
        self.url.setText(temp['url'])

        sentence_widget.addRow(QLabel('全部句子'), self.select_layout)
        sentence_widget.addRow(QLabel('欲編輯句子'), self.sentence)
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
    def show_selected_item(self):
        data = self.collection.find_one({'uuid': self.sentence_list.currentIndex()})
        self.sentence.setText(self.sentence_list.currentText())
        self.answer.setText(data['answer'])
        self.url.setText(data['url'])

    @pyqtSlot()
    def check_data_update(self):
        if self.collection.find().count() > self.sentence_list.count():
            for row in self.collection.find({'uuid': {'$gte': self.sentence_list.count()}}):
                self.sentence_list.addItem(row['sentence'])

    @pyqtSlot()
    def state_changed(self):
        self.sentence.clear()
        self.answer.clear()
        self.url.clear()
        if self.new_or_not.checkState():
            self.sentence_list.setDisabled(True)
        else:
            self.sentence_list.setDisabled(False)
            temp = self.collection.find_one({'uuid':self.sentence_list.currentIndex()})
            self.sentence.setText(temp['sentence'])
            self.answer.setText(temp['answer'])
            self.url.setText(temp['url'])

    @pyqtSlot()
    def remove_btn_method(self):
        if self.new_or_not.checkState():
            QMessageBox.information(self, "提醒", '請先勾去"新增句子"')

        else:
            result = QMessageBox.question(self, '警告', '確定要刪除"{0}"嗎?'.format(self.sentence_list.currentText()),
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)

            if result == QMessageBox.Yes:
                current_index = self.sentence_list.currentIndex()
                self.collection.remove({'uuid': current_index})

                for row in self.collection.find({'uuid': {'$gt': current_index}}):
                    row['uuid'] -= 1
                    self.collection.save(row)

                self.sentence_list.removeItem(current_index)

            else:
                pass

    @pyqtSlot()
    def save_btn_method(self):
        if self.new_or_not.checkState():
            data = {'uuid': self.collection.find().count(), 'sentence': self.sentence.toPlainText(),
                    'answer': self.answer.toPlainText(), 'url': self.url.text(),
                    'segmentation': '',
                    'pos': ''}
            self.collection.insert(data)
            self.sentence_list.addItem(self.sentence.toPlainText())
        else:
            data = self.collection.find_one({'uuid': self.sentence_list.currentIndex()})
            data['sentence'] = self.sentence.toPlainText()
            data['answer'] = self.answer.toPlainText()
            data['url'] = self.url.text()
            data['segmentation'] = similarity.similarity_function_cn.get_words(self.sentence.toPlainText())
            data['pos'] = ''
            self.collection.save(data)

            self.sentence_list.setItemText(self.sentence_list.currentIndex(), self.sentence.toPlainText())

        QMessageBox.information(self, "提醒", '已儲存"{}"'.format(self.sentence.toPlainText()))

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
        self.show_all_sentences = QCheckBox('包含已回答句子')
        self.show_all_sentences.stateChanged.connect(self.state_changed)
        self.sentences_id = []

        self.log_list = QComboBox()
        self.load_sentence()
        self.log_list.currentIndexChanged.connect(self.show_selected_item)

        self.remove_btn = QPushButton('刪除紀錄')
        self.remove_btn.clicked.connect(self.remove_btn_method)

        self.select_layout.addWidget(self.log_list)
        self.select_layout.addWidget(self.show_all_sentences)
        self.select_layout.addWidget(self.remove_btn)

        temp = self.collection_log.find_one({'answer':''})
        self.sentence = QTextEdit()
        # self.sentence.setText(str(temp['sentence']))
        self.answer = QTextEdit()

        sentence_widget.addRow(QLabel('無法回答問句'), self.select_layout)
        sentence_widget.addRow(QLabel('問句'), self.sentence)
        sentence_widget.addRow(QLabel('答案'), self.answer)

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
        data = self.collection_log.find_one({'_id': self.sentences_id[self.log_list.currentIndex()]})
        self.sentence.setText(self.log_list.currentText())
        self.answer.setText(data['answer'])

    @pyqtSlot()
    def state_changed(self):
        self.sentence.clear()
        self.answer.clear()
        self.load_sentence()

    @pyqtSlot()
    def remove_btn_method(self):
        if len(self.sentences_id) > 0:
            result = QMessageBox.question(self, '警告', '確定要刪除"{0}"嗎?'.format(self.log_list.currentText()),
                                          QMessageBox.Yes | QMessageBox.No,
                                          QMessageBox.No)

            if result == QMessageBox.Yes:
                self.remove_item_from_combobox()

            else:
                pass
        else:
            QMessageBox.information(self, '警告', '目前沒有句子')

    def remove_item_from_combobox(self):
        current_index = self.log_list.currentIndex()
        self.collection_log.remove({'_id': self.sentences_id[current_index]})
        del self.sentences_id[current_index]
        if self.log_list.count() == 1:
            self.log_list.setItemText(0, '')

        else:
            self.log_list.removeItem(current_index)

    @pyqtSlot()
    def save_btn_method(self):
        if len(self.sentences_id) > 0:
            data = {'uuid': self.collection_ori.find().count(), 'sentence': self.sentence.toPlainText(),
                    'answer': self.answer.toPlainText(), 'url': '',
                    'segmentation': '',
                    'pos': ''}
            self.collection_ori.insert(data)
            QMessageBox.information(self, '提醒', '已儲存"{}"'.format(self.sentence.toPlainText()))
            self.remove_item_from_combobox()

        else:
            QMessageBox.information(self, '警告', '目前沒有句子')

    @pyqtSlot()
    def cancel_btn_method(self):
        data = self.collection_log.find_one({'_id': self.sentences_id[self.log_list.currentIndex()]})
        self.sentence.setText(str(data['sentence']))
        self.answer.setText(str(data['answer']))


class QA_system_window(QTabWidget):
    def __init__(self, title, width=400, height=300):
        super().__init__()
        self.title = title
        self.width = width
        self.height = height
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.title)
        self.setMinimumSize(600, 450)
        self.resize(self.width, self.height)

        # self.addTab(dig_keyword(), '新增關鍵字')
        self.addTab(dig_similarity_word(), '編輯同義詞')
        self.addTab(dig_edit_sentence(), '編輯問句')
        self.addTab(dig_sentence_log(), '回答紀錄')

        # Show widget
        self.show()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    app.setFont(QtGui.QFont('', 12))
    main_window = QA_system_window('智慧 QA system')
    sys.exit(app.exec_())
