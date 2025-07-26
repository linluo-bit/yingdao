#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
指令执行器基类
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class InstructionResult:
    """指令执行结果"""

    success: bool
    message: str
    data: Any = None
    error: Optional[Exception] = None

    @classmethod
    def success_result(cls, message: str, data: Any = None):
        """创建成功结果"""
        return cls(success=True, message=message, data=data)

    @classmethod
    def error_result(cls, message: str, error: Optional[Exception] = None):
        """创建错误结果"""
        return cls(success=False, message=message, error=error)


class InstructionExecutor(ABC):
    """指令执行器基类"""

    def __init__(self, instruction_type: str):
        self.instruction_type = instruction_type
        self.logger = logging.getLogger(f"{__name__}.{instruction_type}")

    @abstractmethod
    async def execute(
        self, parameters: Dict[str, Any], context: "ExecutionContext"
    ) -> InstructionResult:
        """
        执行指令

        Args:
            parameters: 指令参数
            context: 执行上下文

        Returns:
            InstructionResult: 执行结果
        """
        pass

    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """
        验证参数

        Args:
            parameters: 指令参数

        Returns:
            bool: 参数是否有效
        """
        return True

    def get_required_parameters(self) -> list:
        """获取必需参数列表"""
        return []

    def get_optional_parameters(self) -> Dict[str, Any]:
        """获取可选参数及其默认值"""
        return {}
