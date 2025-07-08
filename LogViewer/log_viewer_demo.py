import os 
import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from pathlib import Path
from PyQt5.QtWidgets import *
from PyQt5.QtGui import *
from PyQt5.QtCore import *
import glob
from datetime import datetime
import re

from Ui_log_viewer import *


LOG_FILES=str( Path(__file__).parent / 'logs')  # 插值表配置文件路径
print(LOG_FILES)

class LogCheckForm(QWidget,Ui_log_viewer):
    def __init__(self):
        super(LogCheckForm,self).__init__()
        self.setupUi(self)
        self.InitUI()



    def InitUI(self):
        self.setWindowTitle('历史日志')
        strdate=datetime.now().strftime('%Y-%m-%d')
        self.current_log_content = ""  # 存储当前完整日志内容
        self.batch_mode = False  # 批量删除模式标志
        
        # 设置列表控件支持多选
        self.listWidget_historyLogs.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # 设置右键菜单
        self.listWidget_historyLogs.setContextMenuPolicy(Qt.CustomContextMenu)
        self.listWidget_historyLogs.customContextMenuRequested.connect(self.Show_Context_Menu)
        
        self.Get_Log_File_By_Date(strdate)
        self.Set_Log_Date()
        self.calendarWidget.selectionChanged.connect(lambda:self.Get_Log_File_By_Date(self.calendarWidget.selectedDate().toString("yyyy-MM-dd")))
        self.comboBox_logType.currentTextChanged.connect(self.Filter_Log_By_Type)
        self.listWidget_historyLogs.itemClicked.connect(self.On_History_Log_Clicked)
        
        # 连接按钮事件
        self.pushButton_batchMode.clicked.connect(self.Enter_Batch_Mode)
        self.pushButton_deleteSelected.clicked.connect(self.Delete_Selected_Logs)
        self.pushButton_cancelBatch.clicked.connect(self.Exit_Batch_Mode)
        
        self.Load_History_Log_List()



    def Set_Log_Date(self):
        log_files=glob.glob(os.path.join(LOG_FILES,"*.log"))
        for logfile in log_files: 
            date = os.path.basename(logfile)
            date = date.split('_')[1].split('.')[0]
            date = datetime.strptime(date, '%Y-%m-%d').date()
            format = QTextCharFormat()
            format.setBackground(QColor(180,238,180))
            self.calendarWidget.setDateTextFormat(date, format)
            
        

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
            # 使用正则表达式提取所有日志级别
            # 日志格式: YYYY/MM/DD HH:MM:SS - 模块名 - 日志级别 - 消息
            log_levels = set()
            pattern = r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} - [^-]+ - ([A-Z]+)\s*- '
            matches = re.findall(pattern, self.current_log_content)
            
            for match in matches:
                log_levels.add(match.strip())
            
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
        
        # 定义日志级别对应的颜色
        log_colors = {
            'ERROR': '#FF0000',      # 红色
            'CRITICAL': '#8B0000',   # 深红色
            'WARNING': '#FF8C00',    # 橙色
            'INFO': '#0000FF',       # 蓝色
            'DEBUG': '#808080',      # 灰色
        }
        
        if log_type == "全部":
            # 显示所有日志并应用颜色
            self.Apply_Colors_To_All_Logs()
        else:
            # 按类型过滤日志并应用颜色
            lines = self.current_log_content.split('\n')
            filtered_lines = []
            
            for line in lines:
                if log_type in line:
                    filtered_lines.append(line)
            
            filtered_content = '\n'.join(filtered_lines)
            self.Apply_Colors_To_Content(filtered_content)
    
    def Apply_Colors_To_All_Logs(self):
        """为所有日志应用颜色"""
        self.Apply_Colors_To_Content(self.current_log_content)
    
    def Apply_Colors_To_Content(self, content):
        """为指定内容应用颜色 - 优化版本"""
        # 定义日志级别对应的颜色
        log_colors = {
            'ERROR': '#FF0000',      # 红色
            'CRITICAL': '#8B0000',   # 深红色
            'WARNING': '#FF8C00',    # 橙色
            'INFO': '#0000FF',       # 蓝色
            'DEBUG': '#808080',      # 灰色
        }
        
        lines = content.split('\n')
        
        # 检查内容大小，如果过大则使用简化渲染
        if len(lines) > 5000:  # 超过5000行使用简化模式
            self.Apply_Colors_Simple(content, log_colors)
            return
        
        # 批量构建HTML内容，避免频繁的appendHtml调用
        html_content = []
        batch_size = 500  # 每批处理500行
        
        for i in range(0, len(lines), batch_size):
            batch_lines = lines[i:i + batch_size]
            batch_html = []
            
            for line in batch_lines:
                if line.strip():  # 跳过空行
                    # 检测日志级别并只对级别关键词应用颜色
                    colored_line = line
                    for level, color in log_colors.items():
                        if f' - {level}' in line:
                            # 只对日志级别关键词应用颜色，其他部分保持默认颜色
                            colored_line = line.replace(
                                f' - {level}', 
                                f' - <span style="color: {color}">{level}</span>'
                            )
                            break
                    
                    # HTML转义特殊字符（除了我们添加的span标签）
                    if '<span style=' not in colored_line:
                        colored_line = colored_line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                    
                    batch_html.append(colored_line)
            
            # 批量添加到文本框
            if batch_html:
                self.plainTextEdit_log.appendHtml('<br>'.join(batch_html) + '<br>')
                
            # 每批处理后刷新UI，保持响应性
            QtWidgets.QApplication.processEvents()
    
    def Apply_Colors_Simple(self, content, log_colors):
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
    
    def Delete_Single_Log(self, item):
        """删除单个日志文件"""
        try:
            logfile = item.data(Qt.UserRole + 1)
            date = item.data(Qt.UserRole)
            
            # 确认删除
            reply = QMessageBox.question(self, '确认删除', 
                                       f'确定要删除日志文件 "{date}" 吗？\n此操作不可撤销！',
                                       QMessageBox.Yes | QMessageBox.No,
                                       QMessageBox.No)
            
            if reply == QMessageBox.Yes:
                # 删除文件
                if os.path.exists(logfile):
                    os.remove(logfile)
                    
                    # 从列表中移除
                    row = self.listWidget_historyLogs.row(item)
                    self.listWidget_historyLogs.takeItem(row)
                    
                    # 清空当前显示的日志内容（如果删除的是当前显示的文件）
                    current_date = self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
                    if date == current_date:
                        self.current_log_content = ""
                        self.plainTextEdit_log.clear()
                        self.Update_Log_Types()
                    
                    # 更新日历显示
                    self.Set_Log_Date()
                    
                    QMessageBox.information(self, '删除成功', f'日志文件 "{date}" 已删除')
                else:
                    QMessageBox.warning(self, '删除失败', f'文件不存在: {logfile}')
                    
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
                deleted_count = 0
                failed_files = []
                current_date = self.calendarWidget.selectedDate().toString("yyyy-MM-dd")
                need_clear_display = False
                
                for item in selected_items:
                    try:
                        logfile = item.data(Qt.UserRole + 1)
                        date = item.data(Qt.UserRole)
                        
                        if os.path.exists(logfile):
                            os.remove(logfile)
                            deleted_count += 1
                            
                            # 检查是否需要清空当前显示
                            if date == current_date:
                                need_clear_display = True
                        else:
                            failed_files.append(f'{date} (文件不存在)')
                            
                    except Exception as e:
                        failed_files.append(f'{item.data(Qt.UserRole)} (删除失败: {str(e)})')
                
                # 重新加载列表
                self.Load_History_Log_List()
                
                # 清空当前显示（如果需要）
                if need_clear_display:
                    self.current_log_content = ""
                    self.plainTextEdit_log.clear()
                    self.Update_Log_Types()
                
                # 更新日历显示
                self.Set_Log_Date()
                
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


if __name__ == "__main__":
    app =QtWidgets.QApplication(sys.argv)
    Tool = LogCheckForm()
    Tool.show()
    sys.exit(app.exec())