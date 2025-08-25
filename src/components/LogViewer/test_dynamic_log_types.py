#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试动态日志类型功能
"""

import re

# 模拟日志内容
log_content = """
2025/04/03 10:00:00 - 自动测试 - INFO      - 系统启动成功
2025/04/03 10:01:00 - 自动测试 - WARNING   - 内存使用率较高，当前使用率85%
2025/04/03 10:02:00 - 自动测试 - ERROR     - 连接数据库失败
2025/04/03 10:03:00 - 自动测试 - DEBUG     - 调试信息：正在重试连接
2025/04/03 10:04:00 - 自动测试 - INFO      - 数据库连接恢复
2025/04/03 10:05:00 - 自动测试 - WARNING   - 磁盘空间不足，剩余空间10%
2025/04/03 10:06:00 - 自动测试 - CRITICAL  - 系统即将崩溃
2025/04/03 10:07:00 - 自动测试 - ERROR     - 系统异常退出
2025/04/03 10:08:00 - 自动测试 - INFO      - 系统重启完成
"""

def extract_log_types(content):
    """提取日志类型"""
    log_levels = set()
    pattern = r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2} - [^-]+ - ([A-Z]+)\s*- '
    matches = re.findall(pattern, content)
    
    for match in matches:
        log_levels.add(match.strip())
    
    return sorted(log_levels)

if __name__ == "__main__":
    print("测试动态日志类型提取功能:")
    log_types = extract_log_types(log_content)
    print(f"发现的日志类型: {log_types}")
    
    expected_types = ['CRITICAL', 'DEBUG', 'ERROR', 'INFO', 'WARNING']
    if log_types == expected_types:
        print("✅ 测试通过！动态日志类型提取功能正常")
    else:
        print(f"❌ 测试失败！期望: {expected_types}, 实际: {log_types}")