# py-util-demos

基于 Python 与 PyQt5 的实用工具集合，包含多个功能模块，如日志查看器、数据监控、校准工具等。

- 代码仓库: https://github.com/SanXiaoXing/PyUtilDemos
- 运行主界面: `python main.py`

文档结构：
- 首页（当前页面）
- API 文档（自动从源码生成）

# 如需本地预览文档

## 如何安装
### 1.安装 Zensical

> 基础依赖库[documentation](https://zensical.org/docs/authoring/content-tabs/)

=== "uv"

    ``` uv
    uv add --dev zensical
    ```

=== "pip"

    ``` pip
    pip install zensical
    ```

### 2.安装 Mkdocstrings

> Python 代码的自动文档生成[Mkdocstrings](https://zensical.org/docs/authoring/content-tabs/)

=== "uv"

    ``` uv
    uv add mkdocstrings-python
    ```

=== "pip"

    ``` pip
    pip install mkdocstrings-python
    ```

## 如何使用
1.启动文档服务`zensical serve`

2.访问 http://localhost:8000/ 查看文档