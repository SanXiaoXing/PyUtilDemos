from PyQt5.QtWidgets import QComboBox, QWidget, QLabel, QPushButton, QHBoxLayout, QVBoxLayout
from PyQt5.QtCore import Qt, QTimer, pyqtSignal, QEvent, QPoint, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QPalette, QColor


class FluentConfirmPopup(QWidget):
    confirmed = pyqtSignal()
    canceled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent, Qt.Tool | Qt.FramelessWindowHint)
        self.setObjectName("FluentConfirmPopup")

        # 设置白色背景
        self.setAutoFillBackground(True)
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(255, 255, 255))
        self.setPalette(palette)

        self.setAttribute(Qt.WA_StyledBackground, True)

        self.label = QLabel("")
        self.btn_confirm = QPushButton("确认")
        self.btn_cancel = QPushButton("取消")
        self.btn_confirm.setObjectName("btn_confirm")
        self.btn_cancel.setObjectName("btn_cancel")

        # 直接使用主布局作为内容区域
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        layout.addWidget(self.label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        btn_layout.addWidget(self.btn_cancel)
        btn_layout.addWidget(self.btn_confirm)
        layout.addLayout(btn_layout)

        self.btn_confirm.clicked.connect(self.on_confirm)
        self.btn_cancel.clicked.connect(self.on_cancel)

        # 自动消失
        self.timer = QTimer(self)
        self.timer.setInterval(5000)
        self.timer.timeout.connect(self.hide)

        # 动画效果
        self.fade_anim = QPropertyAnimation(self, b"windowOpacity")
        self.fade_anim.setDuration(200)
        self.fade_anim.setEasingCurve(QEasingCurve.OutCubic)

        self.setStyleSheet(self.qss())

        self.target_combo = None
        self.monitored_widgets = []

    def set_target_combo(self, combo):
        self.target_combo = combo

    def setup_event_filters(self):
        if not self.target_combo:
            return

        # 清除之前的事件过滤器
        for widget in self.monitored_widgets:
            widget.removeEventFilter(self)
        self.monitored_widgets.clear()

        # 递归安装事件过滤器到所有父窗口
        parent = self.target_combo.parent()
        while parent:
            parent.installEventFilter(self)
            self.monitored_widgets.append(parent)
            parent = parent.parent()

    def eventFilter(self, obj, event):
        if event.type() in (QEvent.Move, QEvent.Resize):
            if self.isVisible() and self.target_combo:
                self.update_position()
        return super().eventFilter(obj, event)

    def update_position(self):
        if not self.target_combo:
            return

        # 计算 popup 位置（在控件下方居中，使用全局坐标）
        combo_global_pos = self.target_combo.mapToGlobal(QPoint(0, 0))
        combo_width = self.target_combo.width()
        popup_width = self.width()

        popup_x = combo_global_pos.x() + (combo_width - popup_width) // 2
        popup_y = combo_global_pos.y() + self.target_combo.height() + 8

        self.move(popup_x, popup_y)

    def show_message(self, text):
        self.label.setText(text)
        self.adjustSize()

        # 在显示时重新设置事件过滤器
        self.setup_event_filters()

        if self.target_combo:
            self.update_position()

        # 淡入动画
        self.setWindowOpacity(0)
        self.show()
        self.raise_()
        self.fade_anim.setStartValue(0)
        self.fade_anim.setEndValue(1)
        self.fade_anim.start()

        self.timer.start()

    def hideEvent(self, event):
        self.timer.stop()
        super().hideEvent(event)

    def on_confirm(self):
        self.timer.stop()
        self.fade_anim.setStartValue(1)
        self.fade_anim.setEndValue(0)
        self.fade_anim.finished.connect(lambda: (self.fade_anim.finished.disconnect(), self.hide(), self.confirmed.emit()))
        self.fade_anim.start()

    def on_cancel(self):
        self.timer.stop()
        self.fade_anim.setStartValue(1)
        self.fade_anim.setEndValue(0)
        self.fade_anim.finished.connect(lambda: (self.fade_anim.finished.disconnect(), self.hide(), self.canceled.emit()))
        self.fade_anim.start()

    def qss(self):
        return """
        QWidget#FluentConfirmPopup {
            background: white;
            border-radius: 12px;
            border: 1px solid rgba(0, 120, 212, 0.2);
        }

        QLabel {
            padding: 4px 0;
            color: #1a1a1a;
            font-size: 14px;
            font-weight: 500;
            background: transparent;
            border: none;
        }

        QPushButton {
            padding: 8px 20px;
            border-radius: 8px;
            border: none;
            font-size: 13px;
            font-weight: 500;
            min-width: 70px;
        }

        QPushButton#btn_cancel {
            background: #f3f8ff;
            color: #0066cc;
        }

        QPushButton#btn_cancel:hover {
            background: #e8f2ff;
        }

        QPushButton#btn_cancel:pressed {
            background: #d9ecff;
        }

        QPushButton#btn_confirm {
            background: #0078d4;
            color: white;
        }

        QPushButton#btn_confirm:hover {
            background: #106ebe;
        }

        QPushButton#btn_confirm:pressed {
            background: #005a9e;
        }
        """

class SafeComboBox(QComboBox):
    """带二次确认的下拉框"""
    
    # 状态变化信号 (new_state: bool, True=闭合, False=断开)
    state_changed = pyqtSignal(bool)
    
    def __init__(self, parent=None):
        super().__init__(parent)

        self.current_value = None
        self.pending_value = None
        
        # 当前状态 (True=闭合, False=断开)
        self._state = False
        # 状态文本映射
        self._state_texts = ("断开", "闭合")

        self.popup = FluentConfirmPopup(self)
        self.popup.set_target_combo(self)
        self.popup.confirmed.connect(self.apply_change)
        self.popup.canceled.connect(self.cancel_change)

        self.currentIndexChanged.connect(self.on_changed)

        self._init_flag = True

    def add_safe_items(self, items):
        for item in items:
            self.addItem(item)
    
    def init_signal_control(self, state: bool = False) -> None:
        """
        初始化为信号控制模式
        
        Args:
            state: 初始状态 (True=闭合, False=断开)
        """
        self._state = state
        self.blockSignals(True)
        self.clear()
        self.addItems(self._state_texts)
        self.setCurrentText(self._state_texts[1] if state else self._state_texts[0])
        self.current_value = self.currentText()
        self.blockSignals(False)
        self._init_flag = False
    
    def set_state(self, state: bool) -> None:
        """
        设置状态（不触发确认弹窗）
        
        Args:
            state: 状态 (True=闭合, False=断开)
        """
        self._state = state
        self.blockSignals(True)
        self.setCurrentText(self._state_texts[1] if state else self._state_texts[0])
        self.current_value = self.currentText()
        self.blockSignals(False)
    
    def get_state(self) -> bool:
        """获取当前状态"""
        return self._state

    def on_changed(self, index):
        text = self.itemText(index)

        # 初始化阶段
        if self._init_flag:
            self.current_value = text
            self._init_flag = False
            return

        self.pending_value = text

        # 回滚 UI（关键防误触）
        self.blockSignals(True)
        self.setCurrentText(self.current_value)
        self.blockSignals(False)

        # 显示气泡
        self.show_popup(text)

    def show_popup(self, text):
        msg = f"切换到【{text}】？"
        self.popup.show_message(msg)

    def apply_change(self):
        if not self.pending_value:
            return

        self.current_value = self.pending_value
        
        # 更新状态
        self._state = self.pending_value == self._state_texts[1]

        self.blockSignals(True)
        self.setCurrentText(self.current_value)
        self.blockSignals(False)

        # 发射状态变化信号
        self.state_changed.emit(self._state)

        self.pending_value = None

    def cancel_change(self):
        self.pending_value = None


class SafeCBWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SafeComboBox 测试")
        self.resize(300, 150)

        layout = QVBoxLayout(self)

        combo = SafeComboBox()
        combo.add_safe_items(["模式A", "模式B", "模式C"])

        layout.addWidget(combo)


if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout
    import sys

    app = QApplication(sys.argv)

    window = SafeCBWindow()
    window.show()
    sys.exit(app.exec())