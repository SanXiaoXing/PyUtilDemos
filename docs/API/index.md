# API 文档总览

以下为各组件的 API 文档，已拆分为独立页面：

- [主程序 main](#主程序-main)
- 组件
  - [日志查看器 LogViewer](../API/log_viewer.md)
  - [校准工具 CalibTool](../API/calib_tool.md)
  - [实时数据绘图 RTDataPlot](../API/rt_data_plot.md)
  - [灯泡状态监控 BulbStateMonitor](../API/bulb_statemonitor.md)
  - [数据回放 DataReplay](../API/data_replay.md)
  - [资源索引查询 ResourceQuery](../API/resource_query.md)
  - [总线数据监控 BusDataMonitor](../API/bus_data_monitor.md)
  - [自定义控件集 CustomWidgets](../API/custom_widgets.md)
  - [网络设备管理 NetManager](../API/net_manager.md)
  - [Xml编辑器 XmlEditor](../API/xml_editor.md)



# API 文档使用说明

## 如何安装

1. 安装依赖库：`pip install mkdocs`
2. 启动文档服务：`mkdocs serve`

## 如何使用
1. 访问 http://localhost:8000/


提示：若某模块未显示详细成员，请补充源码中的 docstring 注释并刷新页面。