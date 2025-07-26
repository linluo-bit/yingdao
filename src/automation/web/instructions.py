#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
网页自动化指令实现
"""

import logging
import time
from typing import Dict, Any, Optional, List
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ...core.instruction_base import InstructionExecutor, InstructionResult
from .driver_manager import WebDriverManager
from .locators import ElementLocator

logger = logging.getLogger(__name__)


class OpenWebPageInstruction(InstructionExecutor):
    """打开网页指令"""
    
    def __init__(self):
        super().__init__("open_webpage")
    
    def get_instruction_name(self) -> str:
        return "open_webpage"
    
    def get_instruction_description(self) -> str:
        return "打开指定的网页"
    
    def get_required_parameters(self) -> List[str]:
        return ["url"]
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "browser": "chrome",
            "headless": False,
            "timeout": 30,
            "window_size": "1920,1080"
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        """验证参数"""
        if "url" not in parameters:
            return False
        
        url = parameters["url"]
        if not isinstance(url, str) or not url.strip():
            return False
        
        # 简单的URL格式验证
        if not (url.startswith("http://") or url.startswith("https://")):
            parameters["url"] = "https://" + url
        
        return True
    
    async def execute(self, parameters: Dict[str, Any], context) -> InstructionResult:
        """执行打开网页"""
        try:
            url = parameters["url"]
            browser = parameters.get("browser", "chrome")
            headless = parameters.get("headless", False)
            timeout = parameters.get("timeout", 30)
            window_size = parameters.get("window_size", "1920,1080")
            
            logger.info(f"打开网页: {url}")
            
            # 获取或创建WebDriver，并自动重启已关闭的driver
            driver = context.get_web_driver()
            if not driver:
                logger.info("创建新的WebDriver")
                driver_manager = WebDriverManager()
                driver = driver_manager.create_driver(
                    browser=browser,
                    headless=headless,
                    window_size=window_size
                )
                context.set_web_driver(driver)
            else:
                # 检查driver是否还活着
                logger.info("检查现有WebDriver连接状态")
                try:
                    # 尝试获取当前URL来检查连接
                    test_url = driver.current_url
                    logger.info(f"WebDriver连接正常，当前URL: {test_url}")
                except Exception as e:
                    logger.warning(f"WebDriver连接已断开: {e}")
                    logger.info("重新创建WebDriver")
                    # 创建新的WebDriverManager实例
                    driver_manager = WebDriverManager()
                    driver = driver_manager.create_driver(
                        browser=browser,
                        headless=headless,
                        window_size=window_size
                    )
                    context.set_web_driver(driver)
            
            # 设置页面加载超时
            driver.set_page_load_timeout(timeout)
            
            # 打开网页
            driver.get(url)
            
            # 等待页面加载完成
            WebDriverWait(driver, timeout).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            current_url = driver.current_url
            title = driver.title
            
            logger.info(f"成功打开网页: {title} ({current_url})")
            
            return InstructionResult(
                success=True,
                message=f"成功打开网页: {title}",
                data={
                    "url": current_url,
                    "title": title
                }
            )
            
        except TimeoutException:
            error_msg = f"打开网页超时: {url}"
            logger.error(error_msg)
            return InstructionResult(success=False, message=error_msg)
        
        except Exception as e:
            error_msg = f"打开网页失败: {e}"
            logger.error(error_msg)
            return InstructionResult(success=False, message=error_msg)


class ClickElementInstruction(InstructionExecutor):
    """点击元素指令"""
    
    def __init__(self):
        super().__init__("click_element")
    
    def get_instruction_name(self) -> str:
        return "click_element"
    
    def get_instruction_description(self) -> str:
        return "点击页面上的元素"
    
    def get_required_parameters(self) -> List[str]:
        return ["selector"]
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "timeout": 10,
            "wait_clickable": True,
            "scroll_to_element": True
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return "selector" in parameters and parameters["selector"]
    
    async def execute(self, parameters: Dict[str, Any], context) -> InstructionResult:
        """执行点击元素"""
        try:
            selector = parameters["selector"]
            timeout = parameters.get("timeout", 10)
            wait_clickable = parameters.get("wait_clickable", True)
            scroll_to_element = parameters.get("scroll_to_element", True)
            
            driver = context.get_web_driver()
            if not driver:
                return InstructionResult(success=False, message="WebDriver未初始化")
            
            locator = ElementLocator(driver, timeout)
            
            # 查找元素
            if wait_clickable:
                element = locator.wait_for_element_clickable(selector, timeout)
            else:
                element = locator.find_element(selector, timeout)
            
            if not element:
                return InstructionResult(success=False, message=f"未找到元素: {selector}")
            
            # 滚动到元素
            if scroll_to_element:
                driver.execute_script("arguments[0].scrollIntoView(true);", element)
                time.sleep(0.5)
            
            # 点击元素
            element.click()
            
            logger.info(f"成功点击元素: {selector}")
            
            return InstructionResult(
                success=True,
                message=f"成功点击元素: {selector}",
                data={"selector": selector}
            )
            
        except Exception as e:
            error_msg = f"点击元素失败: {e}"
            logger.error(error_msg)
            return InstructionResult(success=False, message=error_msg)


class InputTextInstruction(InstructionExecutor):
    """输入文本指令"""
    
    def __init__(self):
        super().__init__("input_text")
    
    def get_instruction_name(self) -> str:
        return "input_text"
    
    def get_instruction_description(self) -> str:
        return "在输入框中输入文本"
    
    def get_required_parameters(self) -> List[str]:
        return ["selector", "text"]
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "timeout": 10,
            "clear_first": True,
            "simulate_typing": False,
            "typing_delay": 0.1
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return "selector" in parameters and "text" in parameters
    
    async def execute(self, parameters: Dict[str, Any], context) -> InstructionResult:
        """执行输入文本"""
        try:
            selector = parameters["selector"]
            text = str(parameters["text"])
            timeout = parameters.get("timeout", 10)
            clear_first = parameters.get("clear_first", True)
            simulate_typing = parameters.get("simulate_typing", False)
            typing_delay = parameters.get("typing_delay", 0.1)
            
            driver = context.get_web_driver()
            if not driver:
                return InstructionResult(success=False, message="WebDriver未初始化")
            
            locator = ElementLocator(driver, timeout)
            element = locator.find_element(selector, timeout)
            
            if not element:
                return InstructionResult(success=False, message=f"未找到输入框: {selector}")
            
            # 滚动到元素
            driver.execute_script("arguments[0].scrollIntoView(true);", element)
            time.sleep(0.5)
            
            # 清空输入框
            if clear_first:
                element.clear()
            
            # 输入文本
            if simulate_typing:
                # 模拟逐字输入
                for char in text:
                    element.send_keys(char)
                    time.sleep(typing_delay)
            else:
                element.send_keys(text)
            
            logger.info(f"成功输入文本到 {selector}: {text}")
            
            return InstructionResult(
                success=True,
                message=f"成功输入文本: {text}",
                data={"selector": selector, "text": text}
            )
            
        except Exception as e:
            error_msg = f"输入文本失败: {e}"
            logger.error(error_msg)
            return InstructionResult(success=False, message=error_msg)


class ExtractTextInstruction(InstructionExecutor):
    """提取文本指令"""
    
    def __init__(self):
        super().__init__("extract_text")
    
    def get_instruction_name(self) -> str:
        return "extract_text"
    
    def get_instruction_description(self) -> str:
        return "从页面元素中提取文本"
    
    def get_required_parameters(self) -> List[str]:
        return ["selector"]
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "timeout": 10,
            "attribute": None,  # 如果指定，提取属性值而不是文本
            "variable_name": None  # 保存到变量
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return "selector" in parameters
    
    async def execute(self, parameters: Dict[str, Any], context) -> InstructionResult:
        """执行提取文本"""
        try:
            selector = parameters["selector"]
            timeout = parameters.get("timeout", 10)
            attribute = parameters.get("attribute")
            variable_name = parameters.get("variable_name")
            
            driver = context.get_web_driver()
            if not driver:
                return InstructionResult(success=False, message="WebDriver未初始化")
            
            locator = ElementLocator(driver, timeout)
            element = locator.find_element(selector, timeout)
            
            if not element:
                return InstructionResult(success=False, message=f"未找到元素: {selector}")
            
            # 提取文本或属性
            if attribute:
                extracted_value = element.get_attribute(attribute)
            else:
                extracted_value = element.text
            
            # 保存到变量
            if variable_name:
                context.set_variable(variable_name, extracted_value)
            
            logger.info(f"成功提取文本: {extracted_value}")
            
            return InstructionResult(
                success=True,
                message=f"成功提取文本: {extracted_value}",
                data={
                    "selector": selector,
                    "text": extracted_value,
                    "variable_name": variable_name
                }
            )
            
        except Exception as e:
            error_msg = f"提取文本失败: {e}"
            logger.error(error_msg)
            return InstructionResult(success=False, message=error_msg)


class HoverElementInstruction(InstructionExecutor):
    """鼠标悬停指令"""
    
    def __init__(self):
        super().__init__("hover_element")
    
    def get_instruction_name(self) -> str:
        return "hover_element"
    
    def get_instruction_description(self) -> str:
        return "鼠标悬停在元素上"
    
    def get_required_parameters(self) -> List[str]:
        return ["selector"]
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {
            "timeout": 10,
            "duration": 1.0  # 悬停持续时间
        }
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        return "selector" in parameters
    
    async def execute(self, parameters: Dict[str, Any], context) -> InstructionResult:
        """执行鼠标悬停"""
        try:
            selector = parameters["selector"]
            timeout = parameters.get("timeout", 10)
            duration = parameters.get("duration", 1.0)
            
            driver = context.get_web_driver()
            if not driver:
                return InstructionResult(success=False, message="WebDriver未初始化")
            
            locator = ElementLocator(driver, timeout)
            element = locator.find_element(selector, timeout)
            
            if not element:
                return InstructionResult(success=False, message=f"未找到元素: {selector}")
            
            # 执行悬停
            actions = ActionChains(driver)
            actions.move_to_element(element).perform()
            
            # 等待指定时间
            time.sleep(duration)
            
            logger.info(f"成功悬停在元素: {selector}")
            
            return InstructionResult(
                success=True,
                message=f"成功悬停在元素: {selector}",
                data={"selector": selector}
            )
            
        except Exception as e:
            error_msg = f"鼠标悬停失败: {e}"
            logger.error(error_msg)
            return InstructionResult(success=False, message=error_msg)


class WaitInstruction(InstructionExecutor):
    """等待指令"""
    
    def __init__(self):
        super().__init__("wait")
    
    def get_instruction_name(self) -> str:
        return "wait"
    
    def get_instruction_description(self) -> str:
        return "等待指定时间"
    
    def get_required_parameters(self) -> List[str]:
        return ["duration"]
    
    def get_optional_parameters(self) -> Dict[str, Any]:
        return {}
    
    def validate_parameters(self, parameters: Dict[str, Any]) -> bool:
        if "duration" not in parameters:
            return False
        
        try:
            float(parameters["duration"])
            return True
        except (ValueError, TypeError):
            return False
    
    async def execute(self, parameters: Dict[str, Any], context) -> InstructionResult:
        """执行等待"""
        try:
            duration = float(parameters["duration"])
            
            logger.info(f"等待 {duration} 秒")
            time.sleep(duration)
            
            return InstructionResult(
                success=True,
                message=f"等待完成: {duration} 秒",
                data={"duration": duration}
            )
            
        except Exception as e:
            error_msg = f"等待执行失败: {e}"
            logger.error(error_msg)
            return InstructionResult(success=False, message=error_msg)