#!/usr/bin/env python3
# -*- coding: UTF-8 -*-
"""
@Project ：py-util-demos 
@File    ：LoggerUtil.py
@Author  ：SanXiaoXing
@Date    ：2025/9/17
@Description: 标准日志工具类
    格式: 2023-09-17 14:30:25.123 [INFO] [MainThread] [UserService] - 用户ID:10086登录成功，IP:192.168.1.100
"""
import os
import sys
import logging
import threading
from datetime import datetime, timedelta
from pathlib import Path

# 日志根目录
LOG_ROOT = Path(__file__).resolve().parent.parent / 'logs'
if not LOG_ROOT.exists():
    LOG_ROOT.mkdir(parents=True, exist_ok=True)


class LoggerUtil:
    """
    标准日志工具类，提供统一的日志记录接口
    """

    # 日志级别映射
    LEVELS = {
        'debug': logging.DEBUG,
        'info': logging.INFO,
        'warning': logging.WARNING,
        'error': logging.ERROR,
        'critical': logging.CRITICAL
    }

    @staticmethod
    def get_logger(name, log_to_file=True, log_to_console=True, log_level='debug'):
        """
        获取指定名称的日志记录器

        Args:
            name: 日志记录器名称，通常是模块或服务名
            log_to_file: 是否记录到文件
            log_to_console: 是否输出到控制台
            log_level: 日志级别，可选值：debug, info, warning, error, critical

        Returns:
            logger: 日志记录器实例
        """
        # 创建日志记录器
        logger = logging.getLogger(name)

        # 如果已经有处理器，说明已经初始化过，直接返回
        if logger.handlers:
            return logger

        # 设置日志级别
        level = LoggerUtil.LEVELS.get(log_level.lower(), logging.INFO)
        logger.setLevel(level)

        # 创建格式化器，使用log_config.py的样式并添加毫秒
        formatter = logging.Formatter(
            fmt="%(asctime)s.%(msecs)03d - %(name)s - %(levelname)-9s - %(message)s",
            datefmt="%Y/%m/%d %H:%M:%S"
        )

        # 添加控制台处理器
        if log_to_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            logger.addHandler(console_handler)

        # 添加文件处理器
        if log_to_file:
            # 按日期生成日志文件名
            log_filename = f"log_{datetime.now().strftime('%Y-%m-%d')}.log"
            log_filepath = LOG_ROOT / log_filename

            # 创建文件处理器
            file_handler = logging.FileHandler(
                filename=str(log_filepath),
                mode='a',
                encoding='utf-8'
            )
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)

        return logger

    @staticmethod
    def clean_old_logs(days_to_keep=90):
        """
        清理指定天数前的日志文件

        Args:
            days_to_keep: 保留的天数，默认90天，如果为None或负数则不清理日志
        """
        # 如果days_to_keep为None或负数，则不清理日志
        if days_to_keep is None or days_to_keep < 0:
            logging.info("日志清理已跳过：设置为无期限保留")
            return

        try:
            now = datetime.now()
            cutoff = now - timedelta(days=days_to_keep)

            # 获取错误日志记录器
            error_logger = LoggerUtil.get_logger("LogCleaner")

            for filename in os.listdir(LOG_ROOT):
                # 仅处理符合命名格式的日志文件
                if filename.startswith("log_") and filename.endswith(".log"):
                    try:
                        # 从文件名中提取日期
                        date_str = filename[4:-4]  # 去掉"log_"和".log"
                        file_date = datetime.strptime(date_str, "%Y-%m-%d")

                        # 比较日期并删除过期文件
                        if file_date < cutoff:
                            filepath = os.path.join(LOG_ROOT, filename)
                            os.remove(filepath)
                            error_logger.info(f"已删除过期日志文件: {filename}")
                    except ValueError:
                        # 如果文件名格式不正确，跳过该文件
                        continue
                    except Exception as e:
                        error_logger.error(f"删除日志文件失败: {filename}, 错误: {str(e)}")
        except Exception as e:
            # 使用系统日志记录器记录清理过程中的错误
            logging.error(f"清理日志时发生错误: {str(e)}")


# 使用示例
if __name__ == "__main__":
    # 获取日志记录器
    logger = LoggerUtil.get_logger("测试服务")

    # 记录不同级别的日志
    logger.debug("这是一条调试信息")
    logger.info(f"用户ID:10086登录成功，IP:192.168.1.100")
    logger.warning("这是一条警告信息")
    logger.error("这是一条错误信息")
    logger.critical("这是一条严重错误信息")

    # 清理过期日志
    LoggerUtil.clean_old_logs(None)