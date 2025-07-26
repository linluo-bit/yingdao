#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自动化执行引擎
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Callable
from .context import ExecutionContext
from .instruction_base import InstructionExecutor, InstructionResult
from ..automation.web.instructions import (
    OpenWebPageInstruction,
    ClickElementInstruction,
    InputTextInstruction,
    ExtractTextInstruction,
    HoverElementInstruction,
    WaitInstruction
)

logger = logging.getLogger(__name__)


class AutomationEngine:
    """自动化执行引擎"""
    
    def __init__(self):
        self.context = ExecutionContext()
        self.instructions: Dict[str, InstructionExecutor] = {}
        self.current_workflow: List[Dict[str, Any]] = []
        self.is_running = False
        self.status_callback: Optional[Callable] = None
        self.log_callback: Optional[Callable] = None
        
        # 注册内置指令
        self._register_builtin_instructions()
    
    def _register_builtin_instructions(self):
        """注册内置指令"""
        instructions = [
            OpenWebPageInstruction(),
            ClickElementInstruction(),
            InputTextInstruction(),
            ExtractTextInstruction(),
            HoverElementInstruction(),
            WaitInstruction()
        ]
        
        for instruction in instructions:
            self.register_instruction(instruction)
        
        logger.info(f"注册了 {len(instructions)} 个内置指令")
    
    def register_instruction(self, instruction: InstructionExecutor):
        """注册指令"""
        self.instructions[instruction.instruction_type] = instruction
        logger.debug(f"注册指令: {instruction.instruction_type}")
    
    def set_status_callback(self, callback: Callable[[str], None]):
        """设置状态回调"""
        self.status_callback = callback
    
    def set_log_callback(self, callback: Callable[[str], None]):
        """设置日志回调"""
        self.log_callback = callback
    
    def _update_status(self, status: str):
        """更新状态"""
        if self.status_callback:
            self.status_callback(status)
    
    def _log_message(self, message: str):
        """记录日志"""
        logger.info(message)
        if self.log_callback:
            self.log_callback(message)
    
    async def execute_instruction(self, instruction_type: str, parameters: Dict[str, Any]) -> InstructionResult:
        """执行单个指令"""
        if instruction_type not in self.instructions:
            error_msg = f"未知的指令类型: {instruction_type}"
            logger.error(error_msg)
            return InstructionResult.error_result(error_msg)
        
        instruction = self.instructions[instruction_type]
        
        # 验证参数
        if not instruction.validate_parameters(parameters):
            error_msg = f"指令参数验证失败: {instruction_type}"
            logger.error(error_msg)
            return InstructionResult.error_result(error_msg)
        
        try:
            self.context.current_instruction = instruction_type
            self._log_message(f"执行指令: {instruction_type}")
            
            result = await instruction.execute(parameters, self.context)
            
            if result.success:
                self._log_message(result.message)
            else:
                self._log_message(f"指令执行失败: {result.message}")
            
            return result
            
        except Exception as e:
            error_msg = f"指令执行异常: {instruction_type}, 错误: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return InstructionResult.error_result(error_msg, e)
        finally:
            self.context.current_instruction = None
    
    async def execute_workflow(self, workflow: List[Dict[str, Any]]) -> bool:
        """执行工作流"""
        self.current_workflow = workflow
        self.is_running = True
        
        try:
            # 清理之前的WebDriver，确保每次执行都是全新环境
            if self.context.web_driver:
                try:
                    self.context.web_driver.quit()
                    logger.info("清理之前的WebDriver")
                except Exception as e:
                    logger.warning(f"清理WebDriver时出错: {e}")
                finally:
                    self.context.web_driver = None
            
            self.context.start_execution()
            self._update_status("正在执行流程...")
            self._log_message(f"开始执行工作流，共 {len(workflow)} 个步骤")
            
            success_count = 0
            
            for i, step in enumerate(workflow):
                if not self.is_running:
                    self._log_message("执行被用户中断")
                    break
                
                instruction_type = step.get("type")
                parameters = step.get("parameters", {})
                
                if not instruction_type:
                    self._log_message(f"步骤 {i+1}: 缺少指令类型")
                    continue
                
                self._log_message(f"步骤 {i+1}/{len(workflow)}: {instruction_type}")
                self._update_status(f"执行步骤 {i+1}/{len(workflow)}: {instruction_type}")
                
                result = await self.execute_instruction(instruction_type, parameters)
                
                if not result.success:
                    self._log_message(f"步骤 {i+1} 执行失败: {result.message}")
                    # 可以选择继续或停止执行
                    if step.get("stop_on_error", True):
                        self._log_message("因错误停止执行")
                        return False
                else:
                    success_count += 1
            
            execution_success = success_count == len(workflow)
            
            if execution_success:
                self._log_message(f"工作流执行完成，成功执行 {success_count} 个步骤")
                self._update_status("执行完成")
            else:
                self._log_message(f"工作流执行结束，成功执行 {success_count}/{len(workflow)} 个步骤")
                self._update_status("执行结束（部分失败）")
            
            return execution_success
            
        except Exception as e:
            error_msg = f"工作流执行异常: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self._log_message(error_msg)
            self._update_status("执行异常")
            return False
        finally:
            self.is_running = False
            self.context.stop_execution()
    
    def stop_execution(self):
        """停止执行"""
        self.is_running = False
        self.context.stop_execution()
        self._log_message("用户请求停止执行")
        self._update_status("已停止")
    
    def cleanup(self):
        """清理资源"""
        if self.context:
            self.context.cleanup()
        self._log_message("引擎资源已清理")
    
    def get_instruction_info(self, instruction_type: str) -> Optional[Dict[str, Any]]:
        """获取指令信息"""
        if instruction_type not in self.instructions:
            return None
        
        instruction = self.instructions[instruction_type]
        return {
            "type": instruction_type,
            "required_parameters": instruction.get_required_parameters(),
            "optional_parameters": instruction.get_optional_parameters()
        }
    
    def list_available_instructions(self) -> List[str]:
        """列出可用指令"""
        return list(self.instructions.keys())
    
    def create_sample_workflow(self) -> List[Dict[str, Any]]:
        """创建示例工作流"""
        return [
            {
                "type": "open_webpage",
                "parameters": {
                    "url": "https://www.baidu.com",
                    "browser": "chrome",
                    "headless": False
                }
            },
            {
                "type": "input_text",
                "parameters": {
                    "selector": "id:kw",
                    "text": "RPA自动化测试"
                }
            },
            {
                "type": "click_element",
                "parameters": {
                    "selector": "id:su"
                }
            },
            {
                "type": "wait",
                "parameters": {
                    "duration": 3
                }
            }
        ] 