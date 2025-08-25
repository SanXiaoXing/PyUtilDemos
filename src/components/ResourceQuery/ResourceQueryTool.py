import sys
import os
from PyQt5.QtWidgets import (QWidget, QApplication, QFileDialog, QTableWidgetItem, QHeaderView, QCheckBox,
                             QVBoxLayout, QDialog, QPushButton, QHBoxLayout, QScrollArea, QFrame)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
import pandas as pd

from src.components.ResourceQuery.Ui_ResourceQueryTool import Ui_ResourceQueryTool
from pypinyin import lazy_pinyin, Style

PINYIN_AVAILABLE = True


class FilterDialog(QDialog):
    """表头筛选对话框"""
    filterChanged = pyqtSignal(str, list)  # column_name, selected_values

    def __init__(self, column_name, unique_values, selected_values=None, parent=None):
        super().__init__(parent)
        self.column_name = column_name
        self.unique_values = unique_values
        self.selected_values = selected_values or []
        self.checkboxes = []

        self.setWindowTitle(f"筛选 - {column_name}")
        self.setFixedSize(300, 400)
        self.setupUI()

    def setupUI(self):
        layout = QVBoxLayout(self)

        # 全选/取消全选按钮
        button_layout = QHBoxLayout()
        self.select_all_btn = QPushButton("全选")
        self.deselect_all_btn = QPushButton("取消全选")
        self.select_all_btn.clicked.connect(self.select_all)
        self.deselect_all_btn.clicked.connect(self.deselect_all)
        button_layout.addWidget(self.select_all_btn)
        button_layout.addWidget(self.deselect_all_btn)
        layout.addLayout(button_layout)

        # 滚动区域包含筛选项
        scroll = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)

        # 添加"全部"选项
        all_checkbox = QCheckBox("(全部)")
        all_checkbox.setChecked(len(self.selected_values) == 0 or len(self.selected_values) == len(self.unique_values))
        all_checkbox.stateChanged.connect(self.all_checkbox_changed)
        scroll_layout.addWidget(all_checkbox)
        self.all_checkbox = all_checkbox

        # 添加分隔线
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setFrameShadow(QFrame.Sunken)
        scroll_layout.addWidget(line)

        # 添加各个值的选项
        for value in sorted(self.unique_values, key=lambda x: str(x)):
            if pd.isna(value):
                continue
            checkbox = QCheckBox(str(value))
            checkbox.setChecked(len(self.selected_values) == 0 or str(value) in self.selected_values)
            scroll_layout.addWidget(checkbox)
            self.checkboxes.append(checkbox)

        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # 确定/取消按钮
        button_layout2 = QHBoxLayout()
        self.ok_btn = QPushButton("确定")
        self.cancel_btn = QPushButton("取消")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        button_layout2.addWidget(self.ok_btn)
        button_layout2.addWidget(self.cancel_btn)
        layout.addLayout(button_layout2)

    def all_checkbox_changed(self, state):
        """全部选项变化时的处理"""
        checked = state == Qt.Checked
        for checkbox in self.checkboxes:
            checkbox.setChecked(checked)

    def select_all(self):
        """全选"""
        self.all_checkbox.setChecked(True)
        for checkbox in self.checkboxes:
            checkbox.setChecked(True)

    def deselect_all(self):
        """取消全选"""
        self.all_checkbox.setChecked(False)
        for checkbox in self.checkboxes:
            checkbox.setChecked(False)

    def get_selected_values(self):
        """获取选中的值"""
        if self.all_checkbox.isChecked():
            return []  # 空列表表示全选
        selected = []
        for checkbox in self.checkboxes:
            if checkbox.isChecked():
                selected.append(checkbox.text())
        return selected

    def accept(self):
        """确定按钮点击"""
        selected = self.get_selected_values()
        self.filterChanged.emit(self.column_name, selected)
        super().accept()


class CustomHeaderView(QHeaderView):
    """自定义表头，支持筛选功能"""
    filterClicked = pyqtSignal(int, str)  # column_index, column_name

    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.setSectionsClickable(True)
        self.filters = {}  # 存储每列的筛选条件

    def set_filter(self, column_name, selected_values):
        """设置列筛选条件"""
        if not selected_values or len(selected_values) == 0:
            # 空列表表示无筛选或全选
            if column_name in self.filters:
                del self.filters[column_name]
        else:
            self.filters[column_name] = selected_values

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() in (Qt.RightButton, Qt.LeftButton):
            # 点击显示筛选菜单
            index = self.logicalIndexAt(event.pos())
            if index >= 0:
                if isinstance(self.parent(), QWidget):
                    try:
                        column_name = self.parent().horizontalHeaderItem(index).text()
                    except Exception:
                        column_name = f"Column {index}"
                else:
                    column_name = f"Column {index}"
                # 移除筛选指示符
                if column_name.endswith(" ⏷"):
                    column_name = column_name[:-2].strip()
                self.filterClicked.emit(index, column_name)
                return
        super().mousePressEvent(event)


