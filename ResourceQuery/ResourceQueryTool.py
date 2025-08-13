import sys
import os
from PyQt5.QtWidgets import QWidget, QApplication, QFileDialog, QComboBox, QSizePolicy, QTableWidgetItem
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QIcon
import pandas as pd

from ResourceQuery.Ui_ResourceQueryTool import Ui_ResourceQueryTool
from pypinyin import lazy_pinyin, Style


PINYIN_AVAILABLE = True

class ResourceQueryTool(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ui = Ui_ResourceQueryTool()
        self.ui.setupUi(self)

        self.df = pd.DataFrame()
        self.filtered_df = pd.DataFrame()
        self.current_excel_path = None  # 启动时不设置默认文件
        self.combo_dims = []

        # 信号绑定
        self.ui.edit_search.textChanged.connect(self._apply_filter)
        self.ui.btn_choose.clicked.connect(self._choose_excel)
        self.ui.btn_reset.clicked.connect(self._reset_filters)
        self.ui.btn_reload.clicked.connect(self._reload_data)

        # 初始化，用户选择文件
        self._update_window_title()
        self._init_filters()
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
        self._init_filters()
        self._apply_filter()

    def _init_filters(self):
        # 清空已有维度控件
        layout = self.ui.dim_layout
        while layout.count():
            item = layout.takeAt(0)
            w = item.widget()
            if w:
                w.deleteLater()
        self.combo_dims.clear()

        # 按Excel列动态创建维度选择
        if self.df.empty:
            return

        max_cols = 5
        row = 0
        col_idx = 0
        for col in self.df.columns:
            combo = QComboBox(self)
            combo.setEditable(False)
            combo.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
            combo.addItem(f'{col}: 全部')
            unique_vals = pd.unique(self.df[col]).tolist()
            for v in unique_vals:
                if pd.isna(v):
                    continue
                combo.addItem(f'{col}: {str(v)}')
            combo.currentIndexChanged.connect(self._apply_filter)
            self.combo_dims.append(combo)
            layout.addWidget(combo, row, col_idx)

            col_idx += 1
            if col_idx >= max_cols:
                col_idx = 0
                row += 1

    def _reset_filters(self):
        self.ui.edit_search.clear()
        for combo in self.combo_dims:
            combo.setCurrentIndex(0)
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
        """将文本转换为拼音首字母组合，例如“中文”->"zw"。"""
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

        该函数根据界面中的筛选条件对原始数据进行过滤，包括维度精确筛选和关键字模糊匹配，
        然后将筛选结果保存到filtered_df属性中并重新渲染表格显示。

        参数:
            self: 类实例，包含以下属性：
                - df: 原始数据框
                - combo_dims: 维度筛选下拉框列表
                - ui.edit_search: 关键字搜索输入框
                - filtered_df: 筛选后的数据框（输出）

        返回值:
            无
        """
        if self.df.empty:
            self.filtered_df = pd.DataFrame()
            self._render_table()
            return

        df = self.df.copy()

        # 维度精确筛选
        for combo in self.combo_dims:
            text = combo.currentText()
            if ': ' in text:
                col, val = text.split(': ', 1)
                col = col.strip()
                if val != '全部':
                    df = df[df[col].astype(str) == val]

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

        该函数将处理后的DataFrame数据渲染到QT表格控件中，并更新状态标签。
        根据数据是否存在和过滤条件，显示相应的表格内容或提示信息。

        参数:
            self: 类实例本身，包含以下属性：
                - filtered_df: 过滤后的DataFrame数据
                - df: 原始DataFrame数据
                - ui.table: QT表格控件
                - ui.label_status: 状态标签控件
                - current_excel_path: 当前Excel文件路径

        返回值:
            无
        """
        df = self.filtered_df
        table = self.ui.table
        table.clear()

        # 处理空数据情况
        if df.empty:
            table.setRowCount(0)
            if not self.df.empty:
                table.setColumnCount(len(self.df.columns))
                table.setHorizontalHeaderLabels(self.df.columns.astype(str).tolist())
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
        table.setHorizontalHeaderLabels(df.columns.astype(str).tolist())

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