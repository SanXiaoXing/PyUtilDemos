from PyQt5.QtWidgets import QWidget, QVBoxLayout, QDoubleSpinBox, QSizePolicy
from PyQt5.QtCore import Qt, QRectF, QPointF
from PyQt5.QtGui import QPainter, QPen, QColor, QFont, QPainterPath
import math


class DialCanvas(QWidget):
    def __init__(self, min_value=0, max_value=100, unit="", thresholds=None, precision=None,parent=None):
        super().__init__(parent)
        self.min_value = min_value
        self.max_value = max_value
        self.current_value = min_value
        self.unit = unit
        self.thresholds = thresholds or []  # ✅ 用于分段颜色显示
        self.precision = precision

        self.start_angle = 225
        self.span_angle = 270
        self.major_divisions = 10
        self.minor_per_major = 5

        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    def set_range(self, min_val, max_val):
        self.min_value = min_val
        self.max_value = max_val
        self.update()

    def set_value(self, value):
        self.current_value = max(min(value, self.max_value), self.min_value)
        self.update()


    def set_precision(self, precision):
        self.precision = precision
        self.update()

    def set_thresholds(self, thresholds):
        self.thresholds = thresholds
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        raw_size = min(self.width(), self.height())
        min_size = 200
        max_size = 400
        size = max(min_size, min(max_size, raw_size))
        margin = 10
        rect = QRectF((self.width() - size) / 2 + margin,
                      (self.height() - size) / 2 + margin,
                      size - 2 * margin, size - 2 * margin)
        center = rect.center()
        radius = rect.width() / 2

        # 背景
        bg_color = self.palette().window().color()
        painter.setPen(Qt.NoPen)
        painter.setBrush(bg_color)
        painter.drawEllipse(rect)

        # ✅ 绘制蓝环（分段）
        outer_radius = radius
        ring_width = radius * 0.07
        inner_radius = radius - ring_width
        self.draw_arc_ring(painter, center, outer_radius, inner_radius,
                           self.start_angle, self.span_angle)

        # 指针（三角形）
        percent = (self.current_value - self.min_value) / (self.max_value - self.min_value)
        angle = self.start_angle - percent * self.span_angle
        rad = math.radians(angle)
        pointer_len = radius * 0.8
        pointer_width = radius * 0.05

        tip = QPointF(center.x() + pointer_len * math.cos(rad),
                      center.y() - pointer_len * math.sin(rad))
        dx = pointer_width * math.sin(rad)
        dy = pointer_width * math.cos(rad)
        left_base = QPointF(center.x() - dx, center.y() - dy)
        right_base = QPointF(center.x() + dx, center.y() + dy)

        pointer_path = QPainterPath()
        pointer_path.moveTo(tip)
        pointer_path.lineTo(left_base)
        pointer_path.lineTo(right_base)
        pointer_path.closeSubpath()

        painter.setPen(Qt.NoPen)
        painter.setBrush(QColor(96, 96, 96))
        painter.drawPath(pointer_path)

        # 中心黑点
        painter.setBrush(Qt.black)
        painter.setBrush(QColor(96, 96, 96))
        painter.drawEllipse(center, radius * 0.05, radius * 0.05)

        # 实时值与单位
        value_font = QFont("Arial", int(radius * 0.1), QFont.Bold)
        unit_font = QFont("Arial", int(radius * 0.07))
        format_str = f"{{:.{self.precision}f}}"
        value_str = format_str.format(self.current_value)
        unit_str = self.unit

        value_rect = QRectF(center.x() - 60, center.y() + radius * 0.15, 120, 40)
        unit_rect = QRectF(center.x() - 60, center.y() + radius * 0.28, 120, 30)
        painter.setPen(QPen(Qt.black))
        painter.setFont(value_font)
        painter.drawText(value_rect, Qt.AlignCenter, value_str)
        painter.setFont(unit_font)
        painter.drawText(unit_rect, Qt.AlignCenter, unit_str)

        # 刻度线和文字
        total_ticks = self.major_divisions * self.minor_per_major
        for i in range(total_ticks + 1):
            angle = self.start_angle - i * self.span_angle / total_ticks
            rad = math.radians(angle)
            is_major = i % self.minor_per_major == 0
            line_len = radius * 0.15 if is_major else radius * 0.07
            pen = QPen(Qt.black, 2 if is_major else 1)
            painter.setPen(pen)
            outer = QPointF(center.x() + radius * math.cos(rad),
                            center.y() - radius * math.sin(rad))
            inner = QPointF(center.x() + (radius - line_len) * math.cos(rad),
                            center.y() - (radius - line_len) * math.sin(rad))
            painter.drawLine(inner, outer)

            if is_major:
                value = self.min_value + (i / total_ticks) * (self.max_value - self.min_value)
                text = f"{value:.0f}"
                text_radius = radius - line_len - 20
                text_width = 40
                text_height = 25
                text_x = center.x() + text_radius * math.cos(rad) - text_width / 2
                text_y = center.y() - text_radius * math.sin(rad) - text_height / 2
                painter.setFont(QFont("Arial", int(radius * 0.07)))
                painter.setPen(Qt.black)
                painter.drawText(QRectF(text_x, text_y, 30, 20), Qt.AlignCenter, text)


    def draw_arc_ring(self, painter, center, outer_radius, inner_radius, start_angle, span_angle):
        if not self.thresholds:
            # 默认蓝色全环
            self._draw_arc_segment(painter, center, outer_radius, inner_radius,
                                start_angle, span_angle, QColor(0, 128, 255, 120))
            return

        total_range = self.max_value - self.min_value
        last_value = self.min_value
        last_angle = start_angle

        for threshold_value, color in self.thresholds:
            threshold_value = min(threshold_value, self.max_value)
            percent = (threshold_value - last_value) / total_range
            angle_span = span_angle * percent
            self._draw_arc_segment(painter, center, outer_radius, inner_radius,
                                last_angle, angle_span, QColor(*color))  # (r,g,b,a)
            last_value = threshold_value
            last_angle -= angle_span

        # 若有剩余区间
        if last_value < self.max_value:
            percent = (self.max_value - last_value) / total_range
            angle_span = span_angle * percent
            self._draw_arc_segment(painter, center, outer_radius, inner_radius,
                                last_angle, angle_span, QColor(0, 128, 255, 80))  # 默认蓝色

    def _draw_arc_segment(self, painter, center, outer_radius, inner_radius,
                          start_angle, span_angle, color):
        path = QPainterPath()
        for i in range(int(span_angle) + 1):
            angle = start_angle - i
            x = center.x() + outer_radius * math.cos(math.radians(angle))
            y = center.y() - outer_radius * math.sin(math.radians(angle))
            if i == 0:
                path.moveTo(x, y)
            else:
                path.lineTo(x, y)
        for i in range(int(span_angle) + 1):
            angle = start_angle - span_angle + i
            x = center.x() + inner_radius * math.cos(math.radians(angle))
            y = center.y() - inner_radius * math.sin(math.radians(angle))
            path.lineTo(x, y)
        path.closeSubpath()
        painter.setBrush(color)
        painter.setPen(Qt.NoPen)
        painter.drawPath(path)


