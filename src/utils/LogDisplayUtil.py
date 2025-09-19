# -*- coding: utf-8 -*-
"""
日志显示工具类

提供统一的日志显示样式和配色功能，从LogViewer中提取的通用方法
支持标准日志格式的颜色渲染和样式设置

Author: SanXiaoXing
Date: 2025
"""

import re
from PyQt5.QtWidgets import QPlainTextEdit, QApplication
from PyQt5.QtCore import Qt


class LogDisplayUtil:
    """日志显示工具类 - 提供统一的日志样式和配色"""
    
    # 日志级别颜色映射（与LogViewer保持一致）
    LOG_COLORS = {
        'ERROR': '#FF0000',      # 红色
        'CRITICAL': '#8B0000',   # 深红色
        'WARNING': '#FF8C00',    # 橙色
        'INFO': '#0000FF',       # 蓝色
        'DEBUG': '#808080',      # 灰色
    }
    
    # 时间戳配色
    TIME_COLOR = '#9b59b6'       # 日期部分使用紫色
    TIME_TIME_COLOR = '#808080'  # 时分秒(.毫秒)使用灰色
    
    def __init__(self):
        """初始化日志显示工具"""
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
    
    def apply_colors_to_text_widget(self, text_widget: QPlainTextEdit, content: str):
        """
        为QPlainTextEdit控件应用日志颜色样式
        
        Args:
            text_widget: QPlainTextEdit控件
            content: 要显示的日志内容
        """
        if not content.strip():
            text_widget.clear()
            return
            
        lines = content.split('\n')
        
        # 检查内容大小，如果过大则使用简化渲染
        if len(lines) > 5000:  # 超过5000行使用简化模式
            self._apply_colors_simple(text_widget, content)
            return
        
        # 清空文本框并设置HTML模式
        text_widget.clear()
        
        # 批量构建HTML内容，避免频繁的appendHtml调用
        batch_size = 500  # 每批处理500行
        
        for i in range(0, len(lines), batch_size):
            batch_lines = lines[i:i + batch_size]
            batch_html = []
            
            for line in batch_lines:
                if line.strip():  # 跳过空行
                    # 先进行HTML转义
                    escaped_line = self._html_escape(line)
                    
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
                    
                    # 处理日志格式: - LEVEL -
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
                text_widget.appendHtml(html_content)
                
            # 每批处理后刷新UI，保持响应性
            QApplication.processEvents()
    
    def _apply_colors_simple(self, text_widget: QPlainTextEdit, content: str):
        """简化的颜色渲染模式，用于大量日志"""
        # 对于大量日志，使用纯文本模式以提高性能
        text_widget.clear()
        text_widget.appendPlainText("日志内容过多，使用简化显示模式...\n\n")
        
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
            text_widget.appendPlainText('\n'.join(batch))
            QApplication.processEvents()
    
    def _html_escape(self, text: str) -> str:
        """HTML转义函数，保持原始空格和换行"""
        return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    
    def append_colored_log(self, text_widget: QPlainTextEdit, log_message: str):
        """
        向文本控件追加单条带颜色的日志消息
        
        Args:
            text_widget: QPlainTextEdit控件
            log_message: 单条日志消息
        """
        if not log_message.strip():
            return
        
        # HTML转义
        escaped_line = self._html_escape(log_message)
        
        # 日期与时间分别着色并斜体
        m_ts = self.re_timestamp_parts.search(log_message)
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
        
        # 处理日志级别颜色
        m = self.re_color_hyphen.search(log_message)  # 在原始行上匹配
        if m:
            lvl = m.group(2)
            color = self.LOG_COLORS.get(lvl)
            if color:
                pattern = re.compile(f'(-\\s+[^-]+\\s+-\\s+)({re.escape(lvl)})(\\s+-)')
                colored_line = pattern.sub(f'\\1<span style="color: {color}">\\2</span>\\3', colored_line)
        
        # 包装在保持空白和等宽字体的span中
        formatted_line = f'<span style="white-space: pre; font-family: Consolas, Monaco, monospace;">{colored_line}</span>'
        
        # 添加到文本框
        text_widget.appendHtml(formatted_line)
    
    def filter_logs_by_level(self, content: str, log_level: str) -> str:
        """
        根据日志级别过滤日志内容
        
        Args:
            content: 完整的日志内容
            log_level: 要过滤的日志级别，"全部"表示不过滤
            
        Returns:
            过滤后的日志内容
        """
        if not content or log_level == "全部":
            return content
            
        lines = content.split('\n')
        filtered_lines = []
        
        for line in lines:
            # 使用正则抽取本行日志级别，避免误匹配
            m = self.re_level_extract.search(line)
            if not m:
                continue
            level = m.group(1)
            if level == log_level:
                filtered_lines.append(line)
        
        return '\n'.join(filtered_lines)
    
    def get_log_levels_from_content(self, content: str) -> list:
        """
        从日志内容中提取所有日志级别
        
        Args:
            content: 日志内容
            
        Returns:
            日志级别列表（已排序）
        """
        if not content:
            return []
            
        log_levels = set()
        for m in self.re_level_extract.finditer(content):
            level = m.group(1)
            if level:
                log_levels.add(level.strip())
        
        return sorted(log_levels)


# 创建全局实例，方便其他模块使用
log_display_util = LogDisplayUtil()