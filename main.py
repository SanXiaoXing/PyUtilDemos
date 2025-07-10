import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QFrame, QSizePolicy, QGraphicsEffect, QGraphicsBlurEffect,
    QGraphicsOpacityEffect
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve, QPoint
from PyQt5.QtGui import QFont


class AnimatedCardWidget(QFrame):
    clicked = pyqtSignal(str)  # 发送卡片标题信号
    
    def __init__(self, svg_path: str, title: str, description: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.description = description
        self.is_hovered = False
        self.original_title_pos = None  # 记录标题的初始位置
        
        self.setMouseTracking(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedSize(200, 150)
        
        self.init_ui(svg_path)
        self.setup_animations()
        self.apply_styles()
    
    def init_ui(self, svg_path):
        """初始化UI组件"""
        layout = QVBoxLayout()
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(25)
        layout.setAlignment(Qt.AlignCenter)
        
        # SVG图标
        self.icon_widget = QSvgWidget(svg_path)
        self.icon_widget.setFixedSize(QSize(50, 50))
        layout.addWidget(self.icon_widget, alignment=Qt.AlignTop)
        
        # 标题标签
        self.title_label = QLabel(self.title)
        self.title_label.setFont(QFont("Arial", 16, QFont.Bold))
        self.title_label.setAlignment(Qt.AlignCenter)
        self.title_label.setStyleSheet("color: #333333; background: transparent; border: none;")
        layout.addWidget(self.title_label, alignment=Qt.AlignCenter)
        
        # 描述标签（初始隐藏）
        self.desc_label = QLabel(self.description)
        self.desc_label.setFont(QFont("Arial", 12))
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("color: #555555; background: transparent; border: none;")
        self.desc_label.setWordWrap(True)
        layout.addWidget(self.desc_label, alignment=Qt.AlignCenter)
        
        self.setLayout(layout)
        
        # 在布局完成后记录标题的初始位置
        self.original_title_pos = None
    
    def setup_animations(self):
        """设置动画效果"""
        # 图标模糊效果
        self.blur_effect = QGraphicsBlurEffect()
        self.blur_effect.setBlurRadius(2)
        self.icon_widget.setGraphicsEffect(self.blur_effect)
        
        # 描述透明度效果
        self.opacity_effect = QGraphicsOpacityEffect()
        self.opacity_effect.setOpacity(0)
        self.desc_label.setGraphicsEffect(self.opacity_effect)
        
        # 模糊动画
        self.blur_animation = QPropertyAnimation(self.blur_effect, b"blurRadius")
        self.blur_animation.setDuration(300)
        self.blur_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 标题位置动画
        self.title_animation = QPropertyAnimation(self.title_label, b"pos")
        self.title_animation.setDuration(300)
        self.title_animation.setEasingCurve(QEasingCurve.OutCubic)
        
        # 描述透明度动画
        self.desc_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.desc_animation.setDuration(300)
        self.desc_animation.setEasingCurve(QEasingCurve.OutCubic)
    
    def apply_styles(self):
        """应用样式"""
        self.setStyleSheet("""
            QFrame {
                background-color: #ffffff;
                border: 1px solid #e0e0e0;
                border-radius: 12px;
            }
            QFrame:hover {
                border-color: #cccccc;
                background-color: #ffffff;
            }
        """)
    
    def get_original_title_pos(self):
        """获取标题的初始位置"""
        if self.original_title_pos is None:
            self.original_title_pos = self.title_label.pos()
        return self.original_title_pos
    
    def enterEvent(self, event):
        """鼠标进入事件"""
        if not self.is_hovered:
            self.is_hovered = True
            self.start_hover_animation()
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        """鼠标离开事件"""
        if self.is_hovered:
            self.is_hovered = False
            self.start_leave_animation()
        super().leaveEvent(event)
    
    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.title)
        super().mousePressEvent(event)
    
    def start_hover_animation(self):
        """开始悬停动画"""
        # 图标模糊
        self.blur_animation.setStartValue(2)
        self.blur_animation.setEndValue(8)
        self.blur_animation.start()
        
        # 标题上移 - 使用绝对位置
        original_pos = self.get_original_title_pos()
        current_pos = self.title_label.pos()
        self.title_animation.setStartValue(current_pos)
        self.title_animation.setEndValue(original_pos + QPoint(0, -40))
        self.title_animation.start()
        
        # 描述渐入
        self.desc_animation.setStartValue(0)
        self.desc_animation.setEndValue(1)
        self.desc_animation.start()
    
    def start_leave_animation(self):
        """开始离开动画"""
        # 图标清晰
        self.blur_animation.setStartValue(8)
        self.blur_animation.setEndValue(2)
        self.blur_animation.start()
        
        # 标题回到原位 - 使用绝对位置
        original_pos = self.get_original_title_pos()
        current_pos = self.title_label.pos()
        self.title_animation.setStartValue(current_pos)
        self.title_animation.setEndValue(original_pos)
        self.title_animation.start()
        
        # 描述渐出
        self.desc_animation.setStartValue(1)
        self.desc_animation.setEndValue(0)
        self.desc_animation.start()
    
class CardGrid(QWidget):
    def __init__(self):
        super().__init__()
        self.resize(1000, 600)
        self.setStyleSheet("""
            QWidget {
                background-color: #f5f5f5;
            }
        """)

        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)
        grid_layout.setContentsMargins(30, 30, 30, 30)

        # 卡片配置数据
        card_configs = [
            {
                "svg": "assets/icon/circle.svg",
                "title": "灯泡状态监控",
                "desc": "实时监控设备状态，支持多种显示模式和数据可视化"
            },
            {
                "svg": "assets/icon/square.svg",
                "title": "数据回放工具",
                "desc": "历史数据回放分析，支持多格式数据导入和时间轴控制"
            },
            {
                "svg": "assets/icon/check.svg",
                "title": "校准工具",
                "desc": "设备校准和参数调整，提供精确的测量和校正功能"
            },
            {
                "svg": "assets/icon/down_arrow.svg",
                "title": "日志查看器",
                "desc": "系统日志实时查看，支持过滤、搜索和导出功能"
            },
            {
                "svg": "assets/icon/circle.svg",
                "title": "总线数据监控",
                "desc": "CAN总线数据实时监控，支持协议解析和数据分析"
            },
            {
                "svg": "assets/icon/square.svg",
                "title": "实时数据绘图",
                "desc": "多通道数据实时绘图，支持波形显示和数据记录"
            },
            {
                "svg": "assets/icon/check.svg",
                "title": "配置转换器",
                "desc": "配置文件格式转换，支持多种标准格式互转"
            },
            {
                "svg": "assets/icon/down_arrow.svg",
                "title": "系统设置",
                "desc": "系统参数配置和用户偏好设置，个性化定制界面"
            }
        ]

        # 创建卡片
        for i, config in enumerate(card_configs):
            # 构建完整的SVG路径
            svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), config["svg"])
            
            # 如果SVG文件不存在，使用默认路径
            if not os.path.exists(svg_path):
                svg_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets/icon/circle.svg")
            
            card = AnimatedCardWidget(svg_path, config["title"], config["desc"])
            card.clicked.connect(self.on_card_clicked)
            
            row = i // 4
            col = i % 4
            grid_layout.addWidget(card, row, col)

        self.setLayout(grid_layout)
    
    def on_card_clicked(self, title):
        """处理卡片点击事件"""
        print(f"点击了卡片: {title}")
        # self.navigate_to_page(title)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CardGrid()
    window.show()
    sys.exit(app.exec_())