class GaugeWidget(QWidget):
    def __init__(self, min_value=0, max_value=100, initial_value=50, unit="",precision=None, thresholds=None, parent=None):
        super().__init__(parent)
        self.dial = DialCanvas(min_value=min_value, max_value=max_value,
                               unit=unit,precision=precision,thresholds=thresholds)
        self.dial.set_value(initial_value)

        self.spinbox = QDoubleSpinBox()
        self.spinbox.setDecimals(precision)
        self.spinbox.setSingleStep(10 ** -precision)
        self.spinbox.setRange(min_value, max_value)
        self.spinbox.setValue(initial_value)
        self.spinbox.setFixedWidth(100)
        self.spinbox.valueChanged.connect(self.on_spin_changed)


        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignHCenter | Qt.AlignTop)
        layout.setSpacing(10)
        layout.addWidget(self.dial, stretch=1)
        layout.addWidget(self.spinbox, alignment=Qt.AlignHCenter)
        self.setLayout(layout)
        self.setMinimumSize(250, 300)


    def on_spin_changed(self, value):
        self.dial.set_value(value)


    def set_value(self, value):
        self.spinbox.setValue(value)
        self.dial.set_value(value)


    def set_precision(self, precision):
        self.spinbox.setDecimals(precision)
        self.spinbox.setSingleStep(10 ** -precision)
        self.dial.set_precision(precision)




if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication

    app = QApplication(sys.argv)

    thresholds = [
    (210, (0, 128, 255, 120)),    # 蓝色：正常区
    (270, (255, 165, 0, 150)),  # 橙色：预警区
    (300, (255, 0, 0, 120)),    # 红色：告警区
]
    
    gauge = GaugeWidget(min_value=0, max_value=300,
                        initial_value=120, unit="km/h", precision=0, thresholds=thresholds)
    gauge.resize(400, 450)
    gauge.show()
    sys.exit(app.exec_())
