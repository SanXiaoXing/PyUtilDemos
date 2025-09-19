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

from src.components.LogViewer.Ui_log_viewer import *
from src.utils.LogDisplayUtil import log_display_util

LOG_FILES = str(Path(__file__).parent.parent.parent / 'logs')

class LogCheckForm(QWidget, Ui_log_viewer):
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
        
        # 使用统一的日志显示工具类，无需重复定义正则表达式
        
        # 设置列表控件支持多选
        self.listWidget_historyLogs.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # 拖拽勾选：初始化并安装事件过滤器（仅在批量模式生效）
        self._drag_check_active = False
        self._drag_check_target_state = None
        self._drag_checked_indexes = set()
        self._drag_autoscroll_margin = 24  # 视口上下边缘触发自动滚动的边距（像素）
        self.listWidget_historyLogs.setMouseTracking(True)
        self.listWidget_historyLogs.viewport().installEventFilter(self)
        
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

    def Get_Log_File_By_Date(self,date):
        log_files=glob.glob(os.path.join(LOG_FILES,"*.log"))
        for logfile in log_files:
            if date in logfile:
                with open(logfile,'r',encoding='utf-8') as file:
                    self.current_log_content=file.read()
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
            # 使用统一工具类提取日志级别
            log_levels = log_display_util.get_log_levels_from_content(self.current_log_content)
            
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
            # 使用统一工具类按类型过滤日志并应用颜色
            filtered_content = log_display_util.filter_logs_by_level(self.current_log_content, log_type)
            self.Apply_Colors_To_Content(filtered_content)
    
    def Apply_Colors_To_Content(self, content):
        """应用颜色到日志内容 - 使用统一工具类"""
        # 使用统一的日志显示工具类进行颜色渲染
        log_display_util.apply_colors_to_text_widget(self.plainTextEdit_log, content)
    
    def Apply_Colors_Simple(self, content):
        """简化的颜色渲染模式，用于大量日志 - 使用统一工具类"""
        # 使用统一的日志显示工具类的简化模式
        log_display_util._apply_colors_simple(self.plainTextEdit_log, content)

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
                self.calendarWidget.selectionChanged.connect(lambda:self.Get_Log_File_By_Date(self.calendarWidget.selectedDate().toString("yyyy-MM-dd")))
                
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
                                       (f'\n... 还有{len(file_list)-10}个文件' if len(file_list) > 10 else '') +
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


    # ============== 鼠标拖动勾选（批量模式）支持 ==============
    def _apply_drag_check_range(self, start_row: int, end_row: int):
        """将指定范围内的列表项设置为目标勾选状态
        
        在批量模式下，用户可以通过鼠标拖动来选择多个项目。此方法负责将指定行范围
        内的未处理条目设置为预设的目标勾选状态，避免重复处理已设置的条目。
        
        Args:
            start_row (int): 起始行号（包含）
            end_row (int): 结束行号（包含）
            
        Returns:
            None: 无返回值
            
        Note:
            - 方法会自动处理起始行号大于结束行号的情况
            - 只处理具有复选框功能的条目(Qt.ItemIsUserCheckable)
            - 已处理过的行号会被记录在self._drag_checked_indexes中避免重复处理
        """
        if start_row > end_row:
            start_row, end_row = end_row, start_row
        for row in range(start_row, end_row + 1):
            if row in self._drag_checked_indexes:
                continue
            item = self.listWidget_historyLogs.item(row)
            if not item:
                continue
            # 仅在复选框可用时生效
            if not (item.flags() & Qt.ItemIsUserCheckable):
                continue
            item.setCheckState(self._drag_check_target_state)
            self._drag_checked_indexes.add(row)

    def eventFilter(self, obj, event):
        """事件过滤器，用于在批量模式下支持通过鼠标拖动来批量勾选或取消勾选列表项。

        该方法拦截发送到 listWidget_historyLogs 视口的鼠标事件，并根据鼠标操作实现
        拖动选择功能。仅在 batch_mode 为 True 时启用此功能。

        Args:
            obj (QObject): 发送事件的对象，应为 listWidget_historyLogs 的视口。
            event (QEvent): 具体的事件对象，如 MouseButtonPress、MouseMove 等。

        Returns:
            bool: 如果事件被处理则返回 True，否则调用父类的事件过滤器并返回其结果。
        """
        if obj is self.listWidget_historyLogs.viewport():
            # 仅在批量模式下启用该功能
            if not getattr(self, 'batch_mode', False):
                return super().eventFilter(obj, event)

            et = event.type()
            # 左键按下：开始拖动勾选操作
            if et == QEvent.MouseButtonPress and event.button() == Qt.LeftButton:
                pos = event.pos()
                item = self.listWidget_historyLogs.itemAt(pos)
                if item and (item.flags() & Qt.ItemIsUserCheckable):
                    self._drag_check_active = True
                    self._drag_checked_indexes.clear()
                    self._drag_last_row = self.listWidget_historyLogs.row(item)
                    # 目标状态取决于按下时的当前状态（按下第一个条目时切换一次）
                    self._drag_check_target_state = Qt.Checked if item.checkState() != Qt.Checked else Qt.Unchecked
                    item.setCheckState(self._drag_check_target_state)
                    self._drag_checked_indexes.add(self._drag_last_row)
                    return True  # 吞掉事件，避免触发选择行为

            # 鼠标移动：在拖动中对经过的条目应用统一的勾选状态，并处理自动滚动
            if et == QEvent.MouseMove and getattr(self, '_drag_check_active', False):
                pos = event.pos()
                viewport = self.listWidget_historyLogs.viewport()
                h = viewport.height()
                y = pos.y()

                # 自动滚动：靠近顶部/底部时缓慢滚动
                vbar = self.listWidget_historyLogs.verticalScrollBar()
                step = max(1, vbar.singleStep())
                if y < self._drag_autoscroll_margin:
                    vbar.setValue(max(vbar.minimum(), vbar.value() - step))
                elif y > h - self._drag_autoscroll_margin:
                    vbar.setValue(min(vbar.maximum(), vbar.value() + step))

                # 应用行范围切换，避免快速移动遗漏中间项
                item = self.listWidget_historyLogs.itemAt(event.pos())
                if item:
                    cur_row = self.listWidget_historyLogs.row(item)
                    self._apply_drag_check_range(self._drag_last_row, cur_row)
                    self._drag_last_row = cur_row
                return True

            # 左键释放：结束拖动
            if et == QEvent.MouseButtonRelease and event.button() == Qt.LeftButton:
                if getattr(self, '_drag_check_active', False):
                    self._drag_check_active = False
                    self._drag_checked_indexes.clear()
                    return True

            # 鼠标离开视口：结束拖动状态
            if et == QEvent.Leave:
                if getattr(self, '_drag_check_active', False):
                    self._drag_check_active = False
                    self._drag_checked_indexes.clear()
                    return True

        return super().eventFilter(obj, event)

if __name__ == "__main__":
    app =QtWidgets.QApplication(sys.argv)
    Tool = LogCheckForm()
    Tool.show()
    sys.exit(app.exec())