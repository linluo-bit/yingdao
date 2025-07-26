#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WebDriver管理器
"""

import logging
import os
from typing import Optional, Dict, Any
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.firefox.options import Options as FirefoxOptions
from selenium.webdriver.edge.options import Options as EdgeOptions
import undetected_chromedriver as uc
from pathlib import Path

logger = logging.getLogger(__name__)


class WebDriverManager:
    """
    WebDriver管理器
    负责创建、配置和管理浏览器驱动实例
    """

    def __init__(self):
        self.driver: Optional[webdriver.Remote] = None
        self.browser_type: str = "chrome"
        self.headless: bool = False
        self.user_data_dir: Optional[str] = None

    def create_driver(
        self,
        browser: str = "chrome",
        headless: bool = False,
        user_data_dir: Optional[str] = None,
        **kwargs,
    ) -> webdriver.Remote:
        """
        创建WebDriver实例

        Args:
            browser: 浏览器类型 (chrome, firefox, edge)
            headless: 是否无头模式
            user_data_dir: 用户数据目录
            **kwargs: 其他配置参数

        Returns:
            WebDriver实例
        """
        self.browser_type = browser.lower()
        self.headless = headless
        self.user_data_dir = user_data_dir

        try:
            if self.browser_type == "chrome":
                self.driver = self._create_chrome_driver(**kwargs)
            elif self.browser_type == "firefox":
                self.driver = self._create_firefox_driver(**kwargs)
            elif self.browser_type == "edge":
                self.driver = self._create_edge_driver(**kwargs)
            else:
                raise ValueError(f"不支持的浏览器类型: {browser}")

            logger.info(f"成功创建 {browser} WebDriver")
            return self.driver

        except Exception as e:
            logger.error(f"创建WebDriver失败: {e}")
            raise

    def _create_chrome_driver(self, **kwargs) -> webdriver.Chrome:
        """创建Chrome WebDriver"""
        options = ChromeOptions()

        # 基础配置
        if self.headless:
            options.add_argument("--headless")

        # 用户数据目录
        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # 反检测配置
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_argument("--disable-extensions")
        # options.add_argument("--disable-plugins")  # 注释掉，可能影响某些网页功能
        # options.add_argument("--disable-images")   # 注释掉，图片可能是必需的
        # options.add_argument("--disable-javascript")  # 注释掉，JavaScript是必需的
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 添加更稳定的配置
        options.add_argument("--disable-web-security")
        options.add_argument("--allow-running-insecure-content")
        options.add_argument("--disable-features=VizDisplayCompositor")

        # 窗口大小
        window_size = kwargs.get("window_size", "1920,1080")
        options.add_argument(f"--window-size={window_size}")

        # 指定Chrome浏览器的可执行文件路径
        import os

        # 用户提供的Chrome路径
        custom_chrome_path = r"D:\Chrome\App\chrome.exe"

        # 常见的Chrome安装路径
        chrome_paths = [
            custom_chrome_path,  # 优先使用用户提供的路径
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            r"C:\Users\{}\AppData\Local\Google\Chrome\Application\chrome.exe".format(
                os.getenv("USERNAME", "Default")
            ),
        ]

        chrome_binary = None
        for path in chrome_paths:
            if os.path.exists(path):
                chrome_binary = path
                logger.info(f"找到Chrome浏览器: {chrome_binary}")
                break

        if chrome_binary:
            options.binary_location = chrome_binary
        else:
            logger.error("未找到Chrome浏览器，请检查安装路径")
            raise Exception("Chrome浏览器未找到")

        # 指定ChromeDriver路径
        project_root = Path(__file__).parent.parent.parent.parent
        chromedriver_path = project_root / "chromedriver.exe"

        try:
            if chromedriver_path.exists():
                logger.info(f"使用本地ChromeDriver: {chromedriver_path}")
                service = ChromeService(executable_path=str(chromedriver_path))
                driver = webdriver.Chrome(service=service, options=options)
            else:
                logger.warning(
                    f"未找到本地ChromeDriver: {chromedriver_path}，尝试使用系统PATH"
                )
                driver = webdriver.Chrome(options=options)

            # 执行反检测脚本
            driver.execute_script(
                "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
            )

            return driver

        except Exception as e:
            logger.error(f"创建Chrome驱动失败: {e}")
            raise

    def _create_firefox_driver(self, **kwargs) -> webdriver.Firefox:
        """创建Firefox WebDriver"""
        options = FirefoxOptions()

        if self.headless:
            options.add_argument("--headless")

        # 用户配置目录
        if self.user_data_dir:
            profile = webdriver.FirefoxProfile(self.user_data_dir)
            options.profile = profile

        return webdriver.Firefox(options=options)

    def _create_edge_driver(self, **kwargs) -> webdriver.Edge:
        """创建Edge WebDriver"""
        options = EdgeOptions()

        if self.headless:
            options.add_argument("--headless")

        if self.user_data_dir:
            options.add_argument(f"--user-data-dir={self.user_data_dir}")

        # 基础配置
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        return webdriver.Edge(options=options)

    def get_driver(self) -> Optional[webdriver.Remote]:
        """获取当前WebDriver实例"""
        return self.driver

    def quit_driver(self):
        """关闭WebDriver"""
        if self.driver:
            try:
                self.driver.quit()
                logger.info("WebDriver已关闭")
            except Exception as e:
                logger.error(f"关闭WebDriver时出错: {e}")
            finally:
                self.driver = None

    def is_driver_alive(self) -> bool:
        """检查WebDriver是否还活着"""
        if not self.driver:
            return False

        try:
            # 尝试获取当前URL来检查连接
            self.driver.current_url
            return True
        except Exception:
            return False

    def restart_driver(self, **kwargs):
        """重启WebDriver"""
        logger.info("重启WebDriver")
        self.quit_driver()
        return self.create_driver(
            browser=self.browser_type,
            headless=self.headless,
            user_data_dir=self.user_data_dir,
            **kwargs,
        )
