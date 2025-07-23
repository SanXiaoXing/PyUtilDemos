import sys
from PyQt5.QtWidgets import QAbstractButton,QApplication, QWidget, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QRectF, QPropertyAnimation, pyqtProperty
from PyQt5.QtGui import QPainter, QColor, QBrush



class ToggleSwitch(QAbstractButton):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._checked = False
        self._circle_position = 0
        self._track_radius = 10
        self._thumb_radius = 9

        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(50, 25)

        self._animation = QPropertyAnimation(self, b"circle_position", self)
        self._animation.setDuration(200)

        self.toggled.connect(self.start_animation)

    def sizeHint(self):
        return self.minimumSize()

    def paintEvent(self, event):
        rect = self.rect()
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Background
        track_color = QColor("#4caf50") if self._checked else QColor("#ccc")
        painter.setBrush(QBrush(track_color))
        painter.setPen(Qt.NoPen)
        track_rect = QRectF(0, 0, rect.width(), rect.height())
        painter.drawRoundedRect(track_rect, self._track_radius, self._track_radius)

        # Thumb
        margin = (rect.height() - self._thumb_radius * 2) / 2
        thumb_x = self._circle_position * (rect.width() - self._thumb_radius * 2 - margin)
        thumb_rect = QRectF(thumb_x + margin, margin, self._thumb_radius * 2, self._thumb_radius * 2)
        painter.setBrush(QBrush(Qt.white))
        painter.drawEllipse(thumb_rect)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle()
        super().mouseReleaseEvent(event)

    def start_animation(self, checked):
        self._checked = checked
        start = 1.0 if not checked else 0.0
        end = 0.0 if not checked else 1.0
        self._animation.stop()
        self._animation.setStartValue(start)
        self._animation.setEndValue(end)
        self._animation.start()

    def get_circle_position(self):
        return self._circle_position

    def set_circle_position(self, pos):
        self._circle_position = pos
        self.update()

    circle_position = pyqtProperty(float, fget=get_circle_position, fset=set_circle_position)


class DemoWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ToggleSwitch 示例")
        layout = QVBoxLayout()

        self.label = QLabel("当前状态：关闭")
        self.switch = ToggleSwitch()
        self.switch.toggled.connect(self.on_toggled)

        layout.addWidget(self.switch)
        layout.addWidget(self.label)
        self.setLayout(layout)

    def on_toggled(self, checked):
        self.label.setText(f"当前状态：{'开启' if checked else '关闭'}")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = DemoWindow()
    window.resize(200, 100)
    window.show()
    sys.exit(app.exec_())