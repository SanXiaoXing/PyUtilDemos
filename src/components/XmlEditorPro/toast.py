from PyQt5.QtCore import QEasingCurve, QPoint, QPropertyAnimation, QTimer, Qt
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget


class Toast(QFrame):
    def __init__(self, message: str, kind: str, parent: QWidget):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 10, 14, 10)
        layout.setSpacing(10)

        dot = QLabel("●")
        dot.setFont(QFont(self.font().family(), 12, QFont.Bold))
        dot.setStyleSheet(f"color: {self._kind_color(kind)}; background: transparent;")
        layout.addWidget(dot)

        label = QLabel(message)
        label.setWordWrap(True)
        label.setStyleSheet("background: transparent;")
        layout.addWidget(label, 1)

        self.setMinimumWidth(260)

    @staticmethod
    def _kind_color(kind: str) -> str:
        if kind == "success":
            return "#34c759"
        if kind == "error":
            return "#ff3b30"
        return "#0a84ff"


class ToastManager:
    def __init__(self, parent: QWidget):
        self._parent = parent
        self._active = []

    def show(self, message: str, kind: str = "info", ms: int = 2800) -> None:
        toast = Toast(message, kind, self._parent)
        toast.show()
        toast.raise_()
        self._active.append(toast)
        self._relayout()

        self._animate_in(toast)
        QTimer.singleShot(ms, lambda: self._animate_out(toast))

    def _relayout(self) -> None:
        pad = 18
        gap = 10
        x = self._parent.width() - pad
        y = self._parent.height() - pad
        for toast in reversed(self._active):
            toast.adjustSize()
            y -= toast.height()
            toast.move(QPoint(x - toast.width(), y))
            y -= gap

    def _animate_in(self, toast: Toast) -> None:
        start = toast.pos() + QPoint(26, 0)
        end = toast.pos()
        toast.move(start)

        anim = QPropertyAnimation(toast, b"pos", toast)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(180)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start()

        toast._anim_in = anim

    def _animate_out(self, toast: Toast) -> None:
        if toast not in self._active:
            return

        start = toast.pos()
        end = toast.pos() + QPoint(26, 0)
        anim = QPropertyAnimation(toast, b"pos", toast)
        anim.setStartValue(start)
        anim.setEndValue(end)
        anim.setDuration(200)
        anim.setEasingCurve(QEasingCurve.InCubic)

        def done():
            if toast in self._active:
                self._active.remove(toast)
            toast.hide()
            toast.deleteLater()
            self._relayout()

        anim.finished.connect(done)
        anim.start()
        toast._anim_out = anim

    def on_parent_resized(self) -> None:
        self._relayout()
