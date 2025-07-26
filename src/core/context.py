#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
执行上下文管理
"""

from typing import Any, Dict, Optional
import asyncio
import logging

logger = logging.getLogger(__name__)


class ExecutionContext:
    """执行上下文"""
    
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.web_driver = None
        self.is_running = False
        self.current_instruction = None
        self._logger = logging.getLogger(__name__)
    
    def set_variable(self, name: str, value: Any):
        """设置变量"""
        self.variables[name] = value
        self._logger.debug(f"设置变量: {name} = {value}")
    
    def get_variable(self, name: str, default: Any = None) -> Any:
        """获取变量"""
        value = self.variables.get(name, default)
        self._logger.debug(f"获取变量: {name} = {value}")
        return value
    
    def has_variable(self, name: str) -> bool:
        """检查变量是否存在"""
        return name in self.variables
    
    def clear_variables(self):
        """清空所有变量"""
        self.variables.clear()
        self._logger.debug("清空所有变量")
    
    def set_web_driver(self, driver):
        """设置WebDriver"""
        self.web_driver = driver
        self._logger.debug("设置WebDriver")
    
    def get_web_driver(self):
        """获取WebDriver"""
        return self.web_driver
    
    def start_execution(self):
        """开始执行"""
        self.is_running = True
        self._logger.info("开始执行流程")
    
    def stop_execution(self):
        """停止执行"""
        self.is_running = False
        self._logger.info("停止执行流程")
    
    def is_execution_running(self) -> bool:
        """检查是否正在执行"""
        return self.is_running
    
    def cleanup(self):
        """清理资源"""
        if self.web_driver:
            try:
                self.web_driver.quit()
                self._logger.info("WebDriver已关闭")
            except Exception as e:
                self._logger.error(f"关闭WebDriver时出错: {e}")
            finally:
                self.web_driver = None
        
        self.is_running = False
        self._logger.info("执行上下文已清理") 