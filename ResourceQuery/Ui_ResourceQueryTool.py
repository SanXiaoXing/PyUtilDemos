# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'resource_query_tool.ui'
#
# Created by: Manual conversion similar to pyuic5 output (keep in repo, not auto-generated)
# WARNING: Changes here will persist. If later you use pyuic5, regenerate accordingly.

from PyQt5 import QtCore, QtGui, QtWidgets


class Ui_ResourceQueryTool(object):
    def setupUi(self, ResourceQueryTool):
        ResourceQueryTool.setObjectName("ResourceQueryTool")
        ResourceQueryTool.resize(500, 650)
        self.main_layout = QtWidgets.QVBoxLayout(ResourceQueryTool)
        self.main_layout.setObjectName("main_layout")

        self.filter_layout = QtWidgets.QHBoxLayout()
        self.filter_layout.setObjectName("filter_layout")
        self.label_info = QtWidgets.QLabel(ResourceQueryTool)
        self.label_info.setObjectName("label_info")
        self.filter_layout.addWidget(self.label_info)
        self.edit_search = QtWidgets.QLineEdit(ResourceQueryTool)
        self.edit_search.setObjectName("edit_search")
        self.filter_layout.addWidget(self.edit_search, 2)
        self.btn_choose = QtWidgets.QPushButton(ResourceQueryTool)
        self.btn_choose.setObjectName("btn_choose")
        self.filter_layout.addWidget(self.btn_choose)
        self.btn_reset = QtWidgets.QPushButton(ResourceQueryTool)
        self.btn_reset.setObjectName("btn_reset")
        self.filter_layout.addWidget(self.btn_reset)
        self.btn_reload = QtWidgets.QPushButton(ResourceQueryTool)
        self.btn_reload.setObjectName("btn_reload")
        self.filter_layout.addWidget(self.btn_reload)
        self.main_layout.addLayout(self.filter_layout)

<<<<<<< HEAD
        self.dim_layout = QtWidgets.QGridLayout()
        self.dim_layout.setObjectName("dim_layout")
        self.main_layout.addLayout(self.dim_layout)

=======
>>>>>>> main
        self.table = QtWidgets.QTableWidget(ResourceQueryTool)
        self.table.setObjectName("table")
        self.table.setEditTriggers(QtWidgets.QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)
        self.main_layout.addWidget(self.table)

        self.bottom_layout = QtWidgets.QHBoxLayout()
        self.bottom_layout.setObjectName("bottom_layout")
        self.label_status = QtWidgets.QLabel(ResourceQueryTool)
        self.label_status.setObjectName("label_status")
        self.bottom_layout.addWidget(self.label_status)
        self.bottom_spacer = QtWidgets.QSpacerItem(40, 20, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Minimum)
        self.bottom_layout.addItem(self.bottom_spacer)
        self.main_layout.addLayout(self.bottom_layout)

        self.retranslateUi(ResourceQueryTool)
        QtCore.QMetaObject.connectSlotsByName(ResourceQueryTool)

    def retranslateUi(self, ResourceQueryTool):
        _translate = QtCore.QCoreApplication.translate
        ResourceQueryTool.setWindowTitle(_translate("ResourceQueryTool", "资源索引查询"))
        self.label_info.setText(_translate("ResourceQueryTool", "筛选内容："))
        self.edit_search.setPlaceholderText(_translate("ResourceQueryTool", "输入关键字进行搜索"))
        self.btn_choose.setText(_translate("ResourceQueryTool", "选择Excel"))
        self.btn_reset.setText(_translate("ResourceQueryTool", "重置"))
        self.btn_reload.setText(_translate("ResourceQueryTool", "重新加载"))