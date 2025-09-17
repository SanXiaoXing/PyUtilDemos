import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import glob
from datetime import datetime, timedelta
import re

from Ui_log_viewer import *

LOG_FILES = str(Path(__file__).parent.parent.parent / 'logs')


class LogCheckForm(QWidget, Ui_log_viewer):
    # 类级别常量定义 - 日志级别颜色映射
    LOG_COLORS = {
        'ERROR': '#FF0000',  # 红色
        'CRITICAL': '#8B0000',  # 深红色
        'WARNING': '#FF8C00',  # 橙色
        'INFO': '#0000FF',  # 蓝色
        'DEBUG': '#808080',  # 灰色,
    }
    # 时间戳配色（不影响日志级别颜色）
    TIME_COLOR = '#9b59b6'  # 日期部分使用紫色
    TIME_TIME_COLOR = '#808080'  # 时分秒(.毫秒)使用灰色

    DATE_FORMAT = '%Y-%m-%d'

    def __init__(self):
        super(LogCheckForm, self).__init__()
        self.setupUi(self)
        self.InitUI()

    def InitUI(self):
        self.setWindowTitle('历史日志')
        strdate = datetime.now().strftime(self.DATE_FORMAT)
        self.current_log_content = ""  # 存储当前完整日志内容
        self.batch_mode = False  # 批量删除模式标志

        # 编译日志格式的提取/着色正则，提高识别准确性与性能
        # 提取日志级别（格式：YYYY-MM-DD HH:MM:SS.mmm - 模块名 - 日志级别 - 消息）
        self.re_level_extract = re.compile(
            r'^\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\s+-\s+[^-]+\s+-\s+([A-Z]+)\s+-',
            re.M
        )
        # 颜色渲染：- LEVEL -
        self.re_color_hyphen = re.compile(
            r'^(\d{4}[-/]\d{2}[-/]\d{2}\s+\d{2}:\d{2}:\d{2}(?:\.\d+)?\s+-\s+[^-]+\s+-\s+)([A-Z]+)(\s+-)'
        )
        # 时间戳匹配（分离日期与时间部分）
        self.re_timestamp_parts = re.compile(
            r'^(\d{4}[-/]\d{2}[-/]\d{2})(\s+)(\d{2}:\d{2}:\d{2}(?:\.\d+)?)'
        )

        # 设置列表控件支持多选
        self.listWidget_historyLogs.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # 设置右键菜单
        self.listWidget_historyLogs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget_historyLogs.customContextMenuRequested.connect(self.Show_Context_Menu)
        self.listWidget_historyLogs.itemClicked.connect(self.On_History_Log_Clicked)

        # 初始化加载与信号连接（之前误删，现恢复）
        self.Get_Log_File_By_Date(strdate)
        self.Set_Log_Date()
        self.calendarWidget.selectionChanged.connect(
            lambda: self.Get_Log_File_By_Date(self.calendarWidget.selectedDate().toString("yyyy-MM-dd"))
        )
        self.comboBox_logType.currentTextChanged.connect(self.Filter_Log_By_Type)

        # 连接按钮事件
        self.pushButton_batchMode.clicked.connect(self.Enter_Batch_Mode)
        self.pushButton_deleteSelected.clicked.connect(self.Delete_Selected_Logs)
        self.pushButton_cancelBatch.clicked.connect(self.Exit_Batch_Mode)
        self.pushButton_deleteByDate.clicked.connect(self.Delete_Logs_By_Date)

        # 设置按钮样式
        self.Set_Button_Styles()

        self.Load_History_Log_List()
        # 设置应用图标
        self._set_window_icon()

    def _set_window_icon(self):
        """设置窗口图标"""
        try:
            icon_path = str(Path(__file__).parent.parent.parent / "assets" / "icon" / "文件文档.svg")
            if os.path.exists(icon_path):
                self.setWindowIcon(QIcon(icon_path))
        except Exception as e:
            print(f"设置图标失败: {e}")

    def Set_Log_Date(self):
        log_files = glob.glob(os.path.join(LOG_FILES, "*.log"))
        for logfile in log_files:
            try:
                date_str = os.path.basename(logfile)
                date_parts = date_str.split('_')
                if len(date_parts) < 2:
                    continue  # 跳过不符合格式的文件名
                date_str = date_parts[1].split('.')[0]
                date = datetime.strptime(date_str, self.DATE_FORMAT).date()
                date_format_obj = QTextCharFormat()
                date_format_obj.setBackground(QColor(180, 238, 180))
                self.calendarWidget.setDateTextFormat(date, date_format_obj)
            except (IndexError, ValueError, AttributeError):
                # 忽略无法解析的文件名或日期格式错误
                continue

    def Get_Log_File_By_Date(self, date):
        log_files = glob.glob(os.path.join(LOG_FILES, "*.log"))
        for logfile in log_files:
            if date in logfile:
                with open(logfile, 'r', encoding='utf-8') as file:
                    self.current_log_content = file.read()
                    self.Update_Log_Types()  # 动态更新日志类型
                    self.Filter_Log_By_Type(self.comboBox_logType.currentText())
                return
        # 如果没有找到对应日期的日志文件，清空显示
        self.current_log_content = ""
        self.plainTextEdit_log.clear()
        self.Update_Log_Types()  # 清空日志类型

    def Update_Log_Types(self):
        """动态扫描当前日志内容中的所有日志类型并更新下拉框"""
        # 保存当前选择的类型
        current_selection = self.comboBox_logType.currentText()

        # 清空下拉框
        self.comboBox_logType.clear()

        # 添加"全部"选项
        self.comboBox_logType.addItem("全部")

        if self.current_log_content:
            # 提取日志级别
            # 日志格式: YYYY-MM-DD/YY/MM/DD HH:MM:SS(.mmm) - 模块名 - 日志级别 - 消息
            log_levels = set()
            for m in self.re_level_extract.finditer(self.current_log_content):
                level = m.group(1)
                if level:
                    log_levels.add(level.strip())

            # 按字母顺序排序并添加到下拉框
            for level in sorted(log_levels):
                self.comboBox_logType.addItem(level)

        # 尝试恢复之前的选择，如果不存在则选择"全部"
        index = self.comboBox_logType.findText(current_selection)
        if index >= 0:
            self.comboBox_logType.setCurrentIndex(index)
        else:
            self.comboBox_logType.setCurrentIndex(0)  # 选择"全部"

    def Filter_Log_By_Type(self, log_type):
        """根据日志类型过滤日志内容并应用颜色"""
        if not self.current_log_content:
            return

        self.plainTextEdit_log.clear()

        if log_type == "全部":
            # 显示所有日志并应用颜色
            self.Apply_Colors_To_Content(self.current_log_content)
        else:
            # 按类型过滤日志并应用颜色
            lines = self.current_log_content.split('\n')
            filtered_lines = []

            for line in lines:
                # 使用正则抽取本行日志级别，避免误匹配
                m = self.re_level_extract.search(line)
                if not m:
                    continue
                level = m.group(1)
                if level == log_type:
                    filtered_lines.append(line)

            filtered_content = '\n'.join(filtered_lines)
            self.Apply_Colors_To_Content(filtered_content)

    def Apply_Colors_To_Content(self, content):
        """为指定内容应用颜色 - 优化版本"""

        def html_escape(text):
            """HTML转义函数，保持原始空格和换行"""
            return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')

        lines = content.split('\n')

        # 检查内容大小，如果过大则使用简化渲染
        if len(lines) > 5000:  # 超过5000行使用简化模式
            self.Apply_Colors_Simple(content)
            return

        # 清空文本框并设置HTML模式
        self.plainTextEdit_log.clear()

        # 批量构建HTML内容，避免频繁的appendHtml调用
        batch_size = 500  # 每批处理500行

        for i in range(0, len(lines), batch_size):
            batch_lines = lines[i:i + batch_size]
            batch_html = []

            for line in batch_lines:
                if line.strip():  # 跳过空行
                    # 先进行HTML转义
                    escaped_line = html_escape(line)
                    # 日期与时间分别着色并斜体：日期(紫色) + 空白 + 时间(灰色)
                    m_ts = self.re_timestamp_parts.search(line)
                    if m_ts:
                        def _ts_replace(match):
                            d = match.group(1)
                            ws = match.group(2)
                            t = match.group(3)
                            return (
                                f'<span style="color: {self.TIME_COLOR}; font-style: italic;">{d}</span>'
                                f'{ws}'
                                f'<span style="color: {self.TIME_TIME_COLOR}; font-style: italic;">{t}</span>'
                            )

                        colored_line = self.re_timestamp_parts.sub(_ts_replace, escaped_line, count=1)
                    else:
                        colored_line = escaped_line

                    # 处理日志格式: - LEVEL -（保持不变）
                    m = self.re_color_hyphen.search(line)  # 在原始行上匹配
                    if m:
                        lvl = m.group(2)
                        color = self.LOG_COLORS.get(lvl)
                        if color:
                            pattern = re.compile(f'(-\\s+[^-]+\\s+-\\s+)({re.escape(lvl)})(\\s+-)')
                            colored_line = pattern.sub(f'\\1<span style="color: {color}">\\2</span>\\3', colored_line)

                    # 包装在保持空白和等宽字体的span中
                    formatted_line = f'<span style="white-space: pre; font-family: Consolas, Monaco, monospace;">{colored_line}</span>'
                    batch_html.append(formatted_line)
                else:
                    # 保留空行
                    batch_html.append('<br>')

            # 批量添加到文本框
            if batch_html:
                html_content = '<br>'.join(batch_html)
                self.plainTextEdit_log.appendHtml(html_content)

            # 每批处理后刷新UI，保持响应性
            QtWidgets.QApplication.processEvents()

    def Apply_Colors_Simple(self, content):
        """简化的颜色渲染模式，用于大量日志"""
        # 对于大量日志，使用纯文本模式以提高性能
        self.plainTextEdit_log.clear()
        self.plainTextEdit_log.appendPlainText("日志内容过多，使用简化显示模式...\n\n")

        # 只显示前2000行和后1000行
        lines = content.split('\n')
        if len(lines) > 3000:
            preview_lines = lines[:2000] + ['\n... 省略中间部分 ...\n'] + lines[-1000:]
        else:
            preview_lines = lines

        # 分批显示，避免一次性加载过多内容
        batch_size = 1000
        for i in range(0, len(preview_lines), batch_size):
            batch = preview_lines[i:i + batch_size]
            self.plainTextEdit_log.appendPlainText('\n'.join(batch))
            QtWidgets.QApplication.processEvents()

    def Load_History_Log_List(self):
        """加载历史日志文件列表 - 优化版本"""
        try:
            self.listWidget_historyLogs.clear()
            log_files = glob.glob(os.path.join(LOG_FILES, "*.log"))
            log_files.sort()  # 按文件名排序

            # 先快速加载文件名，后续异步加载详细信息
            for logfile in log_files:
                try:
                    # 提取日期信息
                    date = os.path.basename(logfile).split('_')[1].split('.')[0]

                    # 获取文件大小作为快速指标
                    file_size = os.path.getsize(logfile)
                    size_kb = file_size // 1024

                    # 创建显示文本（先显示文件大小，避免读取文件内容）
                    display_text = f"{date} ({size_kb}KB)"

                    # 添加到列表控件
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, date)  # 存储日期信息
                    item.setData(Qt.UserRole + 1, logfile)  # 存储文件路径

                    # 根据批量模式设置复选框
                    if self.batch_mode:
                        item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                        item.setCheckState(Qt.Unchecked)
                    else:
                        item.setFlags(item.flags() & ~Qt.ItemIsUserCheckable)

                    self.listWidget_historyLogs.addItem(item)

                except Exception as e:
                    print(f"处理文件 {logfile} 时出错: {e}")

            # 异步更新详细信息（行数统计）
            QtCore.QTimer.singleShot(100, self.Update_Log_Counts_Async)

        except Exception as e:
            print(f"加载历史日志列表时出错: {e}")

    def Update_Log_Counts_Async(self):
        """异步更新日志行数统计"""
        try:
            for i in range(self.listWidget_historyLogs.count()):
                item = self.listWidget_historyLogs.item(i)
                if item:
                    logfile = item.data(Qt.UserRole + 1)
                    date = item.data(Qt.UserRole)

                    try:
                        # 使用更高效的行数统计方法
                        log_count = self.Count_Log_Lines_Fast(logfile)

                        # 更新显示文本
                        display_text = f"{date} ({log_count}条日志)"
                        item.setText(display_text)

                        # 强制刷新UI
                        QtWidgets.QApplication.processEvents()

                    except Exception as e:
                        print(f"更新文件 {logfile} 行数时出错: {e}")

        except Exception as e:
            print(f"异步更新日志行数时出错: {e}")

    def Count_Log_Lines_Fast(self, filepath):
        """快速统计日志文件行数"""
        try:
            count = 0
            with open(filepath, 'r', encoding='utf-8') as file:
                # 使用缓冲读取，避免一次性加载整个文件
                buffer_size = 8192
                while True:
                    buffer = file.read(buffer_size)
                    if not buffer:
                        break
                    count += buffer.count('\n')
            return count
        except Exception as e:
            print(f"统计文件 {filepath} 行数时出错: {e}")
            return 0

    def On_History_Log_Clicked(self, item):
        """处理历史日志列表点击事件"""
        try:
            # 获取存储的日期信息
            date = item.data(Qt.UserRole)
            if date:
                # 临时断开日历信号连接，避免循环触发
                self.calendarWidget.selectionChanged.disconnect()

                # 设置日历控件到对应日期
                selected_date = QDate.fromString(date, "yyyy-MM-dd")
                if selected_date.isValid():
                    self.calendarWidget.setSelectedDate(selected_date)

                # 重新连接信号
                self.calendarWidget.selectionChanged.connect(
                    lambda: self.Get_Log_File_By_Date(self.calendarWidget.selectedDate().toString("yyyy-MM-dd")))

                # 加载对应日期的日志
                self.Get_Log_File_By_Date(date)
        except Exception as e:
            print(f"处理历史日志点击事件时出错: {e}")

    def Show_Context_Menu(self, position):
        """显示右键菜单"""
        item = self.listWidget_historyLogs.itemAt(position)
        if item:
            context_menu = QMenu(self)
            delete_action = QAction("删除此日志文件", self)
            delete_action.triggered.connect(lambda: self.Delete_Single_Log(item))
            context_menu.addAction(delete_action)
            context_menu.exec_(self.listWidget_historyLogs.mapToGlobal(position))

    def _delete_log_files(self, files_to_delete, operation_name="删除"):
        """通用的文件删除方法，减少重复代码"""
        deleted_count = 0
        failed_files = []
        current_date = self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
        need_clear_display = False

        for file_info in files_to_delete:
            try:
                if isinstance(file_info, tuple):
                    logfile, date_str = file_info
                else:
                    # 处理单个文件删除的情况
                    logfile = file_info.data(Qt.UserRole + 1)
                    date_str = file_info.data(Qt.UserRole)

                if os.path.exists(logfile):
                    os.remove(logfile)
                    deleted_count += 1

                    # 检查是否需要清空当前显示
                    if date_str == current_date:
                        need_clear_display = True
                else:
                    failed_files.append(f'{date_str} (文件不存在)')

            except Exception as e:
                failed_files.append(f'{date_str} (删除失败: {str(e)})')

        # 重新加载列表
        self.Load_History_Log_List()

        # 清空当前显示（如果需要）
        if need_clear_display:
            self.current_log_content = ""
            self.plainTextEdit_log.clear()
            self.Update_Log_Types()

        # 更新日历显示
        self.Set_Log_Date()

        return deleted_count, failed_files

    def Delete_Single_Log(self, item):
        """删除单个日志文件"""
        try:
            date = item.data(Qt.UserRole)
            logfile = item.data(Qt.UserRole + 1)

            # 确认删除
            reply = QMessageBox.question(self, '确认删除',
                                         f'确定要删除日志文件 "{date}" 吗？\n\n文件路径: {logfile}\n\n此操作不可撤销！',
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.Yes:
                deleted_count, failed_files = self._delete_log_files([item])

                if failed_files:
                    QMessageBox.warning(self, '删除失败', f'文件不存在: {logfile}')
                else:
                    QMessageBox.information(self, '删除成功', f'日志文件 "{date}" 已删除')

        except Exception as e:
            QMessageBox.critical(self, '删除失败', f'删除文件时出错: {str(e)}')

    def Delete_Selected_Logs(self):
        """批量删除选中的日志文件"""
        try:
            # 在批量模式下，检查复选框状态
            selected_items = []
            for i in range(self.listWidget_historyLogs.count()):
                item = self.listWidget_historyLogs.item(i)
                if item.checkState() == Qt.Checked:
                    selected_items.append(item)

            if not selected_items:
                QMessageBox.information(self, '提示', '请先勾选要删除的日志文件')
                return

            # 确认删除
            file_list = [item.data(Qt.UserRole) for item in selected_items]
            reply = QMessageBox.question(self, '确认批量删除',
                                         f'确定要删除以下 {len(selected_items)} 个日志文件吗？\n\n' +
                                         '\n'.join(file_list) +
                                         '\n\n此操作不可撤销！',
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.Yes:
                deleted_count, failed_files = self._delete_log_files(selected_items)

                # 显示结果
                if failed_files:
                    QMessageBox.warning(self, '批量删除完成',
                                        f'成功删除 {deleted_count} 个文件\n\n失败的文件:\n' +
                                        '\n'.join(failed_files))
                else:
                    QMessageBox.information(self, '批量删除成功', f'成功删除 {deleted_count} 个日志文件')

        except Exception as e:
            QMessageBox.critical(self, '批量删除失败', f'批量删除时出错: {str(e)}')

    def Enter_Batch_Mode(self):
        """进入批量删除模式"""
        self.batch_mode = True

        # 切换按钮显示状态
        self.pushButton_batchMode.setVisible(False)
        self.pushButton_deleteSelected.setVisible(True)
        self.pushButton_cancelBatch.setVisible(True)

        # 重新加载列表以显示复选框
        self.Load_History_Log_List()

        # 禁用右键菜单和单击事件
        self.listWidget_historyLogs.setContextMenuPolicy(Qt.NoContextMenu)
        self.listWidget_historyLogs.itemClicked.disconnect()

    def Exit_Batch_Mode(self):
        """退出批量删除模式"""
        self.batch_mode = False

        # 切换按钮显示状态
        self.pushButton_batchMode.setVisible(True)
        self.pushButton_deleteSelected.setVisible(False)
        self.pushButton_cancelBatch.setVisible(False)

        # 重新加载列表以隐藏复选框
        self.Load_History_Log_List()

        # 恢复右键菜单和单击事件
        self.listWidget_historyLogs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget_historyLogs.itemClicked.connect(self.On_History_Log_Clicked)

    def Delete_Logs_By_Date(self):
        """按日期范围删除日志文件"""
        try:
            # 获取用户输入的天数
            days, ok = QInputDialog.getInt(self, '按日期删除日志',
                                           '请输入要删除多少天前的日志文件：\n(例如：输入7表示删除7天前及更早的日志)',
                                           7, 1, 365, 1)

            if not ok:
                return

            # 计算截止日期
            cutoff_date = datetime.now() - timedelta(days=days)
            cutoff_date_str = cutoff_date.strftime(self.DATE_FORMAT)

            # 查找符合条件的日志文件
            log_files = glob.glob(os.path.join(LOG_FILES, "*.log"))
            files_to_delete = []

            for logfile in log_files:
                try:
                    # 从文件名提取日期
                    filename = os.path.basename(logfile)
                    date_str = filename.split('_')[1].split('.')[0]
                    file_date = datetime.strptime(date_str, self.DATE_FORMAT)

                    # 如果文件日期早于截止日期，加入删除列表
                    if file_date < cutoff_date:
                        files_to_delete.append((logfile, date_str))

                except Exception as e:
                    print(f"解析文件日期时出错 {logfile}: {e}")
                    continue

            if not files_to_delete:
                QMessageBox.information(self, '提示', f'没有找到{days}天前的日志文件')
                return

            # 确认删除
            file_list = [date for _, date in files_to_delete]
            reply = QMessageBox.question(self, '确认按日期删除',
                                         f'找到 {len(files_to_delete)} 个{days}天前的日志文件：\n\n' +
                                         '\n'.join(file_list[:10]) +
                                         (f'\n... 还有{len(file_list) - 10}个文件' if len(file_list) > 10 else '') +
                                         f'\n\n确定要删除{cutoff_date_str}之前的所有日志文件吗？\n此操作不可撤销！',
                                         QMessageBox.Yes | QMessageBox.No,
                                         QMessageBox.No)

            if reply == QMessageBox.Yes:
                deleted_count, failed_files = self._delete_log_files(files_to_delete)

                # 显示结果
                if failed_files:
                    QMessageBox.warning(self, '按日期删除完成',
                                        f'成功删除 {deleted_count} 个文件\n\n失败的文件:\n' +
                                        '\n'.join(failed_files))
                else:
                    QMessageBox.information(self, '按日期删除成功', f'成功删除 {deleted_count} 个{days}天前的日志文件')

        except Exception as e:
            QMessageBox.critical(self, '按日期删除失败', f'按日期删除时出错: {str(e)}')

    def Enter_Batch_Mode(self):
        """进入批量删除模式"""
        self.batch_mode = True

        # 切换按钮显示状态
        self.pushButton_batchMode.setVisible(False)
        self.pushButton_deleteSelected.setVisible(True)
        self.pushButton_cancelBatch.setVisible(True)

        # 重新加载列表以显示复选框
        self.Load_History_Log_List()

        # 禁用右键菜单和单击事件
        self.listWidget_historyLogs.setContextMenuPolicy(Qt.NoContextMenu)
        self.listWidget_historyLogs.itemClicked.disconnect()

    def Exit_Batch_Mode(self):
        """退出批量删除模式"""
        self.batch_mode = False

        # 切换按钮显示状态
        self.pushButton_batchMode.setVisible(True)
        self.pushButton_deleteSelected.setVisible(False)
        self.pushButton_cancelBatch.setVisible(False)

        # 重新加载列表以隐藏复选框
        self.Load_History_Log_List()

        # 恢复右键菜单和单击事件
        self.listWidget_historyLogs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget_historyLogs.itemClicked.connect(self.On_History_Log_Clicked)

    def Set_Button_Styles(self):
        """设置按钮样式"""
        # 批量模式按钮样式 - 蓝色背景
        batch_style = """
            QPushButton {
                background-color: #3498db;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #2980b9;
            }
            QPushButton:pressed {
                background-color: #21618c;
            }
        """

        # 删除选中按钮样式 - 红色背景
        delete_style = """
            QPushButton {
                background-color: #e74c3c;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #c0392b;
            }
            QPushButton:pressed {
                background-color: #a93226;
            }
        """

        # 取消按钮样式 - 灰色背景
        cancel_style = """
            QPushButton {
                background-color: #95a5a6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7f8c8d;
            }
            QPushButton:pressed {
                background-color: #6c7b7d;
            }
        """

        # 按时间删除按钮样式 - 紫色背景
        date_delete_style = """
            QPushButton {
                background-color: #9b59b6;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #8e44ad;
            }
            QPushButton:pressed {
                background-color: #7d3c98;
            }
        """

        # 应用样式
        self.pushButton_deleteSelected.setStyleSheet(delete_style)
        self.pushButton_batchMode.setStyleSheet(batch_style)
        self.pushButton_cancelBatch.setStyleSheet(cancel_style)
        self.pushButton_deleteByDate.setStyleSheet(date_delete_style)


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    Tool = LogCheckForm()
    Tool.show()
    sys.exit(app.exec())