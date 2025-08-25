#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
@Project ：631_ZHCLTest 
@File    ：XmlEditor.py
@Author  ：SanXiaoXing
@Date    ：2025/8/13
@Description: XML编辑器主逻辑 - 支持多层级嵌套结构，优化复用性
"""

import sys
import os
import re
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import Dict, Optional, Any
from PyQt5.QtWidgets import (
    QWidget, QApplication, QHBoxLayout, QLineEdit, QComboBox, 
    QPushButton, QMessageBox, QFileDialog, QTextEdit, QDialog,
    QVBoxLayout, QLabel, QSpacerItem, QSizePolicy, QTreeWidget,
    QTreeWidgetItem, QFrame, QSplitter, QHeaderView, QCheckBox,
    QProgressBar
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer
from PyQt5.QtGui import QFont, QIcon

try:
    from .UI_xml_editor import Ui_XmlEditor
except ImportError:
    # 兼容直接运行本文件的场景
    from UI_xml_editor import Ui_XmlEditor


# 配置常量
class XmlEditorConfig:
    """XML编辑器配置类

    包含UI、字体、尺寸等配置信息
    """

    # UI配置
    TREE_HEADERS = ["标签名", "文本内容", "属性", "操作"]
    COLUMN_WIDTHS = [150, 150, None, 100]  # None表示自适应
    SPLITTER_SIZES = [400, 400]

    # 字体配置
    TITLE_FONT = QFont("Arial", 10, QFont.Bold)
    PREVIEW_FONT = QFont("Consolas", 9)
    DIALOG_TITLE_FONT = QFont("Arial", 12, QFont.Bold)

    # 控件尺寸
    WIDGET_HEIGHT = 24
    BUTTON_SIZE = (22, 22)
    ROW_HEIGHT = 28

    # 文本配置
    PLACEHOLDERS = {
        'tag': "标签名（如：book, title）",
        'text': "文本内容",
        'attr': "属性（如：id=\"1\" name=\"test\"）"
    }

    # 按钮配置
    BUTTONS = {
        'add': {'text': '+', 'tooltip': '添加子元素'},
        'add_attr': {'text': 'A+', 'tooltip': '添加属性'},
        'delete': {'text': '×', 'tooltip': '删除'}
    }


class XmlUtils:
    """XML工具类 - 提供通用的XML处理功能"""

    @staticmethod
    def format_xml(element: ET.Element, indent: str = "  ") -> str:
        """格式化XML元素为字符串

        Args:
            element: 要格式化的XML元素
            indent: 缩进字符串，默认为两个空格

        Returns:
            str: 格式化后的XML字符串

        Raises:
            Exception: XML格式化过程中可能出现的异常
        """
        try:
            if element is None:
                return "<!-- 没有有效的XML数据 -->"

            rough_string = ET.tostring(element, encoding='unicode')
            reparsed = minidom.parseString(rough_string)
            formatted_xml = reparsed.toprettyxml(indent=indent)
            # 移除空行
            lines = [line for line in formatted_xml.split('\n') if line.strip()]
            # 强制声明 UTF-8 编码
            if lines:
                if lines[0].startswith('<?xml'):
                    lines[0] = '<?xml version="1.0" encoding="UTF-8"?>'
                else:
                    lines.insert(0, '<?xml version="1.0" encoding="UTF-8"?>')
            return '\n'.join(lines)
        except Exception as e:
            return f"<!-- XML格式化错误: {str(e)} -->"

    @staticmethod
    def save_xml_to_file(element: ET.Element, file_path: str) -> None:
        """保存XML元素到文件

        Args:
            element: 要保存的XML元素
            file_path: 保存文件的路径

        Raises:
            IOError: 文件写入过程中可能出现的异常
        """
        formatted_xml = XmlUtils.format_xml(element)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_xml)


class AttributeParser:
    """属性解析器 - 处理XML属性的解析和格式化"""

    ATTR_PATTERN = re.compile(r'(\w+)=(["\'])([^"\']*)\2')

    @classmethod
    def parse_from_text(cls, text: str) -> Dict[str, str]:
        """从文本解析属性

        Args:
            text: 包含属性的文本字符串，如 'id="1" name="test"'

        Returns:
            Dict[str, str]: 解析后的属性字典
        """
        attributes = {}
        if not text.strip():
            return attributes

        matches = cls.ATTR_PATTERN.findall(text)
        for match in matches:
            attr_name, quote, attr_value = match
            attributes[attr_name] = attr_value

        return attributes

    @staticmethod
    def format_to_text(attributes: Dict[str, str]) -> str:
        """将属性字典格式化为文本

        Args:
            attributes: 属性字典

        Returns:
            str: 格式化后的属性文本
        """
        if not attributes:
            return ""
        return ' '.join([f'{k}="{v}"' for k, v in attributes.items()])


class BasePreviewDialog(QDialog):
    """通用预览对话框基类"""

    def __init__(self, title: str, content: str, parent=None):
        """初始化预览对话框

        Args:
            title: 对话框标题
            content: 显示的内容
            parent: 父级窗口
        """
        super().__init__(parent)
        self.title = title
        self.content = content
        self.setup_ui()

    def setup_ui(self):
        """设置UI界面"""
        self.setWindowTitle(self.title)
        self.setModal(True)
        self.resize(600, 500)

        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel(self.title)
        title_label.setFont(XmlEditorConfig.DIALOG_TITLE_FONT)
        layout.addWidget(title_label)

        # 内容显示
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)
        self.text_edit.setFont(QFont("Consolas", 10))
        self.text_edit.setPlainText(self.content)
        layout.addWidget(self.text_edit)

        # 按钮布局
        self._setup_buttons(layout)

    def _setup_buttons(self, layout):
        """设置按钮

        Args:
            layout: 父级布局
        """
        button_layout = QHBoxLayout()

        # 复制按钮
        copy_btn = QPushButton("复制到剪贴板")
        copy_btn.clicked.connect(self.copy_to_clipboard)
        button_layout.addWidget(copy_btn)

        # 关闭按钮
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.close)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)

    def copy_to_clipboard(self):
        """复制到剪贴板"""
        clipboard = QApplication.clipboard()
        clipboard.setText(self.text_edit.toPlainText())
        QMessageBox.information(self, "成功", "内容已复制到剪贴板！")


# 新增：单独添加属性的对话框
class AddAttributeDialog(QDialog):
    """添加属性对话框，输入属性名与属性值"""
    def __init__(self, parent=None):
        """初始化添加属性对话框

        Args:
            parent: 父级窗口
        """
        super().__init__(parent)
        self.setWindowTitle("添加属性")
        self.setModal(True)
        self.resize(360, 160)
        self._setup_ui()

    def _setup_ui(self):
        """设置UI界面"""
        layout = QVBoxLayout(self)

        # 标题
        title = QLabel("请输入要添加的属性名与属性值")
        title.setFont(XmlEditorConfig.TITLE_FONT)
        layout.addWidget(title)

        # 输入区域
        from PyQt5.QtWidgets import QFormLayout
        form = QFormLayout()
        self.name_edit = QLineEdit()
        self.name_edit.setPlaceholderText("属性名（仅字母数字与下划线）")
        self.value_edit = QLineEdit()
        self.value_edit.setPlaceholderText("属性值")
        form.addRow("属性名：", self.name_edit)
        form.addRow("属性值：", self.value_edit)
        layout.addLayout(form)

        # 按钮区
        btns = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        btns.addStretch(1)
        btns.addWidget(self.ok_btn)
        btns.addWidget(self.cancel_btn)
        layout.addLayout(btns)

        self.ok_btn.clicked.connect(self._on_ok)
        self.cancel_btn.clicked.connect(self.reject)

    def _on_ok(self):
        """确定按钮点击事件"""
        name = self.name_edit.text().strip()
        value = self.value_edit.text()
        if not name:
            QMessageBox.warning(self, "提示", "属性名不能为空！")
            return
        # 仅允许与解析器一致的命名（\w）
        if not re.match(r'^\w+$', name):
            QMessageBox.warning(self, "提示", "属性名仅支持字母、数字与下划线！")
            return
        self.accept()

    def get_data(self):
        """获取输入的属性数据

        Returns:
            tuple: (属性名, 属性值)
        """
        return self.name_edit.text().strip(), self.value_edit.text()


class XmlTreeWidget(QTreeWidget):
    """支持多层级XML结构的树形编辑器"""

    itemChanged = pyqtSignal()

    def __init__(self, parent=None):
        """初始化XML树形控件

        Args:
            parent: 父级窗口
        """
        super().__init__(parent)
        self.config = XmlEditorConfig()
        self.setup_tree()

    def setup_tree(self):
        """设置树形控件"""
        # 设置表头
        self.setHeaderLabels(self.config.TREE_HEADERS)

        # 基本设置
        self.setAlternatingRowColors(True)
        self.setRootIsDecorated(True)
        self.setIndentation(20)
        self.setAnimated(True)
        self.setExpandsOnDoubleClick(True)
        self.setItemsExpandable(True)
        self.setUniformRowHeights(False)

        # 右键菜单
        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.open_context_menu)

        # 设置列宽
        self._setup_columns()

        # 添加根节点
        self.add_root_item()

    def _setup_columns(self):
        """设置列宽和调整模式"""
        header = self.header()
        widths = self.config.COLUMN_WIDTHS

        for i, width in enumerate(widths):
            if width is None:
                header.setSectionResizeMode(i, QHeaderView.Stretch)
            elif i == len(widths) - 1:  # 最后一列固定
                header.setSectionResizeMode(i, QHeaderView.Fixed)
                header.resizeSection(i, width)
            else:
                header.setSectionResizeMode(i, QHeaderView.Interactive)
                header.resizeSection(i, width)

    def showEvent(self, event):
        """展示事件处理

        Args:
            event: 展示事件
        """
        super().showEvent(event)
        # 展示时展开前两层
        self.expandToDepth(1)

    def open_context_menu(self, position):
        """打开右键菜单

        Args:
            position: 菜单位置
        """
        from PyQt5.QtWidgets import QMenu
        menu = QMenu(self)
        expand_all = menu.addAction("展开全部")
        collapse_all = menu.addAction("折叠全部")

        action = menu.exec_(self.mapToGlobal(position))
        if action == expand_all:
            self.expandAll()
        elif action == collapse_all:
            self.collapseAll()

    def add_root_item(self):
        """添加根节点"""
        root_item = XmlTreeItem(self, tag_name="root")
        self.addTopLevelItem(root_item)
        self.expandItem(root_item)

    def get_xml_data(self):
        """获取完整的XML数据

        Returns:
            ET.Element or None: XML根元素或None
        """
        if self.topLevelItemCount() == 0:
            return None

        root_item = self.topLevelItem(0)
        if isinstance(root_item, XmlTreeItem):
            return root_item.to_element()
        return None


class XmlTreeItem(QTreeWidgetItem):
    """XML树形项"""

    def __init__(self, parent, tag_name="", text_content="", attributes=None):
        """初始化XML树形项

        Args:
            parent: 父级项或树控件
            tag_name: 标签名
            text_content: 文本内容
            attributes: 属性字典
        """
        super().__init__(parent)
        self.tag_name = tag_name
        self.text_content = text_content
        self.attributes = attributes or {}
        self.config = XmlEditorConfig()

        self.setup_item()

    def setup_item(self):
        """设置树形项"""
        # 创建编辑控件
        self._create_edit_widgets()

        # 创建操作按钮
        self._create_button_widgets()

        # 延迟设置到树形控件
        if self.treeWidget():
            self._set_widgets()
        else:
            from PyQt5.QtCore import QTimer
            QTimer.singleShot(10, self._set_widgets)

    def _create_edit_widgets(self):
        """创建编辑控件"""
        # 标签名编辑
        self.tag_edit = self._create_line_edit(
            str(self.tag_name),
            self.config.PLACEHOLDERS['tag'],
            self.on_tag_changed
        )

        # 文本内容编辑
        self.text_edit = self._create_line_edit(
            str(self.text_content),
            self.config.PLACEHOLDERS['text'],
            self.on_text_changed
        )

        # 属性编辑
        self.attr_edit = self._create_line_edit(
            "",
            self.config.PLACEHOLDERS['attr'],
            self.on_attributes_changed
        )
        self.update_attributes_display()

    def _create_line_edit(self, text: str, placeholder: str, callback) -> QLineEdit:
        """创建标准化的行编辑控件

        Args:
            text: 初始文本
            placeholder: 占位符文本
            callback: 文本改变时的回调函数

        Returns:
            QLineEdit: 创建的行编辑控件
        """
        edit = QLineEdit()
        edit.setText(text)
        edit.setPlaceholderText(placeholder)
        edit.setMaximumHeight(self.config.WIDGET_HEIGHT)
        edit.textChanged.connect(callback)
        edit.textChanged.connect(self.emit_tree_change)
        return edit

    def _create_button_widgets(self):
        """创建操作按钮"""
        self.button_widget = QWidget()
        self.button_widget.setMaximumHeight(self.config.ROW_HEIGHT)

        button_layout = QHBoxLayout(self.button_widget)
        button_layout.setContentsMargins(2, 2, 2, 2)
        button_layout.setSpacing(2)

        # 添加子元素按钮
        add_config = self.config.BUTTONS['add']
        self.add_btn = self._create_button(
            add_config['text'],
            add_config['tooltip'],
            self.add_child_item
        )

        # 新增：添加属性按钮
        add_attr_cfg = self.config.BUTTONS['add_attr']
        self.add_attr_btn = self._create_button(
            add_attr_cfg['text'],
            add_attr_cfg['tooltip'],
            self.add_attribute
        )

        # 删除按钮
        delete_config = self.config.BUTTONS['delete']
        self.delete_btn = self._create_button(
            delete_config['text'],
            delete_config['tooltip'],
            self.delete_item
        )

        button_layout.addWidget(self.add_btn)
        button_layout.addWidget(self.add_attr_btn)
        button_layout.addWidget(self.delete_btn)
        button_layout.addStretch()

    def _create_button(self, text: str, tooltip: str, callback) -> QPushButton:
        """创建标准化的按钮

        Args:
            text: 按钮文本
            tooltip: 提示文本
            callback: 点击回调函数

        Returns:
            QPushButton: 创建的按钮
        """
        btn = QPushButton(text)
        btn.setFixedSize(*self.config.BUTTON_SIZE)
        btn.setToolTip(tooltip)
        btn.clicked.connect(callback)
        return btn

    def _set_widgets(self):
        """设置小部件到树形控件"""
        tree = self.treeWidget()
        if not tree:
            return

        # 设置控件高度
        widgets = [self.tag_edit, self.text_edit, self.attr_edit]
        for widget in widgets:
            widget.setFixedHeight(self.config.WIDGET_HEIGHT)

        # 设置到树形控件
        tree.setItemWidget(self, 0, self.tag_edit)
        tree.setItemWidget(self, 1, self.text_edit)
        tree.setItemWidget(self, 2, self.attr_edit)
        tree.setItemWidget(self, 3, self.button_widget)

        # 设置行高
        row_size = QSize(0, self.config.ROW_HEIGHT)
        for i in range(4):
            self.setSizeHint(i, row_size)

    def emit_tree_change(self):
        """向树发出更改信号以刷新预览"""
        tree = self.treeWidget()
        if tree and hasattr(tree, 'itemChanged'):
            tree.itemChanged.emit()

    def on_tag_changed(self, text):
        """标签名改变时的处理

        Args:
            text: 新的标签名
        """
        self.tag_name = text

    def on_text_changed(self, text):
        """文本内容改变时的处理

        Args:
            text: 新的文本内容
        """
        self.text_content = text

    def on_attributes_changed(self, text):
        """属性改变时的处理

        Args:
            text: 属性文本
        """
        self.attributes = AttributeParser.parse_from_text(text)

    def update_attributes_display(self):
        """更新属性显示"""
        attr_text = AttributeParser.format_to_text(self.attributes)
        self.attr_edit.setText(attr_text)

    # 新增：单独添加属性逻辑
    def add_attribute(self):
        """添加属性"""
        dialog = AddAttributeDialog(self.treeWidget())
        if dialog.exec_() == QDialog.Accepted:
            name, value = dialog.get_data()
            if not name:
                return
            # 若属性已存在，询问是否覆盖
            if name in self.attributes:
                reply = QMessageBox.question(
                    self.treeWidget(), "确认", f"属性 '{name}' 已存在，是否覆盖？",
                    QMessageBox.Yes | QMessageBox.No, QMessageBox.No
                )
                if reply != QMessageBox.Yes:
                    return
            self.attributes[name] = value
            # 更新显示与预览
            self.update_attributes_display()
            self.emit_tree_change()

    def add_child_item(self):
        """添加子元素"""
        child_item = XmlTreeItem(self, tag_name=f"element{self.childCount() + 1}")
        self.addChild(child_item)
        self.setExpanded(True)

        # 触发更新信号
        if hasattr(self.treeWidget(), 'itemChanged'):
            self.treeWidget().itemChanged.emit()

    def delete_item(self):
        """删除当前项"""
        parent = self.parent()
        if parent:
            parent.removeChild(self)
        else:
            # 根项不能删除，但可以清空
            while self.childCount() > 0:
                self.removeChild(self.child(0))

        # 触发更新信号
        tree = self.treeWidget()
        if tree and hasattr(tree, 'itemChanged'):
            tree.itemChanged.emit()

    def to_element(self):
        """转换为XML元素

        Returns:
            ET.Element or None: 转换后的XML元素或None
        """
        if not self.tag_name:
            return None

        element = ET.Element(self.tag_name)

        # 设置属性
        for attr_name, attr_value in self.attributes.items():
            element.set(attr_name, attr_value)

        # 设置文本内容
        if self.text_content and self.childCount() == 0:
            element.text = self.text_content

        # 添加子元素
        for i in range(self.childCount()):
            child = self.child(i)
            if isinstance(child, XmlTreeItem):
                child_element = child.to_element()
                if child_element is not None:
                    element.append(child_element)

        return element

    def from_element(self, element):
        """从XML元素加载数据

        Args:
            element: 要加载的XML元素
        """
        self.tag_name = element.tag
        self.tag_edit.setText(self.tag_name)

        # 加载属性
        self.attributes = dict(element.attrib)
        self.update_attributes_display()

        # 加载文本内容
        if element.text and element.text.strip():
            self.text_content = element.text.strip()
            self.text_edit.setText(self.text_content)

        # 清空现有子项
        while self.childCount() > 0:
            self.removeChild(self.child(0))

        # 加载子元素
        for child_element in element:
            child_item = XmlTreeItem(self)
            child_item.from_element(child_element)
            self.addChild(child_item)

        self.setExpanded(True)


class XmlPreviewDialog(BasePreviewDialog):
    """XML预览对话框"""

    def __init__(self, xml_element, parent=None):
        """初始化XML预览对话框

        Args:
            xml_element: 要预览的XML元素
            parent: 父级窗口
        """
        content = XmlUtils.format_xml(xml_element)
        super().__init__("XML预览", content, parent)


class XmlEditor(QWidget):
    """XML编辑器主类 - 支持多层级结构"""

    def __init__(self, parent=None):
        """初始化XML编辑器

        Args:
            parent: 父级窗口
        """
        super().__init__(parent)
        self.ui = Ui_XmlEditor()
        self.ui.setupUi(self)
        self.config = XmlEditorConfig()

        # 异步加载相关属性
        self.loading_timer = QTimer()
        self.loading_queue = []
        self.current_loading_item = None
        self.total_elements = 0
        self.processed_elements = 0

        self.setup_tree_editor()
        self.setup_connections()
        self.setup_async_loading()

    def setup_tree_editor(self):
        """设置树形编辑器"""
        # 移除原有的滚动区域，替换为分割器
        self.ui.verticalLayout.removeWidget(self.ui.scrollArea)
        self.ui.scrollArea.setParent(None)

        # 创建分割器
        splitter = QSplitter(Qt.Horizontal)

        # 左侧：树形编辑器
        left_widget = self._create_tree_widget()

        # 右侧：实时预览
        right_widget = self._create_preview_widget()

        # 添加到分割器
        splitter.addWidget(left_widget)
        splitter.addWidget(right_widget)
        splitter.setSizes(self.config.SPLITTER_SIZES)

        # 添加到主布局
        self.ui.verticalLayout.insertWidget(1, splitter)

        # 初始更新预览
        self.update_preview()

    def _create_tree_widget(self) -> QWidget:
        """创建树形编辑器部件

        Returns:
            QWidget: 树形编辑器部件
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 树形编辑器标题
        title = QLabel("XML结构编辑器")
        title.setFont(self.config.TITLE_FONT)
        layout.addWidget(title)

        # 创建树形控件
        self.xml_tree = XmlTreeWidget()
        self.xml_tree.itemChanged.connect(self.on_tree_changed)
        layout.addWidget(self.xml_tree)

        return widget

    def _create_preview_widget(self) -> QWidget:
        """创建预览部件

        Returns:
            QWidget: 预览部件
        """
        widget = QWidget()
        layout = QVBoxLayout(widget)

        # 预览标题
        title = QLabel("实时预览")
        title.setFont(self.config.TITLE_FONT)
        layout.addWidget(title)

        # 添加进度条和状态标签
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)

        self.status_label = QLabel("")
        self.status_label.setVisible(False)
        layout.addWidget(self.status_label)

        # 预览文本框
        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setFont(self.config.PREVIEW_FONT)
        layout.addWidget(self.preview_text)

        return widget

    def setup_connections(self):
        """设置信号连接"""
        self.ui.btn_add_element.clicked.connect(self.add_root_element)
        self.ui.btn_clear_all.clicked.connect(self.clear_all_elements)
        self.ui.btn_preview.clicked.connect(self.preview_xml)
        self.ui.btn_download.clicked.connect(self.download_xml)

        # 新增：加载XML按钮
        self.btn_load = QPushButton("加载XML")
        # 插入到顶部工具栏，在"添加元素"按钮之前
        try:
            self.ui.horizontalLayout_top.insertWidget(2, self.btn_load)
        except Exception:
            # 如果插入失败则追加
            self.ui.horizontalLayout_top.addWidget(self.btn_load)
        self.btn_load.clicked.connect(self.open_xml_file)

        # 修改按钮文本
        self.ui.btn_add_element.setText("添加根级元素")

    def setup_async_loading(self):
        """设置异步加载机制"""
        self.loading_timer.timeout.connect(self.process_loading_batch)
        self.loading_timer.setSingleShot(False)

    def open_xml_file(self):
        """打开并加载XML文件"""
        try:
            # 选择文件
            file_path, _ = QFileDialog.getOpenFileName(
                self, "选择XML文件", "", "XML文件 (*.xml);;所有文件 (*)"
            )

            if not file_path:
                return

            # 读取文件内容
            try:
                # 优先尝试UTF-8编码
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except UnicodeDecodeError:
                # 如果UTF-8失败，尝试其他编码
                try:
                    with open(file_path, 'r', encoding='gbk') as f:
                        content = f.read()
                except UnicodeDecodeError:
                    with open(file_path, 'r', encoding='latin-1') as f:
                        content = f.read()

            # 解析XML内容
            root = ET.fromstring(content)

            # 使用异步加载机制
            self.start_async_loading(root)

        except ET.ParseError as e:
            QMessageBox.critical(self, "XML解析错误", f"XML文件格式错误: {str(e)}")
        except FileNotFoundError:
            QMessageBox.critical(self, "文件错误", "找不到指定的文件")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"加载XML文件时发生错误: {str(e)}")

    def start_async_loading(self, root_element):
        """开始异步加载XML数据

        Args:
            root_element: 要加载的根XML元素
        """
        try:
            # 停止之前的加载
            if self.loading_timer.isActive():
                self.loading_timer.stop()

            # 清空现有数据
            self.xml_tree.clear()
            self.xml_tree.add_root_item()

            # 计算总元素数量
            self.total_elements = self._count_elements(root_element)
            self.processed_elements = 0

            # 准备加载队列
            self.loading_queue = []
            root_item = self.xml_tree.topLevelItem(0)
            if isinstance(root_item, XmlTreeItem):
                self._prepare_loading_queue(root_element, root_item)

            # 显示进度条和状态
            self.progress_bar.setVisible(True)
            self.progress_bar.setMaximum(self.total_elements)
            self.progress_bar.setValue(0)
            self.status_label.setVisible(True)
            self.status_label.setText(f"正在加载XML文件... (0/{self.total_elements})")

            # 禁用加载按钮
            self.btn_load.setEnabled(False)

            # 开始定时器
            self.loading_timer.start(10)  # 每10ms处理一批

        except Exception as e:
            QMessageBox.critical(self, "错误", f"准备加载时发生错误：{str(e)}")
            self._finish_loading()

    def _count_elements(self, element):
        """递归计算XML元素总数

        Args:
            element: 要计算的XML元素

        Returns:
            int: 元素总数
        """
        count = 1
        for child in element:
            count += self._count_elements(child)
        return count

    def _prepare_loading_queue(self, xml_element, tree_item):
        """准备加载队列

        Args:
            xml_element: 要加载的XML元素
            tree_item: 对应的树形项
        """
        # 添加当前元素到队列
        self.loading_queue.append((xml_element, tree_item, 'self'))

        # 添加子元素到队列
        for child_element in xml_element:
            child_item = XmlTreeItem(tree_item)
            tree_item.addChild(child_item)
            self.loading_queue.append((child_element, child_item, 'child'))
            # 递归添加子元素的子元素
            self._prepare_loading_queue(child_element, child_item)

    def process_loading_batch(self):
        """处理一批加载任务"""
        batch_size = 5  # 每批处理5个元素
        processed_in_batch = 0

        while self.loading_queue and processed_in_batch < batch_size:
            xml_element, tree_item, load_type = self.loading_queue.pop(0)

            try:
                if load_type == 'self':
                    # 加载元素自身的属性和文本
                    tree_item.tag_name = xml_element.tag
                    tree_item.tag_edit.setText(tree_item.tag_name)

                    # 加载属性
                    tree_item.attributes = dict(xml_element.attrib)
                    tree_item.update_attributes_display()

                    # 加载文本内容
                    if xml_element.text and xml_element.text.strip():
                        tree_item.text_content = xml_element.text.strip()
                        tree_item.text_edit.setText(tree_item.text_content)

                self.processed_elements += 1
                processed_in_batch += 1

                # 更新进度
                self.progress_bar.setValue(self.processed_elements)
                self.status_label.setText(
                    f"正在加载XML文件... ({self.processed_elements}/{self.total_elements}) - {xml_element.tag}"
                )

            except Exception as e:
                print(f"加载元素时出错: {e}")
                self.processed_elements += 1

        # 检查是否完成
        if not self.loading_queue:
            self._finish_loading()

    def _finish_loading(self):
        """完成加载"""
        self.loading_timer.stop()
        self.progress_bar.setVisible(False)
        self.status_label.setVisible(False)
        self.btn_load.setEnabled(True)

        # 展开根节点
        if self.xml_tree.topLevelItemCount() > 0:
            root_item = self.xml_tree.topLevelItem(0)
            self.xml_tree.expandItem(root_item)

        # 更新预览
        self.update_preview()

        QMessageBox.information(self, "成功", f"XML文件加载完成！共处理 {self.processed_elements} 个元素。")

    def on_tree_changed(self):
        """树形结构改变时更新预览"""
        self.update_preview()

    def update_preview(self):
        """更新实时预览"""
        xml_element = self.xml_tree.get_xml_data()
        formatted_xml = XmlUtils.format_xml(xml_element)
        self.preview_text.setPlainText(formatted_xml)

    def add_root_element(self):
        """添加根级元素"""
        if self.xml_tree.topLevelItemCount() > 0:
            root_item = self.xml_tree.topLevelItem(0)
            if isinstance(root_item, XmlTreeItem):
                root_item.add_child_item()

    def clear_all_elements(self):
        """清空所有元素"""
        reply = QMessageBox.question(
            self, "确认", "确定要清空所有元素吗？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.xml_tree.clear()
            self.xml_tree.add_root_item()
            self.update_preview()

    def get_xml_data(self):
        """获取当前的XML数据

        Returns:
            ET.Element or None: 当前XML数据或None
        """
        return self.xml_tree.get_xml_data()

    def load_xml_data(self, xml_element):
        """加载XML数据 - 已弃用，使用start_async_loading替代

        Args:
            xml_element: 要加载的XML元素
        """
        # 重定向到异步加载方法
        self.start_async_loading(xml_element)

    def preview_xml(self):
        """预览XML"""
        try:
            xml_element = self.get_xml_data()
            if xml_element is None:
                QMessageBox.information(self, "提示", "没有有效的XML数据可预览！")
                return

            preview_dialog = XmlPreviewDialog(xml_element, self)
            preview_dialog.exec_()

        except Exception as e:
            QMessageBox.critical(self, "错误", f"预览XML时发生错误: {str(e)}")

    def download_xml(self):
        """下载XML文件"""
        try:
            xml_element = self.get_xml_data()
            if xml_element is None:
                QMessageBox.information(self, "提示", "没有有效的XML数据可下载！")
                return

            # 选择保存路径
            file_path, _ = QFileDialog.getSaveFileName(
                self, "保存XML文件", "data.xml", "XML文件 (*.xml)"
            )

            if file_path:
                XmlUtils.save_xml_to_file(xml_element, file_path)
                QMessageBox.information(self, "成功", f"XML文件已保存到: {file_path}")

        except Exception as e:
            QMessageBox.critical(self, "错误", f"保存XML文件时发生错误: {str(e)}")


def main():
    """主函数，用于测试"""
    app = QApplication(sys.argv)

    editor = XmlEditor()
    editor.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
