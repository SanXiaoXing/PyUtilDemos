# -*- coding: utf-8 -*-
"""搜索下拉框控件。

结合 QLineEdit 和下拉列表的自定义搜索控件。
"""

from typing import List, Dict, Optional, Callable
from PyQt5.QtWidgets import (
    QWidget, QLineEdit, QListWidget, QListWidgetItem, QVBoxLayout,
    QFrame, QAbstractItemView
)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QEvent
from PyQt5.QtGui import QColor
# from pyqtgraph.examples.DateAxisItem_QtDesigner import window


class SearchComboBox(QWidget):
    """搜索下拉框控件。
    
    结合输入框和下拉列表，支持输入搜索、结果展示和选择跳转。
    
    Signals:
        signal_selected: 信号选中时发射 (signal_id: str)
    """
    
    signal_selected = pyqtSignal(str)  # signal_id
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        
        # 搜索结果数据源：[(signal_id, signal_name, page), ...]
        self._search_data: List[tuple] = []
        # 最大显示结果数
        self._max_results = 10
        
        self._init_ui()
    
    def _init_ui(self) -> None:
        """初始化UI"""
        # 主布局
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 输入框
        self._line_edit = QLineEdit()
        self._line_edit.setPlaceholderText("搜索信号...")
        self._line_edit.setClearButtonEnabled(True)
        self._line_edit.textChanged.connect(self._on_text_changed)
        
        # 下拉列表容器（使用 Tool 标志避免焦点问题）
        self._popup_frame = QFrame(self, Qt.Tool | Qt.FramelessWindowHint)
        self._popup_frame.setObjectName("searchPopup")
        self._popup_frame.setAttribute(Qt.WidgetAttribute.WA_ShowWithoutActivating)
        
        popup_layout = QVBoxLayout(self._popup_frame)
        popup_layout.setContentsMargins(0, 0, 0, 0)
        popup_layout.setSpacing(0)
        
        # 下拉列表
        self._list_widget = QListWidget()
        self._list_widget.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self._list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self._list_widget.itemClicked.connect(self._on_item_clicked)
        self._list_widget.setMaximumHeight(250)
        
        popup_layout.addWidget(self._list_widget)
        
        # 设置样式
        self._setup_style()
        
        layout.addWidget(self._line_edit)
        
        # 安装事件过滤器
        self._line_edit.installEventFilter(self)
        self._popup_frame.installEventFilter(self)
    
    def _setup_style(self) -> None:
        """设置样式"""
        self._line_edit.setStyleSheet("""
            QLineEdit {
                padding: 6px 10px;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                background: white;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #0078d4;
            }
            QLineEdit::clear-button {
                subcontrol-position: right center;
                padding-right: 4px;
            }
        """)
        
        self._popup_frame.setStyleSheet("""
            QFrame#searchPopup {
                background: white;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
            }
            QListWidget {
                border: none;
                background: transparent;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #f0f0f0;
            }
            QListWidget::item:last-child {
                border-bottom: none;
            }
            QListWidget::item:hover {
                background: #f5f5f5;
            }
            QListWidget::item:selected {
                background: #e8f4ff;
                color: #0078d4;
            }
        """)
    
    def set_search_data(self, data: List[tuple]) -> None:
        """设置搜索数据源。
        
        Args:
            data: 数据列表，每个元素为 (signal_id, signal_name, page)
        """
        self._search_data = data
    
    def set_placeholder(self, text: str) -> None:
        """设置占位文本。
        
        Args:
            text: 占位文本
        """
        self._line_edit.setPlaceholderText(text)
    
    def text(self) -> str:
        """获取当前输入文本。"""
        return self._line_edit.text()
    
    def setText(self, text: str) -> None:
        """设置输入文本。"""
        self._line_edit.setText(text)
    
    def clear(self) -> None:
        """清空输入。"""
        self._line_edit.clear()
    
    def _on_text_changed(self, text: str) -> None:
        """输入文本变化处理。"""
        if not text.strip():
            self._hide_popup()
            return
        
        # 搜索匹配结果
        results = self._search(text)
        
        if results:
            self._show_results(results)
        else:
            self._hide_popup()
    
    def _search(self, keyword: str) -> List[tuple]:
        """搜索匹配结果。
        
        Args:
            keyword: 搜索关键词
            
        Returns:
            匹配结果列表 [(signal_id, signal_name, page), ...]
        """
        keyword = keyword.lower().strip()
        results = []
        
        for signal_id, signal_name, page in self._search_data:
            # 匹配信号ID或信号名称
            if keyword in signal_id.lower() or keyword in signal_name.lower():
                results.append((signal_id, signal_name, page))
                if len(results) >= self._max_results:
                    break
        
        return results
    
    def _show_results(self, results: List[tuple]) -> None:
        """显示搜索结果。
        
        Args:
            results: 结果列表
        """
        self._list_widget.clear()
        
        for signal_id, signal_name, page in results:
            item = QListWidgetItem()
            # 显示格式: "信号ID - 信号名称 [页]"
            item.setText(f"{signal_id} - {signal_name} [{page}]")
            item.setData(Qt.ItemDataRole.UserRole, signal_id)  # 存储信号ID
            item.setData(Qt.ItemDataRole.UserRole + 1, page)   # 存储页面
            self._list_widget.addItem(item)
        
        # 显示下拉框
        self._show_popup()
    
    def _show_popup(self) -> None:
        """显示下拉框。"""
        if self._list_widget.count() == 0:
            return
        
        # 计算位置
        global_pos = self._line_edit.mapToGlobal(self._line_edit.rect().bottomLeft())
        
        # 设置大小
        item_height = 35
        list_height = min(self._list_widget.count(), 8) * item_height + 4
        self._list_widget.setFixedHeight(list_height)
        
        self._popup_frame.move(global_pos)
        self._popup_frame.setFixedWidth(self._line_edit.width())
        self._popup_frame.show()
        
        # 安装应用程序级别的事件过滤器（用于检测外部点击）
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().installEventFilter(self)
    
    def _hide_popup(self) -> None:
        """隐藏下拉框。"""
        self._popup_frame.hide()
        
        # 移除应用程序级别的事件过滤器
        from PyQt5.QtWidgets import QApplication
        QApplication.instance().removeEventFilter(self)
    
    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """点击结果项。"""
        signal_id = item.data(Qt.ItemDataRole.UserRole)
        self._hide_popup()
        self._line_edit.clear()
        self.signal_selected.emit(signal_id)
    
    def eventFilter(self, obj, event) -> bool:
        """事件过滤器。"""
        # 处理应用程序级别的事件（外部点击检测）
        if obj is None or obj == self:
            return super().eventFilter(obj, event)
        
        # 检查是否是应用程序事件
        from PyQt5.QtWidgets import QApplication
        if obj == QApplication.instance():
            return self._on_app_event(event)
        
        if event.type() == QEvent.Type.KeyPress:
            if obj == self._line_edit:
                if event.key() == Qt.Key.Key_Down:
                    # 向下键：移动到列表下一项
                    self._navigate_list(1)
                    return True
                elif event.key() == Qt.Key.Key_Up:
                    # 向上键：移动到列表上一项
                    self._navigate_list(-1)
                    return True
                elif event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                    # 回车键：选中当前项
                    self._select_current_item()
                    return True
                elif event.key() == Qt.Key.Key_Escape:
                    # ESC键：隐藏下拉框
                    self._hide_popup()
                    return True
        
        elif event.type() == QEvent.Type.FocusOut:
            # 输入框失去焦点时检查是否需要隐藏下拉框
            if obj == self._line_edit:
                # 延迟检查，让焦点转移完成
                from PyQt5.QtCore import QTimer
                QTimer.singleShot(100, self._check_hide_popup)
        
        return super().eventFilter(obj, event)
    
    def _check_hide_popup(self) -> None:
        """检查是否需要隐藏下拉框。"""
        if not self._popup_frame.isVisible():
            return
        
        # 获取当前焦点控件
        focus_widget = self._line_edit.window().focusWidget()
        
        # 如果焦点在下拉框或列表中，不隐藏
        if focus_widget:
            if focus_widget == self._list_widget:
                return
            if focus_widget == self._line_edit:
                return
            # 检查是否是下拉框的子控件
            parent = focus_widget.parent()
            while parent:
                if parent == self._popup_frame:
                    return
                parent = parent.parent()
        
        # 焦点不在下拉框相关控件中，隐藏
        self._hide_popup()
    
    def _on_app_event(self, event) -> bool:
        """处理应用程序级别的事件。
        
        Args:
            event: 事件对象
            
        Returns:
            是否拦截事件
        """
        if event.type() == QEvent.Type.MouseButtonPress:
            # 检查点击是否在下拉框外部
            global_pos = event.globalPos()
            
            # 检查是否点击在输入框内
            line_edit_rect = self._line_edit.rect()
            line_edit_global_rect = self._line_edit.mapToGlobal(line_edit_rect.topLeft())
            line_edit_global_rect.setWidth(line_edit_rect.width())
            line_edit_global_rect.setHeight(line_edit_rect.height())
            
            if line_edit_global_rect.contains(global_pos):
                return False
            
            # 检查是否点击在下拉框内
            popup_rect = self._popup_frame.rect()
            popup_global_rect = self._popup_frame.mapToGlobal(popup_rect.topLeft())
            popup_global_rect.setWidth(popup_rect.width())
            popup_global_rect.setHeight(popup_rect.height())
            
            if popup_global_rect.contains(global_pos):
                return False
            
            # 点击在外部，隐藏下拉框
            self._hide_popup()
        
        return False
    
    def _navigate_list(self, direction: int) -> None:
        """导航列表项。
        
        Args:
            direction: 方向 (1=向下, -1=向上)
        """
        if not self._popup_frame.isVisible():
            return
        
        current_row = self._list_widget.currentRow()
        count = self._list_widget.count()
        
        if count == 0:
            return
        
        new_row = current_row + direction
        
        if new_row < 0:
            new_row = count - 1
        elif new_row >= count:
            new_row = 0
        
        self._list_widget.setCurrentRow(new_row)
    
    def _select_current_item(self) -> None:
        """选中当前列表项。"""
        current_item = self._list_widget.currentItem()
        if current_item:
            self._on_item_clicked(current_item)


class SearchCBWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SearchComboBox")
        self.resize(400, 300)

        layout = QVBoxLayout()

        search_combo = SearchComboBox()

        # 设置测试数据
        test_data = [
            ("X1-01", "继电器控制信号", "X1"),
            ("X1-02", "温度传感器", "X1"),
            ("X2-01", "压力传感器", "X2"),
            ("X2-02", "流量计", "X2"),
            ("X3-01", "液位传感器", "X3"),
        ]
        search_combo.set_search_data(test_data)

        search_combo.signal_selected.connect(lambda sid: print(f"选中信号: {sid}"))
        layout.addWidget(search_combo)
        self.setLayout(layout)

if __name__ == "__main__":
    import sys
    from PyQt5.QtWidgets import QApplication, QVBoxLayout, QLabel
    
    app = QApplication(sys.argv)

    window=SearchCBWindow()

    window.show()
    sys.exit(app.exec())
