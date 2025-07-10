#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
QFluentWidgets风格QSS样式演示
兼容Python 3.8.10+

这个演示展示了如何使用更新后的Fluent Design风格QSS样式文件。
样式文件位置: ./style.qss
"""

import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLineEdit, QComboBox, QCheckBox, QRadioButton,
    QSlider, QProgressBar, QTableWidget, QTableWidgetItem,
    QTreeWidget, QTreeWidgetItem, QPlainTextEdit, QGroupBox,
    QTabWidget, QLabel, QMenuBar, QMenu, QStatusBar
)
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QFont


class FluentDemoWindow(QMainWindow):
    """Fluent Design风格演示窗口"""
    
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.load_stylesheet()
        
    def init_ui(self):
        """初始化用户界面"""
        self.setWindowTitle('QFluentWidgets风格QSS演示 - Python 3.8.10+')
        self.setGeometry(100, 100, 1000, 700)
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.statusBar().showMessage('准备就绪 - Fluent Design风格界面')
        
        # 创建中央窗口部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # 创建主布局
        main_layout = QVBoxLayout(central_widget)
        
        # 创建标签页
        tab_widget = QTabWidget()
        main_layout.addWidget(tab_widget)
        
        # 添加各种组件演示标签页
        tab_widget.addTab(self.create_basic_controls(), '基础控件')
        tab_widget.addTab(self.create_input_controls(), '输入控件')
        tab_widget.addTab(self.create_display_controls(), '显示控件')
        tab_widget.addTab(self.create_layout_controls(), '布局控件')
        
    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()
        
        # 文件菜单
        file_menu = menubar.addMenu('文件')
        file_menu.addAction('新建')
        file_menu.addAction('打开')
        file_menu.addSeparator()
        file_menu.addAction('退出')
        
        # 编辑菜单
        edit_menu = menubar.addMenu('编辑')
        edit_menu.addAction('复制')
        edit_menu.addAction('粘贴')
        
        # 主题菜单
        theme_menu = menubar.addMenu('主题')
        theme_menu.addAction('浅色主题')
        theme_menu.addAction('深色主题')
        
    def create_basic_controls(self):
        """创建基础控件演示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 按钮组
        button_group = QGroupBox('按钮控件')
        button_layout = QHBoxLayout(button_group)
        
        primary_btn = QPushButton('主要按钮')
        secondary_btn = QPushButton('次要按钮')
        secondary_btn.setProperty('class', 'secondary')
        disabled_btn = QPushButton('禁用按钮')
        disabled_btn.setEnabled(False)
        
        button_layout.addWidget(primary_btn)
        button_layout.addWidget(secondary_btn)
        button_layout.addWidget(disabled_btn)
        
        layout.addWidget(button_group)
        
        # 选择控件组
        selection_group = QGroupBox('选择控件')
        selection_layout = QVBoxLayout(selection_group)
        
        # 复选框
        checkbox_layout = QHBoxLayout()
        checkbox1 = QCheckBox('选项 1')
        checkbox2 = QCheckBox('选项 2')
        checkbox2.setChecked(True)
        checkbox3 = QCheckBox('禁用选项')
        checkbox3.setEnabled(False)
        checkbox4 = QCheckBox('已选中禁用选项')
        checkbox4.setChecked(True)
        checkbox4.setEnabled(False)
        
        checkbox_layout.addWidget(checkbox1)
        checkbox_layout.addWidget(checkbox2)
        checkbox_layout.addWidget(checkbox3)
        checkbox_layout.addWidget(checkbox4)
        selection_layout.addLayout(checkbox_layout)
        
        # 单选按钮
        radio_layout = QHBoxLayout()
        radio1 = QRadioButton('选项 A')
        radio2 = QRadioButton('选项 B')
        radio2.setChecked(True)
        radio3 = QRadioButton('选项 C')
        
        radio_layout.addWidget(radio1)
        radio_layout.addWidget(radio2)
        radio_layout.addWidget(radio3)
        selection_layout.addLayout(radio_layout)
        
        layout.addWidget(selection_group)
        
        # 滑块和进度条
        slider_group = QGroupBox('滑块和进度条')
        slider_layout = QVBoxLayout(slider_group)
        
        slider = QSlider(Qt.Horizontal)
        slider.setRange(0, 100)
        slider.setValue(50)
        slider_layout.addWidget(QLabel('滑块控件:'))
        slider_layout.addWidget(slider)
        
        progress = QProgressBar()
        progress.setRange(0, 100)
        progress.setValue(75)
        slider_layout.addWidget(QLabel('进度条:'))
        slider_layout.addWidget(progress)
        
        # 连接滑块和进度条
        slider.valueChanged.connect(progress.setValue)
        
        layout.addWidget(slider_group)
        
        layout.addStretch()
        return widget
        
    def create_input_controls(self):
        """创建输入控件演示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 文本输入组
        input_group = QGroupBox('文本输入控件')
        input_layout = QVBoxLayout(input_group)
        
        # 单行输入
        input_layout.addWidget(QLabel('单行文本输入:'))
        line_edit = QLineEdit()
        line_edit.setPlaceholderText('请输入文本...')
        input_layout.addWidget(line_edit)
        
        # 多行输入
        input_layout.addWidget(QLabel('多行文本输入:'))
        text_edit = QPlainTextEdit()
        text_edit.setPlaceholderText('请输入多行文本...')
        text_edit.setMaximumHeight(100)
        input_layout.addWidget(text_edit)
        
        layout.addWidget(input_group)
        
        # 下拉框组
        combo_group = QGroupBox('下拉选择控件')
        combo_layout = QVBoxLayout(combo_group)
        
        combo_layout.addWidget(QLabel('下拉框:'))
        combo_box = QComboBox()
        combo_box.addItems(['选项 1', '选项 2', '选项 3', '选项 4'])
        combo_layout.addWidget(combo_box)
        
        layout.addWidget(combo_group)
        
        layout.addStretch()
        return widget
        
    def create_display_controls(self):
        """创建显示控件演示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 表格控件
        table_group = QGroupBox('表格控件')
        table_layout = QVBoxLayout(table_group)
        
        table = QTableWidget(3, 4)
        table.setHorizontalHeaderLabels(['列 1', '列 2', '列 3', '列 4'])
        
        # 填充示例数据
        for row in range(3):
            for col in range(4):
                item = QTableWidgetItem(f'数据 {row+1}-{col+1}')
                table.setItem(row, col, item)
                
        table_layout.addWidget(table)
        layout.addWidget(table_group)
        
        # 树形控件
        tree_group = QGroupBox('树形控件')
        tree_layout = QVBoxLayout(tree_group)
        
        tree = QTreeWidget()
        tree.setHeaderLabels(['名称', '类型', '大小'])
        
        # 添加示例项目
        root1 = QTreeWidgetItem(tree, ['文档', '文件夹', ''])
        QTreeWidgetItem(root1, ['文档1.txt', '文本文件', '1.2 KB'])
        QTreeWidgetItem(root1, ['文档2.pdf', 'PDF文件', '2.5 MB'])
        
        root2 = QTreeWidgetItem(tree, ['图片', '文件夹', ''])
        QTreeWidgetItem(root2, ['图片1.jpg', '图像文件', '856 KB'])
        QTreeWidgetItem(root2, ['图片2.png', '图像文件', '1.2 MB'])
        
        tree.expandAll()
        tree_layout.addWidget(tree)
        layout.addWidget(tree_group)
        
        return widget
        
    def create_layout_controls(self):
        """创建布局控件演示"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # 分组框演示
        group1 = QGroupBox('分组框 1')
        group1_layout = QVBoxLayout(group1)
        group1_layout.addWidget(QLabel('这是第一个分组框的内容'))
        group1_layout.addWidget(QPushButton('按钮 1'))
        
        group2 = QGroupBox('分组框 2')
        group2_layout = QVBoxLayout(group2)
        group2_layout.addWidget(QLabel('这是第二个分组框的内容'))
        group2_layout.addWidget(QPushButton('按钮 2'))
        
        groups_layout = QHBoxLayout()
        groups_layout.addWidget(group1)
        groups_layout.addWidget(group2)
        
        layout.addLayout(groups_layout)
        
        # 信息标签
        info_group = QGroupBox('样式信息')
        info_layout = QVBoxLayout(info_group)
        
        info_text = QPlainTextEdit()
        info_text.setPlainText(
            "这个演示展示了基于QFluentWidgets设计理念的QSS样式。\n\n"
            "特性包括:\n"
            "• 现代化的Fluent Design风格\n"
            "• 一致的颜色方案和字体\n"
            "• 圆角边框和阴影效果\n"
            "• 悬停和焦点状态动画\n"
            "• 兼容Python 3.8.10+\n\n"
            "要使用完整的QFluentWidgets功能，请安装:\n"
            "pip install PyQt-Fluent-Widgets"
        )
        info_text.setReadOnly(True)
        info_layout.addWidget(info_text)
        
        layout.addWidget(info_group)
        
        return widget
        
    def load_stylesheet(self):
        """加载QSS样式表"""
        try:
            # 获取当前脚本目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            qss_file = os.path.join(current_dir, 'style.qss')
            
            if os.path.exists(qss_file):
                with open(qss_file, 'r', encoding='utf-8') as f:
                    stylesheet = f.read()
                    self.setStyleSheet(stylesheet)
                    print(f"已加载样式文件: {qss_file}")
            else:
                print(f"样式文件不存在: {qss_file}")
                print("使用默认样式")
                
        except Exception as e:
            print(f"加载样式文件时出错: {e}")
            print("使用默认样式")


def main():
    """主函数"""
    app = QApplication(sys.argv)
    
    # 设置应用程序信息
    app.setApplicationName('QFluentWidgets风格QSS演示')
    app.setApplicationVersion('1.0.0')
    app.setOrganizationName('PyQt Demo')
    
    # 创建并显示主窗口
    window = FluentDemoWindow()
    window.show()
    
    print("Fluent Design 样式演示程序已启动")
    print("关闭窗口以退出程序")
    
    # 运行应用程序
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()