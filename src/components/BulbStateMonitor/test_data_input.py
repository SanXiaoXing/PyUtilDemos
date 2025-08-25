#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
@Project ：py-util-demos
@File    ：test_data_input.py
@Author  ：SanXiaoXing
@Date    ：2025/7/12
@Description: 灯泡状态监控工具 - 数据输入测试脚本

本脚本演示如何通过编程接口向监控工具发送数据
"""

import sys
import os
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import QTimer

# 添加当前目录到路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from bulb_statemonitor_demo import BulbStateMonitor

def test_data_input():
    """测试数据输入功能"""
    app = QApplication(sys.argv)
    
    # 创建监控实例
    monitor = BulbStateMonitor()
    monitor.show()
    
    # 创建定时器，模拟数据输入
    timer = QTimer()
    
    test_data = [
        "ff00",  # 第一个字节0xFF，第二个字节0x00
        "00ff",  # 第一个字节0x00，第二个字节0xFF
        "ffff",  # 两个字节都是0xFF
        "0000",  # 两个字节都是0x00
        "aa55",  # 第一个字节0xAA，第二个字节0x55
    ]
    
    current_index = 0
    
    def send_next_data():
        nonlocal current_index
        if current_index < len(test_data):
            data = test_data[current_index]
            print(f"\n=== 发送测试数据 {current_index + 1}: {data} ===")
            success = monitor.send_data_packet(data)
            if success:
                print(f"数据 {data} 发送成功")
            else:
                print(f"数据 {data} 发送失败")
            current_index += 1
        else:
            print("\n=== 所有测试数据发送完成 ===")
            timer.stop()
    
    # 每3秒发送一次数据
    timer.timeout.connect(send_next_data)
    timer.start(3000)
    
    print("灯泡状态监控工具已启动")
    print("将每3秒自动发送一次测试数据")
    print("您也可以在界面的输入框中手动输入数据进行测试")
    print("\n支持的数据格式示例:")
    print("- ffff (两个字节，都是0xFF)")
    print("- ff00 (第一个字节0xFF，第二个字节0x00)")
    print("- aa55 (第一个字节0xAA，第二个字节0x55)")
    
    sys.exit(app.exec_())

if __name__ == "__main__":
    test_data_input()