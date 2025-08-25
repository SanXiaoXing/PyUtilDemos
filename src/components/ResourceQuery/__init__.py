"""
功能描述：多维度测试资源索引查询

该模块提供测试资源查询功能，包括：
- 多维度查询：按类型、名称、规格等多个维度筛选资源
- 查询结果展示：在表格中显示查询结果
- 数据过滤：实时过滤和搜索功能
"""

from src.components.ResourceQuery.ResourceQueryTool import ResourceQueryTool

__all__ = [
    'ResourceQueryTool'
]

__version__ = '1.0.0'
__author__ = 'SanXiaoXing'
__copyright__ = 'Copyright 2025 SanXiaoXing'