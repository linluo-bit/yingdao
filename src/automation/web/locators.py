#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元素定位器
"""

import logging
from typing import Optional, List, Union, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.remote.webelement import WebElement
from selenium.common.exceptions import TimeoutException, NoSuchElementException

logger = logging.getLogger(__name__)


class ElementLocator:
    """元素定位器"""

    # 定位策略映射
    LOCATOR_MAP = {
        "id": By.ID,
        "name": By.NAME,
        "class": By.CLASS_NAME,
        "tag": By.TAG_NAME,
        "xpath": By.XPATH,
        "css": By.CSS_SELECTOR,
        "link_text": By.LINK_TEXT,
        "partial_link_text": By.PARTIAL_LINK_TEXT,
    }

    def __init__(self, driver, wait_timeout: int = 10):
        self.driver = driver
        self.wait_timeout = wait_timeout
        self.wait = WebDriverWait(driver, wait_timeout)

    def parse_selector(self, selector: str) -> Tuple[By, str]:
        """
        解析选择器字符串

        支持的格式:
        - id:element_id
        - name:element_name
        - class:class_name
        - tag:tag_name
        - xpath://div[@id='test']
        - css:.class-name
        - link_text:链接文字
        - partial_link_text:部分链接文字
        - 纯字符串（自动判断）
        """
        if not selector:
            raise ValueError("选择器不能为空")

        selector = selector.strip()

        # 如果包含冒号，按格式解析
        if ":" in selector and not selector.startswith("//"):
            parts = selector.split(":", 1)
            if len(parts) == 2:
                strategy, value = parts[0].strip().lower(), parts[1].strip()
                if strategy in self.LOCATOR_MAP:
                    return self.LOCATOR_MAP[strategy], value

        # 自动判断选择器类型
        if selector.startswith("//"):
            return By.XPATH, selector
        elif selector.startswith("#"):
            return By.CSS_SELECTOR, selector
        elif selector.startswith("."):
            return By.CSS_SELECTOR, selector
        elif selector.startswith("["):
            return By.CSS_SELECTOR, selector
        else:
            # 默认尝试ID，然后Name，最后CSS
            try:
                self.driver.find_element(By.ID, selector)
                return By.ID, selector
            except NoSuchElementException:
                try:
                    self.driver.find_element(By.NAME, selector)
                    return By.NAME, selector
                except NoSuchElementException:
                    return By.CSS_SELECTOR, selector

    def find_element(
        self, selector: str, timeout: Optional[int] = None
    ) -> Optional[WebElement]:
        """
        查找单个元素

        Args:
            selector: 元素选择器
            timeout: 等待超时时间

        Returns:
            WebElement: 找到的元素，未找到返回None
        """
        try:
            by, value = self.parse_selector(selector)
            wait_time = timeout if timeout is not None else self.wait_timeout

            element = WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )

            logger.debug(f"找到元素: {selector}")
            return element

        except TimeoutException:
            logger.warning(f"元素查找超时: {selector}")
            return None
        except Exception as e:
            logger.error(f"查找元素时出错: {selector}, 错误: {e}")
            return None

    def find_elements(
        self, selector: str, timeout: Optional[int] = None
    ) -> List[WebElement]:
        """
        查找多个元素

        Args:
            selector: 元素选择器
            timeout: 等待超时时间

        Returns:
            List[WebElement]: 找到的元素列表
        """
        try:
            by, value = self.parse_selector(selector)
            wait_time = timeout if timeout is not None else self.wait_timeout

            # 等待至少一个元素出现
            WebDriverWait(self.driver, wait_time).until(
                EC.presence_of_element_located((by, value))
            )

            elements = self.driver.find_elements(by, value)
            logger.debug(f"找到 {len(elements)} 个元素: {selector}")
            return elements

        except TimeoutException:
            logger.warning(f"元素查找超时: {selector}")
            return []
        except Exception as e:
            logger.error(f"查找元素时出错: {selector}, 错误: {e}")
            return []

    def wait_for_element_clickable(
        self, selector: str, timeout: Optional[int] = None
    ) -> Optional[WebElement]:
        """等待元素可点击"""
        try:
            by, value = self.parse_selector(selector)
            wait_time = timeout if timeout is not None else self.wait_timeout

            element = WebDriverWait(self.driver, wait_time).until(
                EC.element_to_be_clickable((by, value))
            )

            logger.debug(f"元素可点击: {selector}")
            return element

        except TimeoutException:
            logger.warning(f"等待元素可点击超时: {selector}")
            return None
        except Exception as e:
            logger.error(f"等待元素可点击时出错: {selector}, 错误: {e}")
            return None

    def wait_for_element_visible(
        self, selector: str, timeout: Optional[int] = None
    ) -> Optional[WebElement]:
        """等待元素可见"""
        try:
            by, value = self.parse_selector(selector)
            wait_time = timeout if timeout is not None else self.wait_timeout

            element = WebDriverWait(self.driver, wait_time).until(
                EC.visibility_of_element_located((by, value))
            )

            logger.debug(f"元素可见: {selector}")
            return element

        except TimeoutException:
            logger.warning(f"等待元素可见超时: {selector}")
            return None
        except Exception as e:
            logger.error(f"等待元素可见时出错: {selector}, 错误: {e}")
            return None

    def wait_for_text_present(
        self, selector: str, text: str, timeout: Optional[int] = None
    ) -> bool:
        """等待元素包含指定文本"""
        try:
            by, value = self.parse_selector(selector)
            wait_time = timeout if timeout is not None else self.wait_timeout

            result = WebDriverWait(self.driver, wait_time).until(
                EC.text_to_be_present_in_element((by, value), text)
            )

            logger.debug(f"元素包含文本 '{text}': {selector}")
            return result

        except TimeoutException:
            logger.warning(f"等待文本出现超时: {selector}, 文本: {text}")
            return False
        except Exception as e:
            logger.error(f"等待文本出现时出错: {selector}, 文本: {text}, 错误: {e}")
            return False

    def is_element_present(self, selector: str) -> bool:
        """检查元素是否存在"""
        try:
            by, value = self.parse_selector(selector)
            self.driver.find_element(by, value)
            return True
        except NoSuchElementException:
            return False
        except Exception as e:
            logger.error(f"检查元素存在时出错: {selector}, 错误: {e}")
            return False