class ResourceQueryTool(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ResourceQueryTool()
        self.ui.setupUi(self)

        self.df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()
        self.current_excel_path = None  # 启动时不设置默认文件
        self.column_filters = {}  # 存储每列的筛选条件

        # 设置自定义表头
        self.header = CustomHeaderView(Qt.Horizontal, self.ui.table)
        self.ui.table.setHorizontalHeader(self.header)
        self.header.setSectionResizeMode(QHeaderView.ResizeToContents)
        self.header.filterClicked.connect(self.show_column_filter)

        # 信号绑定
        self.ui.edit_search.textChanged.connect(self._apply_filter)
        self.ui.btn_choose.clicked.connect(self._choose_excel)
        self.ui.btn_reset.clicked.connect(self._reset_filters)
        self.ui.btn_reload.clicked.connect(self._reload_data)

        # 初始化，用户选择文件
        self._update_window_title()
        self._apply_filter()

        try:
            icon_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                                        "assets", "icon", "中央处理器.svg")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"设置图标失败: {e}")

    def _update_window_title(self):
        if self.current_excel_path:
            base = os.path.basename(self.current_excel_path)
            self.setWindowTitle(f"资源索引查询 - {base}")
        else:
            self.setWindowTitle("资源索引查询")

    def _load_data(self):
        try:
            if not self.current_excel_path:
                self.df = pd.DataFrame()
                self.ui.label_status.setText('未选择资源表文件')
                self._render_table()  # 清空表格头
                return
            self.df = pd.read_excel(self.current_excel_path)
            self.ui.label_status.setText('加载完成')
        except Exception as e:
            self.df = pd.DataFrame()
            self.ui.label_status.setText(f'加载失败：{e}')
        finally:
            self._update_window_title()

    def _reload_data(self):
        self._load_data()
        self._reset_filters()
        self._apply_filter()

    def show_column_filter(self, column_index, column_name):
        """显示列筛选对话框"""
        if self.df.empty or column_name not in self.df.columns:
            return

        # 基于当前过滤结果（排除本列的筛选）计算唯一值，保证用户可以多次精炼筛选
        df_temp = self.df.copy()
        # 应用除当前列外的列头筛选
        for col, vals in self.column_filters.items():
            if col == column_name:
                continue
            if col in df_temp.columns and vals:
                df_temp = df_temp[df_temp[col].astype(str).isin(vals)]
        # 应用关键字过滤
        kw = self.ui.edit_search.text().strip()
        if kw and not df_temp.empty:
            mask = pd.Series([False] * len(df_temp))
            kw_py_full = self._to_pinyin(kw)
            kw_py_init = self._to_pinyin_initials(kw)
            for c in df_temp.columns:
                series = df_temp[c].astype(str)
                col_mask = series.str.contains(kw, case=False, na=False)
                if PINYIN_AVAILABLE:
                    def cell_match(cell):
                        if pd.isna(cell):
                            return False
                        s = str(cell)
                        if any('\u4e00' <= ch <= '\u9fff' for ch in s):
                            py_full = ''.join(lazy_pinyin(s)).lower()
                            if kw.lower() in py_full or kw_py_full in py_full:
                                return True
                            py_init = ''.join(lazy_pinyin(s, style=Style.FIRST_LETTER)).lower()
                            if kw.lower() in py_init or kw_py_init in py_init:
                                return True
                        return False

                    col_mask |= series.apply(cell_match)
                mask |= col_mask
            df_temp = df_temp[mask]

        unique_values = pd.unique(df_temp[column_name]).tolist() if column_name in df_temp.columns else []
        selected_values = self.column_filters.get(column_name, [])

        dialog = FilterDialog(column_name, unique_values, selected_values, self)
        dialog.filterChanged.connect(self.apply_column_filter)
        dialog.exec_()

    def apply_column_filter(self, column_name, selected_values):
        """应用列筛选"""
        if not selected_values or len(selected_values) == 0:
            # 移除筛选
            if column_name in self.column_filters:
                del self.column_filters[column_name]
        else:
            self.column_filters[column_name] = selected_values

        # 更新表头样式（可选：显示筛选状态）
        self.header.set_filter(column_name, selected_values)

        # 重新应用筛选
        self._apply_filter()

    def _reset_filters(self):
        self.ui.edit_search.clear()
        self.column_filters.clear()
        self.header.filters.clear()
        self._apply_filter()

    def _to_pinyin(self, text: str) -> str:
        """
        将文本转换为连续拼音字符串（不含空格），仅当 pypinyin 可用时；否则返回原文本。
        同时提供首字母形式，便于模糊匹配。
        """
        if not isinstance(text, str):
            text = str(text)
        if not PINYIN_AVAILABLE:
            return text.lower()
        pys = lazy_pinyin(text)
        return ''.join(pys).lower()

    def _to_pinyin_initials(self, text: str) -> str:
        """将文本转换为拼音首字母组合，例如"中文"->"zw"。"""
        if not isinstance(text, str):
            text = str(text)
        if not PINYIN_AVAILABLE:
            return text.lower()
        initials = lazy_pinyin(text, style=Style.FIRST_LETTER)
        return ''.join(initials).lower()

    def _match_with_pinyin(self, cell_text: str, keyword: str) -> bool:
        """
        进行包含匹配，支持：
        - 原文包含（不区分大小写）
        - 拼音全拼包含
        - 拼音首字母包含
        """
        if not isinstance(cell_text, str):
            cell_text = str(cell_text)
        if not isinstance(keyword, str):
            keyword = str(keyword)
        s = cell_text.lower()
        kw = keyword.lower()
        if kw in s:
            return True
        # 当包含中文时，尝试拼音匹配
        if any('\u4e00' <= ch <= '\u9fff' for ch in cell_text):
            py_full = self._to_pinyin(cell_text)
            if kw in py_full:
                return True
            py_init = self._to_pinyin_initials(cell_text)
            if kw in py_init:
                return True
        return False

    def _apply_filter(self):
        """
        应用筛选条件到数据框并更新显示表格

        该函数根据界面中的筛选条件对原始数据进行过滤，包括列头筛选和关键字模糊匹配，
        然后将筛选结果保存到filtered_df属性中并重新渲染表格显示。
        """
        if self.df.empty:
            self.filtered_df = pd.DataFrame()
            self._render_table()
            return

        df = self.df.copy()

        # 应用列头筛选
        for column_name, selected_values in self.column_filters.items():
            if column_name in df.columns and selected_values:
                df = df[df[column_name].astype(str).isin(selected_values)]

        # 关键字模糊匹配（任意列包含），扩展支持拼音
        kw = self.ui.edit_search.text().strip()
        if kw:
            mask = pd.Series([False] * len(df))
            # 预处理：当关键词是中文时，构建其拼音与首字母，便于反向匹配
            kw_py_full = self._to_pinyin(kw)
            kw_py_init = self._to_pinyin_initials(kw)
            for c in df.columns:
                series = df[c].astype(str)
                # 先做原文包含（忽略大小写）
                col_mask = series.str.contains(kw, case=False, na=False)
                # 再做拼音匹配：仅对包含中文的单元格做转换以降低开销
                if PINYIN_AVAILABLE:
                    # 生成该列的拼音缓存以减少重复转换
                    def cell_match(cell):
                        if pd.isna(cell):
                            return False
                        s = str(cell)
                        # 原文匹配已做过，这里只处理拼音情况
                        if any('\u4e00' <= ch <= '\u9fff' for ch in s):
                            py_full = ''.join(lazy_pinyin(s)).lower()
                            if kw.lower() in py_full or kw_py_full in py_full:
                                return True
                            py_init = ''.join(lazy_pinyin(s, style=Style.FIRST_LETTER)).lower()
                            if kw.lower() in py_init or kw_py_init in py_init:
                                return True
                        return False
                    col_mask |= series.apply(cell_match)
                mask |= col_mask
            df = df[mask]

        self.filtered_df = df
        self._render_table()

    def _render_table(self):
        """
        渲染表格数据到UI界面
        """
        df = self.filtered_df
        table = self.ui.table
        table.clearContents()

        # 处理空数据情况
        if df.empty:
            table.setRowCount(0)
            if not self.df.empty:
                table.setColumnCount(len(self.df.columns))
                # 设置表头并标识过滤状态
                headers = []
                for col in self.df.columns.astype(str).tolist():
                    if col in self.column_filters:
                        headers.append(f"{col} ⏷")
                    else:
                        headers.append(col)
                table.setHorizontalHeaderLabels(headers)
                self.ui.label_status.setText('共 0 条')
            else:
                table.setColumnCount(0)
                if not self.current_excel_path:
                    self.ui.label_status.setText('请选择资源表文件')
                else:
                    self.ui.label_status.setText('无数据')
            return

        # 设置表格行列数和表头
        table.setColumnCount(len(df.columns))
        table.setRowCount(len(df))
        # 设置表头并标识过滤状态
        headers = []
        for col in df.columns.astype(str).tolist():
            if col in self.column_filters:
                headers.append(f"{col} ⏷")
            else:
                headers.append(col)
        table.setHorizontalHeaderLabels(headers)

        # 填充表格数据
        for i, (_, row) in enumerate(df.iterrows()):
            for j, col in enumerate(df.columns):
                val = row[col]
                text = '' if pd.isna(val) else str(val)
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                item.setFont(QFont('Arial', 10))
                table.setItem(i, j, item)

        # 调整列宽并更新状态标签
        table.resizeColumnsToContents()
        self.ui.label_status.setText(f'共 {len(df)} 条')

    def _choose_excel(self):
        if self.current_excel_path:
            start_dir = os.path.dirname(self.current_excel_path)
        else:
            start_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'configFiles')
            if not os.path.exists(start_dir):
                start_dir = os.getcwd()
        path, _ = QFileDialog.getOpenFileName(self, '选择资源表 Excel 文件', start_dir, 'Excel 文件 (*.xlsx *.xls)')
        if not path:
            return
        self.current_excel_path = path
        self._reload_data()
        self._update_window_title()


if __name__ == '__main__':
    app = QApplication(sys.argv)
    w = ResourceQueryTool()
    w.show()
    sys.exit(app.exec_())