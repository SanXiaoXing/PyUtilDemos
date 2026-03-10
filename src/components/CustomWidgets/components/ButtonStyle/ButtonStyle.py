#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：631_ZHCLTest 
@File    ：ButtonStyle.py
@Author  ：SanXiaoXing
@Date    ：2026/1/22
@Description: 滑动开关组件
"""
import sys
from PyQt5.QtCore import Qt, QRect, QPoint, QVariantAnimation, pyqtSignal
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QApplication, QWidget, QHBoxLayout, QVBoxLayout, QLabel


class SwitchButton(QWidget):
    # 添加状态变化信号
    toggled = pyqtSignal(bool)  # 状态变化时发射信号

    def __init__(self, parent=None, width=50, height=30):
        super().__init__(parent)
        self.checked = False
        self.setCursor(Qt.PointingHandCursor)
        self.animation = QVariantAnimation()
        self.animation.setDuration(80)  # 动画持续时间
        self.animation.valueChanged.connect(self.update)
        self.animation.finished.connect(self.onAnimationFinished)
        # 设置按钮大小
        self.setButtonSize(width, height)

    def setButtonSize(self, width, height):
        """设置按钮大小，所有参数自动按比例计算"""
        self.setFixedSize(width, height)
        # 按钮圆形的半径 = 高度的一半减去边距
        self.circle_radius = height * 0.4
        # 圆角半径 = 高度的一半
        self.rounded_radius = height / 2
        # 动画移动距离 = 宽度 - 高度（圆形直径）
        self.move_offset = width - height
        self.animation.setStartValue(0)
        self.animation.setEndValue(self.move_offset)
        # 更新动画方向
        self.animation.setDirection(QVariantAnimation.Forward if self.checked else QVariantAnimation.Backward)

    def isChecked(self):
        return self.checked

    def setChecked(self, check):
        self.checked = check
        self.animation.setDirection(QVariantAnimation.Forward if self.checked else QVariantAnimation.Backward)
        self.animation.start()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.setPen(Qt.NoPen)
        if self.checked:
            painter.setBrush(QColor('#07c160'))  # 选中颜色
        else:
            painter.setBrush(QColor('#d5d5d5'))  # 未选中颜色

        # 绘制外框（圆角半径自适应）
        painter.drawRoundedRect(QRect(0, 0, self.width(), self.height()), 
                                self.rounded_radius, self.rounded_radius)

        # 按钮位置（自适应）
        offset = self.animation.currentValue()
        center_x = self.height() / 2 + offset
        center_y = self.height() / 2

        # 绘制按钮
        painter.setBrush(QColor(255, 255, 255))
        painter.drawEllipse(QPoint(int(center_x), int(center_y)), 
                            int(self.circle_radius), int(self.circle_radius))

    def mouseReleaseEvent(self, event) -> None:
        if event.button() == Qt.LeftButton:
            self.checked = not self.checked
            self.animation.setDirection(QVariantAnimation.Forward if self.checked else QVariantAnimation.Backward)
            self.animation.start()
            self.toggled.emit(self.checked)  # 发射状态变化信号

    def onAnimationFinished(self):
        pass


class Example(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

    def initUI(self):
        main_layout = QVBoxLayout()
        
        # 默认大小 (50x30)
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("默认:"))
        switch1 = SwitchButton()
        switch1.toggled.connect(self.onStateChanged)
        h1.addWidget(switch1)
        main_layout.addLayout(h1)
        
        # 放大 1.5倍 (75x45)
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("1.5倍:"))
        switch2 = SwitchButton(width=75, height=45)
        switch2.toggled.connect(self.onStateChanged)
        h2.addWidget(switch2)
        main_layout.addLayout(h2)
        
        # 放大 2倍 (100x60)
        h3 = QHBoxLayout()
        h3.addWidget(QLabel("2倍:"))
        switch3 = SwitchButton(width=100, height=60)
        switch3.toggled.connect(self.onStateChanged)
        h3.addWidget(switch3)
        main_layout.addLayout(h3)
        
        self.setLayout(main_layout)
        self.setFixedSize(400, 300)
    
    def onStateChanged(self, checked):
        """点击开关时打印 0 或 1"""
        print("1" if checked else "0")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Example()
    ex.show()
    sys.exit(app.exec_())