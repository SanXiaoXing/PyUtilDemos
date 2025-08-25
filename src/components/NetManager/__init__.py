#!/usr/bin/env python
# -*- coding: UTF-8 -*-
"""
@Project ：631_ZHCLTest
@File    ：__init__.py
@Author  ：SanXiaoXing
@Date    ：2025/8/16
@Description: NetManager 网络设备管理组件;提供网络设备的扫描、管理、增删改查等功能
"""

# 导入核心类
from .NetManager import NetManager, AddDeviceDialog, ScanWorker
from Ui_NetManager import Ui_NetManager

# 公开接口
__all__ = [
    'NetManager',           # 主要的网络设备管理器类
    'AddDeviceDialog',      # 添加设备对话框
    'ScanWorker',          # 网络扫描工作线程
    'Ui_NetManager',       # UI界面类
]

# 版本信息
__version__ = '1.0.0'
__author__ = 'SanXiaoXing'
__copyright__ = 'Copyright 2025 SanXiaoXing'

# 模块级别的文档字符串
"""
NetManager 组件使用说明:

1. 基本使用:
    from component.NetManager import NetManager
    
    # 创建网络设备管理器
    manager = NetManager()
    manager.show()

2. 自定义配置文件路径:
    manager = NetManager(json_path="/path/to/custom/NetDevice.json")

3. 主要功能:
    - 自动扫描网络设备状态
    - 添加、编辑、删除网络设备
    - 设备状态筛选和搜索
    - 实时显示设备在线/离线状态
    - 支持右键菜单操作

4. 配置文件格式 (NetDevice.json):
    {
        "192.168.1.1": "路由器",
        "192.168.1.100": "服务器",
        "192.168.1.200": "工作站"
    }
"""