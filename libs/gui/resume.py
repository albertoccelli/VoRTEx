# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resume.ui'
#
# Created by: PyQt5 UI code generator 5.15.4
#
# WARNING: Any manual changes made to this file will be lost when pyuic5 is
# run again.  Do not edit this file unless you know what you are doing.


from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_Resume(object):
    def setupUi(self, Resume):
        Resume.setObjectName("Resume")
        Resume.resize(387, 449)
        Resume.setMaximumSize(QtCore.QSize(387, 449))
        self.horizontalLayout_2 = QtWidgets.QHBoxLayout(Resume)
        self.horizontalLayout_2.setObjectName("horizontalLayout_2")
        self.horizontalLayout = QtWidgets.QHBoxLayout()
        self.horizontalLayout.setObjectName("horizontalLayout")
        self.listWidget = QtWidgets.QListWidget(Resume)
        sizePolicy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Maximum, QtWidgets.QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.listWidget.sizePolicy().hasHeightForWidth())
        self.listWidget.setSizePolicy(sizePolicy)
        self.listWidget.setObjectName("listWidget")
        self.horizontalLayout.addWidget(self.listWidget)
        spacerItem = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.horizontalLayout.addItem(spacerItem)
        self.verticalLayout = QtWidgets.QVBoxLayout()
        self.verticalLayout.setObjectName("verticalLayout")
        self.resumeButton = QtWidgets.QPushButton(Resume)
        self.resumeButton.setMinimumSize(QtCore.QSize(101, 23))
        self.resumeButton.setMaximumSize(QtCore.QSize(101, 23))
        font = QtGui.QFont()
        font.setBold(True)
        font.setWeight(75)
        self.resumeButton.setFont(font)
        self.resumeButton.setObjectName("resumeButton")
        self.verticalLayout.addWidget(self.resumeButton)
        self.cancelButton_2 = QtWidgets.QPushButton(Resume)
        self.cancelButton_2.setMinimumSize(QtCore.QSize(101, 23))
        self.cancelButton_2.setMaximumSize(QtCore.QSize(101, 23))
        self.cancelButton_2.setObjectName("cancelButton_2")
        self.verticalLayout.addWidget(self.cancelButton_2)
        self.newButton = QtWidgets.QPushButton(Resume)
        self.newButton.setMinimumSize(QtCore.QSize(101, 23))
        self.newButton.setMaximumSize(QtCore.QSize(101, 23))
        self.newButton.setObjectName("newButton")
        self.verticalLayout.addWidget(self.newButton)
        self.cancelButton = QtWidgets.QPushButton(Resume)
        self.cancelButton.setMinimumSize(QtCore.QSize(101, 23))
        self.cancelButton.setMaximumSize(QtCore.QSize(101, 23))
        self.cancelButton.setObjectName("cancelButton")
        self.verticalLayout.addWidget(self.cancelButton)
        self.textBrowser = QtWidgets.QTextBrowser(Resume)
        self.textBrowser.setMinimumSize(QtCore.QSize(101, 0))
        self.textBrowser.setMaximumSize(QtCore.QSize(101, 16777215))
        self.textBrowser.setObjectName("textBrowser")
        self.verticalLayout.addWidget(self.textBrowser)
        self.horizontalLayout.addLayout(self.verticalLayout)
        self.horizontalLayout_2.addLayout(self.horizontalLayout)

        self.retranslateUi(Resume)
        QtCore.QMetaObject.connectSlotsByName(Resume)

    def retranslateUi(self, Resume):
        _translate = QtCore.QCoreApplication.translate
        Resume.setWindowTitle(_translate("Resume", "Dialog"))
        self.resumeButton.setText(_translate("Resume", "Resume"))
        self.cancelButton_2.setText(_translate("Resume", "Delete selected"))
        self.newButton.setText(_translate("Resume", "Start new"))
        self.cancelButton.setText(_translate("Resume", "Cancel"))
        self.textBrowser.setHtml(_translate("Resume", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'MS Shell Dlg 2\'; font-size:8.25pt; font-weight:400; font-style:normal;\">\n"
"<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    Resume = QtWidgets.QDialog()
    ui = Ui_Resume()
    ui.setupUi(Resume)
    Resume.show()
    sys.exit(app.exec_())
