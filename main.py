#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPA桌面软件主入口文件
复刻影刀RPA的功能
"""

import sys
import logging
import threading
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTextEdit, QGraphicsView,
    QGraphicsScene, QPushButton, QStatusBar,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QCheckBox, QDialogButtonBox,
    QMenu, QMessageBox, QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsLineItem,
    QLabel, QScrollArea, QGridLayout, QFrame, QProgressBar
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData, QTimer
from PyQt6.QtGui import QAction, QDrag, QBrush, QPen, QFont, QColor

# 导入我们的自动化引擎
from src.core.engine import AutomationEngine

# 全局缓存机制
last_element_cache = None
cache_timestamp = 0

# 设置日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('rpa_debug.log'),
        logging.StreamHandler()  # 同时输出到控制台
    ]
)
logger = logging.getLogger(__name__)


class RPARequestHandler(BaseHTTPRequestHandler):
    """RPA应用HTTP请求处理器"""
    
    def __init__(self, *args, rpa_app=None, **kwargs):
        self.rpa_app = rpa_app
        super().__init__(*args, **kwargs)
    
    def do_OPTIONS(self):
        """处理OPTIONS预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.send_header('Access-Control-Max-Age', '86400')  # 24小时缓存
        self.end_headers()
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/ping':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')  # 添加CORS头
            self.end_headers()
            self.wfile.write(json.dumps({'status': 'ok'}).encode())
        elif self.path == '/get_last_element':
            # 添加获取最后捕获元素的接口
            if self.rpa_app and hasattr(self.rpa_app, 'last_captured_element') and self.rpa_app.last_captured_element:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps(self.rpa_app.last_captured_element).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')  # 添加CORS头
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'No element captured'}).encode())
        else:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')  # 添加CORS头
            self.end_headers()
    
    def do_POST(self):
        """处理POST请求"""
        print(f"[DEBUG] 收到POST请求，路径: {self.path}")
        logger.debug(f"收到POST请求，路径: {self.path}")
        
        if self.path in ['/capture_element', '/save_element']:
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            print(f"[DEBUG] POST数据长度: {content_length}")
            print(f"[DEBUG] POST原始数据: {post_data}")
            logger.debug(f"POST数据长度: {content_length}")
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                print(f"[DEBUG] 解析后的JSON数据: {data}")
                logger.debug(f"解析后的JSON数据: {data}")
                
                if data.get('action') in ['element_captured', 'save_element']:
                    element_info = data.get('element', {})
                    
                    # 添加调试日志
                    print(f"[DEBUG] HTTP服务器接收到元素: {element_info.get('tagName', 'unknown')}")
                    logger.info(f"HTTP服务器接收到元素: {element_info.get('tagName', 'unknown')}")
                    
                    # 更新全局缓存
                    global last_element_cache, cache_timestamp
                    last_element_cache = element_info
                    cache_timestamp = time.time()
                    print(f"[DEBUG] 元素已缓存，时间戳: {cache_timestamp}")
                    
                    # 直接保存到 rpa_app 的 last_captured_element
                    if self.rpa_app:
                        self.rpa_app.last_captured_element = element_info
                        print(f"[DEBUG] 已保存到 last_captured_element: {bool(self.rpa_app.last_captured_element)}")
                        logger.debug(f"已保存到 last_captured_element: {bool(self.rpa_app.last_captured_element)}")
                        
                        # 添加更多调试信息
                        print(f"[DEBUG] 准备发送信号到主线程")
                        logger.debug(f"准备发送信号到主线程")
                        
                        # 发送信号到主线程处理元素信息
                        try:
                            self.rpa_app.element_captured_signal.emit(element_info)
                            print(f"[DEBUG] 信号发送成功")
                            logger.debug(f"信号发送成功")
                        except Exception as e:
                            print(f"[ERROR] 信号发送失败: {e}")
                            logger.error(f"信号发送失败: {e}")
                    else:
                        print(f"[ERROR] rpa_app 为空")
                        logger.error(f"rpa_app 为空")
                    
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
                    self.send_header('Access-Control-Allow-Headers', 'Content-Type')
                    self.end_headers()
                    self.wfile.write(json.dumps({'status': 'success'}).encode())
                else:
                    print(f"[DEBUG] 无效的action: {data.get('action')}")
                    logger.debug(f"无效的action: {data.get('action')}")
                    self.send_response(400)
                    self.send_header('Access-Control-Allow-Origin', '*')
                    self.end_headers()
            except json.JSONDecodeError as e:
                print(f"[DEBUG] JSON解析错误: {e}")
                logger.error(f"JSON解析错误: {e}")
                self.send_response(400)
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
        else:
            self.send_response(404)
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
    
    def log_message(self, format, *args):
        """重写日志方法，避免在控制台输出"""
        pass


class RPAServer:
    """RPA应用HTTP服务器"""
    
    def __init__(self, rpa_app, port=8888):
        self.rpa_app = rpa_app
        self.port = port
        self.server = None
        self.server_thread = None
    
    def start(self):
        """启动服务器"""
        try:
            # 创建自定义请求处理器
            def handler(*args, **kwargs):
                return RPARequestHandler(*args, rpa_app=self.rpa_app, **kwargs)
            
            self.server = HTTPServer(('localhost', self.port), handler)
            self.server_thread = threading.Thread(target=self.server.serve_forever, daemon=True)
            self.server_thread.start()
            logger.info(f"RPA HTTP服务器已启动，端口: {self.port}")
        except Exception as e:
            logger.error(f"启动HTTP服务器失败: {e}")

    def stop(self):
        """停止服务器"""
        if self.server:
            self.server.shutdown()
            self.server.server_close()
            logger.info(f"RPA HTTP服务器已停止，端口: {self.port}")


class WorkflowExecutionThread(QThread):
    """工作流执行线程"""

    finished = pyqtSignal(bool)
    status_updated = pyqtSignal(str)
    log_message = pyqtSignal(str)

    def __init__(self, engine, workflow):
        super().__init__()
        self.engine = engine
        self.workflow = workflow

    def run(self):
        """运行工作流"""
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        try:
            result = loop.run_until_complete(
                self.engine.execute_workflow(self.workflow)
            )
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"工作流执行异常: {e}")
            self.finished.emit(False)
        finally:
            loop.close()


class InstructionConfigDialog(QDialog):
    """指令配置对话框"""

    def __init__(self, instruction_type: str, instruction_info: dict, parent=None):
        super().__init__(parent)
        self.instruction_type = instruction_type
        self.instruction_info = instruction_info
        self.parameters = {}

        self.setWindowTitle(f"配置指令: {instruction_type}")
        self.setModal(True)
        self.resize(400, 300)

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 表单布局
        form_layout = QFormLayout()

        # 必需参数
        required_params = self.instruction_info.get("required_parameters", [])
        optional_params = self.instruction_info.get("optional_parameters", {})

        self.param_widgets = {}

        # 添加必需参数
        for param in required_params:
            widget = QLineEdit()
            form_layout.addRow(f"{param} (必需):", widget)
            self.param_widgets[param] = widget

        # 添加可选参数
        for param, default_value in optional_params.items():
            if isinstance(default_value, bool):
                widget = QCheckBox()
                widget.setChecked(default_value)
            elif isinstance(default_value, int):
                widget = QSpinBox()
                widget.setValue(default_value)
                widget.setRange(0, 99999)
            elif isinstance(default_value, str) and param == "browser":
                widget = QComboBox()
                widget.addItems(["chrome", "firefox", "edge"])
                widget.setCurrentText(default_value)
            else:
                widget = QLineEdit()
                widget.setText(str(default_value))

            form_layout.addRow(f"{param}:", widget)
            self.param_widgets[param] = widget

        layout.addLayout(form_layout)

        # 按钮
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def get_parameters(self) -> dict:
        """获取参数"""
        parameters = {}

        for param, widget in self.param_widgets.items():
            if isinstance(widget, QLineEdit):
                value = widget.text().strip()
                if value:
                    parameters[param] = value
            elif isinstance(widget, QCheckBox):
                parameters[param] = widget.isChecked()
            elif isinstance(widget, QSpinBox):
                parameters[param] = widget.value()
            elif isinstance(widget, QComboBox):
                parameters[param] = widget.currentText()

        return parameters


class ClickElementConfigDialog(QDialog):
    """点击元素配置对话框（集成捕获元素功能）"""

    def __init__(self, instruction_info: dict, parent=None):
        super().__init__(parent)
        self.instruction_info = instruction_info
        self.parameters = {}

        self.setWindowTitle("配置点击元素指令")
        self.setModal(True)
        self.resize(500, 400)

        self.setup_ui()

    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)

        # 标题
        title_label = QLabel("点击元素配置")
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title_label)

        # 选择器配置区域
        selector_group = QWidget()
        selector_layout = QVBoxLayout(selector_group)

        # 选择器类型
        selector_type_layout = QHBoxLayout()
        selector_type_layout.addWidget(QLabel("选择器类型:"))
        self.selector_type_combo = QComboBox()
        self.selector_type_combo.addItems(["css", "xpath", "id", "name"])
        self.selector_type_combo.currentTextChanged.connect(self.on_selector_type_changed)
        selector_type_layout.addWidget(self.selector_type_combo)
        selector_type_layout.addStretch()
        selector_layout.addLayout(selector_type_layout)

        # 选择器输入区域
        selector_input_layout = QHBoxLayout()
        selector_input_layout.addWidget(QLabel("选择器:"))
        self.selector_input = QLineEdit()
        self.selector_input.setPlaceholderText("输入CSS选择器、XPath或元素ID")
        selector_input_layout.addWidget(self.selector_input)
        selector_layout.addLayout(selector_input_layout)

        # 捕获元素按钮和状态显示
        capture_layout = QHBoxLayout()
        capture_layout.addStretch()
        
        # 状态标签
        self.capture_status_label = QLabel("")
        self.capture_status_label.setStyleSheet("""
            QLabel {
                color: #0078d4;
                font-weight: bold;
                font-size: 14px;
                background-color: #f0f8ff;
                border: 2px solid #0078d4;
                border-radius: 6px;
                padding: 8px 12px;
                margin: 5px;
            }
        """)
        capture_layout.addWidget(self.capture_status_label)
        
        # 进度条
        self.capture_progress = QProgressBar()
        self.capture_progress.setVisible(False)
        self.capture_progress.setRange(0, 0)  # 无限进度条
        self.capture_progress.setStyleSheet("""
            QProgressBar {
                border: 2px solid #0078d4;
                border-radius: 5px;
                background-color: #f0f0f0;
                text-align: center;
                font-weight: bold;
                color: #0078d4;
            }
            QProgressBar::chunk {
                background-color: #0078d4;
                border-radius: 3px;
            }
        """)
        self.capture_progress.setMaximumWidth(200)  # 增加宽度
        capture_layout.addWidget(self.capture_progress)
        
        self.capture_btn = QPushButton("🔍 捕获元素")
        self.capture_btn.setStyleSheet("""
            QPushButton {
                background-color: #0078d4;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #106ebe;
            }
            QPushButton:disabled {
                background-color: #ccc;
                color: #666;
            }
        """)
        self.capture_btn.clicked.connect(self.capture_element)
        capture_layout.addWidget(self.capture_btn)
        selector_layout.addLayout(capture_layout)

        layout.addWidget(selector_group)

        # 分隔线
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(line)

        # 其他参数
        params_group = QWidget()
        params_layout = QFormLayout(params_group)

        # 超时时间
        self.timeout_spin = QSpinBox()
        self.timeout_spin.setRange(1, 60)
        self.timeout_spin.setValue(10)
        self.timeout_spin.setSuffix(" 秒")
        params_layout.addRow("超时时间:", self.timeout_spin)

        # 等待元素可见
        self.wait_visible_check = QCheckBox()
        self.wait_visible_check.setChecked(True)
        params_layout.addRow("等待元素可见:", self.wait_visible_check)

        # 等待元素可点击
        self.wait_clickable_check = QCheckBox()
        self.wait_clickable_check.setChecked(True)
        params_layout.addRow("等待元素可点击:", self.wait_clickable_check)

        layout.addWidget(params_group)

        # 说明文本
        info_text = """💡 提示：
• 点击"捕获元素"按钮，然后在浏览器中使用Ctrl+鼠标左键选择元素
• 或者手动输入CSS选择器、XPath等
• 选择器类型会影响元素的定位方式"""
        info_label = QLabel(info_text)
        info_label.setStyleSheet("""
            QLabel {
                background-color: #f0f8ff;
                border: 1px solid #0078d4;
                border-radius: 4px;
                padding: 10px;
                color: #333;
                font-size: 12px;
            }
        """)
        info_label.setWordWrap(True)
        layout.addWidget(info_label)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        cancel_btn = QPushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)
        
        ok_btn = QPushButton("确定")
        ok_btn.setStyleSheet("""
            QPushButton {
                background-color: #28a745;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #218838;
            }
        """)
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)
        
        layout.addLayout(button_layout)
        
        # 初始化状态
        self.show_capture_status("点击捕获按钮开始")

    def on_selector_type_changed(self, selector_type):
        """选择器类型改变时的处理"""
        placeholder_map = {
            "css": "输入CSS选择器，如: #login-btn, .submit-button",
            "xpath": "输入XPath，如: //button[@id='login-btn']",
            "id": "输入元素ID，如: login-btn",
            "name": "输入元素name属性，如: username"
        }
        self.selector_input.setPlaceholderText(placeholder_map.get(selector_type, ""))

    def capture_element(self):
        """捕获元素"""
        from PyQt6.QtWidgets import QMessageBox
        import json
        import os
        
        # 显示捕获说明
        msg = QMessageBox()
        msg.setWindowTitle("元素捕获说明")
        msg.setIcon(QMessageBox.Icon.Information)
        msg.setText("""🔍 元素捕获步骤：

1. 点击"确定"后，请切换到浏览器窗口
2. 按住 Ctrl 键进入捕获模式
3. 鼠标悬停时会高亮显示元素
4. 按住 Ctrl + 鼠标左键点击要捕获的元素
5. 捕获完成后，选择器会自动填入

💡 确保已安装Chrome插件并启用！""")
        msg.setStandardButtons(QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Cancel)
        
        if msg.exec() == QMessageBox.StandardButton.Ok:
            # 显示捕获状态
            self.show_capture_status("正在等待元素捕获...")
            self.capture_btn.setEnabled(False)
            self.capture_progress.setVisible(True)
            
            # 创建定时器检查捕获状态
            self.capture_timer = QTimer()
            self.capture_timer.timeout.connect(self.check_capture_status)
            self.capture_timer.start(1000)  # 每秒检查一次
            
            # 设置超时
            self.capture_timeout_timer = QTimer()
            self.capture_timeout_timer.timeout.connect(self.capture_timeout)
            self.capture_timeout_timer.setSingleShot(True)
            self.capture_timeout_timer.start(30000)  # 30秒超时
    
    def show_capture_status(self, message):
        """显示捕获状态"""
        self.capture_status_label.setText(message)
    
    def check_capture_status(self):
        """检查捕获状态"""
        # 首先检查全局缓存
        global last_element_cache, cache_timestamp
        current_time = time.time()
        
        if last_element_cache and (current_time - cache_timestamp) < 30:  # 30秒内的缓存有效
            self.on_element_captured_success(last_element_cache)
            return
        
        # 尝试从Chrome插件获取捕获的元素
        captured_selector = self.get_captured_element_from_plugin()
        
        if captured_selector:
            self.on_element_captured_success(captured_selector)
    
    def on_element_captured_success(self, captured_selector):
        """元素捕获成功处理"""
        # 停止定时器
        if hasattr(self, 'capture_timer'):
            self.capture_timer.stop()
        if hasattr(self, 'capture_timeout_timer'):
            self.capture_timeout_timer.stop()
        
        # 恢复UI状态
        self.capture_btn.setEnabled(True)
        self.capture_progress.setVisible(False)
        self.show_capture_status("捕获成功！")
        
        # 根据当前选择器类型设置选择器
        current_type = self.selector_type_combo.currentText()
        if current_type == "css":
            self.selector_input.setText(captured_selector.get("cssSelector", ""))
        elif current_type == "xpath":
            self.selector_input.setText(captured_selector.get("xpath", ""))
        elif current_type == "id":
            self.selector_input.setText(captured_selector.get("id", ""))
        elif current_type == "name":
            self.selector_input.setText(captured_selector.get("name", ""))
        
        # 显示元素预览
        self.show_element_preview(captured_selector)
        
        # 显示成功消息
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self,
            "捕获成功",
            f"元素已捕获！\n"
            f"标签: {captured_selector.get('tagName', '')}\n"
            f"ID: {captured_selector.get('id', '无')}\n"
            f"文本: {captured_selector.get('text', '')[:30]}...\n"
            f"选择器已自动填入！"
        )
    
    def capture_timeout(self):
        """捕获超时处理"""
        # 停止定时器
        if hasattr(self, 'capture_timer'):
            self.capture_timer.stop()
        
        # 恢复UI状态
        self.capture_btn.setEnabled(True)
        self.capture_progress.setVisible(False)
        self.show_capture_status("捕获超时")
        
        # 显示超时提示
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.warning(
            self,
            "捕获超时",
            "元素捕获超时。\n\n"
            "请确保：\n"
            "1. Chrome插件已正确安装并启用\n"
            "2. 在浏览器中成功捕获了元素\n"
            "3. 插件数据文件存在且可访问\n\n"
            "您可以手动输入选择器或重新尝试捕获。"
        )
    
    def show_element_preview(self, element_data):
        """显示元素预览"""
        preview_text = f"""📋 元素预览：
标签: {element_data.get('tagName', 'unknown')}
ID: {element_data.get('id', '无')}
类名: {element_data.get('className', '无')}
文本: {element_data.get('text', '无')[:50]}..."""
        self.show_capture_status(preview_text)

    def get_captured_element_from_plugin(self):
        """从Chrome插件获取捕获的元素信息"""
        import json
        import os
        import time
        import glob
        import requests
        
        # 首先检查全局缓存
        global last_element_cache, cache_timestamp
        current_time = time.time()
        
        if last_element_cache and (current_time - cache_timestamp) < 30:  # 30秒内的缓存有效
            print(f"从全局缓存获取元素: {last_element_cache.get('tagName', 'unknown')}")
            return last_element_cache
        
        # 检查主窗口是否有最近捕获的元素
        main_window = self.window()
        if hasattr(main_window, 'last_captured_element') and main_window.last_captured_element:
            print(f"从主窗口获取最近捕获的元素: {main_window.last_captured_element.get('tagName', 'unknown')}")
            return main_window.last_captured_element
        
        # 尝试从HTTP服务器获取最新元素
        try:
            response = requests.get('http://localhost:8888/get_last_element', timeout=3)
            if response.status_code == 200:
                element_data = response.json()
                if self._validate_element_data(element_data):
                    print(f"从HTTP服务器获取到元素: {element_data.get('tagName', 'unknown')}")
                    return element_data
        except Exception as e:
            print(f"从HTTP服务器获取元素失败: {e}")
        
        # 尝试从Chrome扩展的本地存储读取（通过文件系统）
        print("尝试从Chrome存储读取元素数据...")
        
        # 直接从captured_elements目录读取最新文件
        captured_dir = os.path.join(os.getcwd(), "captured_elements")
        if os.path.exists(captured_dir):
            print(f"检查captured_elements目录: {captured_dir}")
            
            # 查找所有JSON文件
            json_files = []
            for file in os.listdir(captured_dir):
                if file.endswith('.json'):
                    file_path = os.path.join(captured_dir, file)
                    json_files.append((file_path, os.path.getmtime(file_path)))
            
            if json_files:
                # 按修改时间排序，获取最新的文件
                json_files.sort(key=lambda x: x[1], reverse=True)
                latest_file, latest_time = json_files[0]
                
                # 检查是否在10分钟内
                current_time = time.time()
                if current_time - latest_time < 600:  # 10分钟内
                    try:
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            element_data = json.load(f)
                        
                        if self._validate_element_data(element_data):
                            print(f"从{os.path.basename(latest_file)}找到元素: {element_data.get('tagName', 'unknown')}")
                            return element_data
                        else:
                            print(f"{os.path.basename(latest_file)}中的元素数据无效")
                    except Exception as e:
                        print(f"读取{latest_file}失败: {e}")
                else:
                    print(f"文件时间过久: {current_time - latest_time}秒前")
            else:
                print("captured_elements目录中没有JSON文件")
        else:
            print("captured_elements目录不存在")
        
        # 如果还是没有找到，尝试从Chrome的localStorage文件读取
        print("尝试从Chrome localStorage文件读取...")
        
        # 检查Chrome扩展的本地存储
        chrome_storage_paths = [
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Local Extension Settings"),
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Storage/ext"),
        ]
        
        for storage_path in chrome_storage_paths:
            if os.path.exists(storage_path):
                print(f"检查Chrome存储路径: {storage_path}")
                # 查找可能的扩展ID目录
                for item in os.listdir(storage_path):
                    item_path = os.path.join(storage_path, item)
                    if os.path.isdir(item_path):
                        # 检查是否有local.json文件
                        local_file = os.path.join(item_path, "local.json")
                        if os.path.exists(local_file):
                            try:
                                with open(local_file, 'r', encoding='utf-8') as f:
                                    storage_data = json.load(f)
                                
                                # 查找lastCapturedElement
                                if 'lastCapturedElement' in storage_data:
                                    element = storage_data['lastCapturedElement']
                                    capture_time = storage_data.get('lastCaptureTime', 0)
                                    current_time = time.time() * 1000  # 转换为毫秒
                                    
                                    # 检查是否在10分钟内
                                    if current_time - capture_time < 600000:  # 10分钟
                                        print(f"从Chrome存储中找到元素: {element.get('tagName', 'unknown')}")
                                        return element
                            except Exception as e:
                                print(f"读取Chrome存储失败: {e}")
                                continue
        
        # 检查localStorage数据（通过Chrome存储）
        chrome_storage_paths = [
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Local Storage"),
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Storage/ext"),
        ]
        
        for storage_path in chrome_storage_paths:
            if os.path.exists(storage_path):
                print(f"检查Chrome localStorage路径: {storage_path}")
                # 查找localStorage文件
                for root, dirs, files in os.walk(storage_path):
                    for file in files:
                        if file.endswith('.localstorage') or file.endswith('.ldb'):
                            file_path = os.path.join(root, file)
                            try:
                                # 尝试读取localStorage文件
                                with open(file_path, 'rb') as f:
                                    content = f.read().decode('utf-8', errors='ignore')
                                
                                # 查找RPA相关的数据
                                if 'rpa_last_captured_element' in content:
                                    print(f"找到localStorage文件: {file_path}")
                                    # 这里我们找到了localStorage文件，但需要进一步解析
                                    # 由于localStorage文件格式复杂，我们采用其他方法
                                    break
                            except Exception as e:
                                continue
        
        # 首先检查captured_elements目录中的最新文件
        captured_dir = os.path.join(os.getcwd(), "captured_elements")
        if os.path.exists(captured_dir):
            print(f"检查captured_elements目录: {captured_dir}")
            
            # 检查latest_element.json文件
            latest_file = os.path.join(captured_dir, "latest_element.json")
            if os.path.exists(latest_file):
                try:
                    file_time = os.path.getmtime(latest_file)
                    current_time = time.time()
                    
                    # 检查是否在10分钟内
                    if current_time - file_time < 600:  # 10分钟内
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            element_data = json.load(f)
                        
                        if self._validate_element_data(element_data):
                            print(f"从latest_element.json找到元素: {element_data.get('tagName', 'unknown')}")
                            return element_data
                        else:
                            print("latest_element.json中的元素数据无效")
                except Exception as e:
                    print(f"读取latest_element.json失败: {e}")
            
            # 查找最新的element_*.json文件
            pattern = os.path.join(captured_dir, "element_*.json")
            json_files = glob.glob(pattern)
            
            if json_files:
                # 按修改时间排序，获取最新的文件
                json_files.sort(key=os.path.getmtime, reverse=True)
                latest_file = json_files[0]
                
                try:
                    file_time = os.path.getmtime(latest_file)
                    current_time = time.time()
                    
                    # 检查是否在10分钟内
                    if current_time - file_time < 600:  # 10分钟内
                        with open(latest_file, 'r', encoding='utf-8') as f:
                            element_data = json.load(f)
                        
                        if self._validate_element_data(element_data):
                            print(f"从{os.path.basename(latest_file)}找到元素: {element_data.get('tagName', 'unknown')}")
                            return element_data
                        else:
                            print(f"{os.path.basename(latest_file)}中的元素数据无效")
                except Exception as e:
                    print(f"读取{latest_file}失败: {e}")
        
        # 查找路径列表 - 扩展更多可能的路径
        search_paths = [
            # Chrome插件数据路径
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Local Extension Settings/rpa-element-capture"),
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Storage/ext/rpa-element-capture"),
            os.path.expanduser("~/AppData/Local/Google/Chrome/User Data/Default/Extensions/rpa-element-capture"),
            # 下载文件夹
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~/Desktop"),
            os.path.expanduser("~/Documents"),
            # 当前项目目录
            os.path.join(os.getcwd(), "captured_elements"),
            # 临时目录
            os.path.join(os.getcwd(), "temp"),
        ]
        
        # 创建captured_elements目录（如果不存在）
        captured_dir = os.path.join(os.getcwd(), "captured_elements")
        if not os.path.exists(captured_dir):
            os.makedirs(captured_dir)
            print(f"创建目录: {captured_dir}")
        
        # 查找最新的捕获数据
        latest_element = None
        latest_time = 0
        
        # 首先查找下载文件夹中的捕获文件
        for search_path in search_paths:
            if os.path.exists(search_path):
                print(f"搜索路径: {search_path}")
                # 查找rpa-captured-element-*.json文件，但排除测试文件
                pattern = os.path.join(search_path, "rpa-captured-element-*.json")
                json_files = glob.glob(pattern)
                
                for json_file in json_files:
                    # 跳过测试文件
                    if "test" in os.path.basename(json_file).lower():
                        print(f"跳过测试文件: {os.path.basename(json_file)}")
                        continue
                        
                    try:
                        # 检查文件修改时间
                        file_time = os.path.getmtime(json_file)
                        current_time = time.time()
                        
                        print(f"找到文件: {json_file}, 修改时间: {file_time}, 当前时间: {current_time}")
                        
                        # 扩展时间窗口到10分钟
                        if current_time - file_time < 600:  # 10分钟内
                            with open(json_file, 'r', encoding='utf-8') as f:
                                data = json.load(f)
                                
                            if isinstance(data, dict) and 'capturedElements' in data:
                                elements = data['capturedElements']
                                if elements and len(elements) > 0:
                                    element = elements[0]  # 获取第一个元素
                                    
                                    # 验证元素数据的有效性
                                    if self._validate_element_data(element):
                                        if file_time > latest_time:
                                            latest_time = file_time
                                            latest_element = element
                                            print(f"找到有效元素: {element.get('tagName', 'unknown')}")
                                    else:
                                        print(f"元素数据无效: {element.get('tagName', 'unknown')}")
                                        
                    except Exception as e:
                        print(f"读取文件失败 {json_file}: {e}")
                        continue
        
        # 如果没找到下载文件，尝试从Chrome存储中读取
        if not latest_element:
            print("未找到下载文件，尝试从Chrome存储读取...")
            for data_path in search_paths:
                if os.path.exists(data_path):
                    # 查找存储文件
                    for root, dirs, files in os.walk(data_path):
                        for file in files:
                            if file.endswith('.json') or file == '000003.log':
                                file_path = os.path.join(root, file)
                                try:
                                    # 尝试读取文件内容
                                    with open(file_path, 'r', encoding='utf-8') as f:
                                        content = f.read()
                                        
                                    # 尝试解析JSON数据
                                    try:
                                        data = json.loads(content)
                                        if isinstance(data, dict) and 'capturedElements' in data:
                                            elements = data['capturedElements']
                                            if elements and len(elements) > 0:
                                                # 获取最新的元素
                                                for element in elements:
                                                    # 验证元素数据的有效性
                                                    if not self._validate_element_data(element):
                                                        continue
                                                        
                                                    timestamp = element.get('timestamp', '')
                                                    if timestamp:
                                                        try:
                                                            # 解析时间戳
                                                            if isinstance(timestamp, str):
                                                                import datetime
                                                                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                                                element_time = dt.timestamp()
                                                            else:
                                                                element_time = float(timestamp)
                                                            
                                                            if element_time > latest_time:
                                                                latest_time = element_time
                                                                latest_element = element
                                                                print(f"从存储中找到元素: {element.get('tagName', 'unknown')}")
                                                        except:
                                                            continue
                                    except json.JSONDecodeError:
                                        # 如果不是JSON，尝试从日志文件中提取
                                        if 'capturedElements' in content:
                                            # 简单的文本解析
                                            import re
                                            matches = re.findall(r'\{[^}]+\}', content)
                                            for match in matches:
                                                try:
                                                    element_data = json.loads(match)
                                                    if 'tagName' in element_data and 'timestamp' in element_data:
                                                        # 验证元素数据的有效性
                                                        if not self._validate_element_data(element_data):
                                                            continue
                                                            
                                                        timestamp = element_data.get('timestamp', '')
                                                        if timestamp:
                                                            try:
                                                                if isinstance(timestamp, str):
                                                                    import datetime
                                                                    dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                                                                    element_time = dt.timestamp()
                                                                else:
                                                                    element_time = float(timestamp)
                                                                
                                                                if element_time > latest_time:
                                                                    latest_time = element_time
                                                                    latest_element = element_data
                                                                    print(f"从日志中解析到元素: {element_data.get('tagName', 'unknown')}")
                                                            except:
                                                                continue
                                                except:
                                                    continue
                                                        
                                except Exception as e:
                                    continue
        
        # 如果找到了元素，检查是否在最近10分钟内捕获的
        if latest_element and latest_time > 0:
            current_time = time.time()
            if current_time - latest_time < 600:  # 10分钟内
                print(f"返回捕获的元素: {latest_element.get('tagName', 'unknown')}")
                return latest_element
            else:
                print(f"元素捕获时间过久: {current_time - latest_time}秒前")
        else:
            print("未找到任何捕获的元素")
        
        return None

    def _validate_element_data(self, element):
        """验证元素数据的有效性"""
        if not isinstance(element, dict):
            return False
            
        # 检查必需字段
        required_fields = ['tagName', 'timestamp']
        for field in required_fields:
            if field not in element or not element[field]:
                return False
        
        # 检查是否为测试数据
        if 'test' in str(element).lower():
            return False
            
        # 检查时间戳是否合理（不能是未来时间）
        try:
            timestamp = element.get('timestamp', '')
            if isinstance(timestamp, str):
                import datetime
                dt = datetime.datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                element_time = dt.timestamp()
            else:
                element_time = float(timestamp)
                
            current_time = time.time()
            if element_time > current_time:
                return False
                
        except:
            return False
        
        return True

    def get_parameters(self) -> dict:
        """获取参数"""
        parameters = {
            "selector": self.selector_input.text().strip(),
            "selector_type": self.selector_type_combo.currentText(),
            "timeout": self.timeout_spin.value(),
            "wait_visible": self.wait_visible_check.isChecked(),
            "wait_clickable": self.wait_clickable_check.isChecked(),
        }
        return parameters

    def validate_parameters(self) -> bool:
        """验证参数"""
        if not self.selector_input.text().strip():
            from PyQt6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "参数错误", "请输入选择器或使用捕获元素功能！")
            return False
        return True


class InstructionPanel(QTreeWidget):
    """指令库面板"""

    def __init__(self):
        super().__init__()
        self.setHeaderLabel("指令库")
        self.setFixedWidth(200)

        # 设置更大的字体
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        # 启用拖拽
        self.setDragEnabled(True)
        self.setDragDropMode(QTreeWidget.DragDropMode.DragOnly)

        self.init_instructions()

        # 连接双击事件
        self.itemDoubleClicked.connect(self.on_item_double_clicked)

    def init_instructions(self):
        """初始化指令列表"""
        # 网页自动化
        web_automation = QTreeWidgetItem(["网页自动化"])
        web_automation.addChild(QTreeWidgetItem(["打开网页"]))
        web_automation.addChild(QTreeWidgetItem(["点击元素(web)"]))
        web_automation.addChild(QTreeWidgetItem(["填写输入框(web)"]))
        web_automation.addChild(QTreeWidgetItem(["获取网页内容"]))
        web_automation.addChild(QTreeWidgetItem(["鼠标悬停在元素上(web)"]))
        web_automation.addChild(QTreeWidgetItem(["等待"]))
        self.addTopLevelItem(web_automation)

        # 桌面自动化
        desktop_automation = QTreeWidgetItem(["桌面软件自动化"])
        desktop_automation.addChild(QTreeWidgetItem(["获取窗口对象"]))
        desktop_automation.addChild(QTreeWidgetItem(["获取窗口对象列表"]))
        desktop_automation.addChild(QTreeWidgetItem(["点击元素(win)"]))
        desktop_automation.addChild(QTreeWidgetItem(["鼠标悬停在元素上(win)"]))
        desktop_automation.addChild(QTreeWidgetItem(["填写输入框(win)"]))
        desktop_automation.addChild(QTreeWidgetItem(["运行或打开"]))
        self.addTopLevelItem(desktop_automation)

        # 数据处理
        data_processing = QTreeWidgetItem(["数据处理"])
        data_processing.addChild(QTreeWidgetItem(["变量赋值"]))
        data_processing.addChild(QTreeWidgetItem(["条件判断"]))
        data_processing.addChild(QTreeWidgetItem(["循环"]))
        data_processing.addChild(QTreeWidgetItem(["字符串处理"]))
        data_processing.addChild(QTreeWidgetItem(["数学运算"]))
        self.addTopLevelItem(data_processing)

        # 文件操作
        file_operations = QTreeWidgetItem(["文件操作"])
        file_operations.addChild(QTreeWidgetItem(["读取文件"]))
        file_operations.addChild(QTreeWidgetItem(["写入文件"]))
        file_operations.addChild(QTreeWidgetItem(["复制文件"]))
        file_operations.addChild(QTreeWidgetItem(["删除文件"]))
        file_operations.addChild(QTreeWidgetItem(["创建文件夹"]))
        self.addTopLevelItem(file_operations)

        # 系统操作
        system_operations = QTreeWidgetItem(["系统操作"])
        system_operations.addChild(QTreeWidgetItem(["键盘输入"]))
        system_operations.addChild(QTreeWidgetItem(["鼠标操作"]))
        system_operations.addChild(QTreeWidgetItem(["截图"]))
        system_operations.addChild(QTreeWidgetItem(["发送邮件"]))
        system_operations.addChild(QTreeWidgetItem(["系统通知"]))
        self.addTopLevelItem(system_operations)

        # 展开所有项
        self.expandAll()

    def on_item_double_clicked(self, item, column):
        """处理双击事件"""
        if item.parent():  # 确保是叶子节点（指令）
            instruction_name = item.text(0)
            # 发送信号给主窗口
            main_window = self.window()
            if hasattr(main_window, "on_instruction_selected"):
                main_window.on_instruction_selected(instruction_name)

    def startDrag(self, supportedActions):
        """开始拖拽"""
        item = self.currentItem()
        if item and item.parent():  # 确保是叶子节点（指令）
            drag = QDrag(self)
            mimeData = QMimeData()

            # 设置拖拽数据
            instruction_name = item.text(0)
            mimeData.setText(instruction_name)
            mimeData.setData("application/x-instruction", instruction_name.encode())

            drag.setMimeData(mimeData)

            # 执行拖拽
            drag.exec(Qt.DropAction.CopyAction)


class WorkflowCanvas(QGraphicsView):
    """工作流设计画布"""
    
    # 颜色常量
    CIRCLE_BG_COLOR = QColor(52, 152, 219)  # 蓝色背景
    CIRCLE_BORDER_COLOR = QColor(41, 128, 185)  # 深蓝色边框
    RECT_BG_COLOR = QColor(236, 240, 241)  # 浅灰色背景
    RECT_BORDER_COLOR = QColor(189, 195, 199)  # 灰色边框
    TEXT_COLOR = QColor(44, 62, 80)  # 深灰色文字
    LINE_COLOR = QColor(149, 165, 166)  # 连接线颜色
    SELECTED_BORDER_COLOR = QColor(52, 152, 219)  # 选中时的蓝色边框
    
    def __init__(self):
        super().__init__()
        self.scene = QGraphicsScene()
        self.setScene(self.scene)
        
        # 设置画布属性
        self.setRenderHint(self.renderHints() | self.renderHints().Antialiasing)
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        
        # 启用拖放
        self.setAcceptDrops(True)
        
        # 工作流步骤列表
        self.workflow_steps = []
        
        # 当前选中的步骤
        self.selected_step_index = -1
        
        # 布局参数
        self.start_x = 50  # 起始X坐标
        self.start_y = 50  # 起始Y坐标
        self.step_height = 80  # 每个步骤的高度间距
        self.step_width = 300  # 步骤宽度
        self.step_box_height = 60  # 步骤框高度
        
        # 添加欢迎文本
        self.welcome_text = self.scene.addText(
            "从左侧拖入指令，像搭积木一样构建自动化流程",
            font=self.font()
        )
        self.welcome_text.setPos(self.start_x, self.start_y + 50)
        
        # 设置焦点策略以接收键盘事件
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
    
    def _create_circle_item(self, position, step_number):
        """创建步骤编号圆圈"""
        circle_item = QGraphicsEllipseItem(0, 0, 30, 30)
        circle_item.setBrush(QBrush(self.CIRCLE_BG_COLOR))
        circle_item.setPen(QPen(self.CIRCLE_BORDER_COLOR, 2))
        circle_item.setPos(position.x() - 40, position.y() + 15)
        return circle_item
    
    def _create_number_text(self, position, step_number):
        """创建步骤编号文本"""
        number_text = QGraphicsTextItem(str(step_number))
        number_text.setDefaultTextColor(Qt.GlobalColor.white)
        font = QFont()
        font.setBold(True)
        font.setPointSize(12)
        number_text.setFont(font)
        number_text.setPos(position.x() - 32, position.y() + 18)
        return number_text
    
    def _create_rect_item(self, position):
        """创建指令矩形框"""
        rect_item = QGraphicsRectItem(0, 0, self.step_width, self.step_box_height)
        rect_item.setBrush(QBrush(self.RECT_BG_COLOR))
        rect_item.setPen(QPen(self.RECT_BORDER_COLOR, 2))
        rect_item.setPos(position)
        return rect_item
    
    def _create_text_item(self, position, instruction_name):
        """创建指令名称文本"""
        text_item = QGraphicsTextItem(instruction_name)
        text_item.setDefaultTextColor(self.TEXT_COLOR)
        font = QFont()
        font.setPointSize(12)
        text_item.setFont(font)
        text_item.setPos(position.x() + 15, position.y() + 20)
        return text_item
    
    def _create_line_item(self, position, step_number):
        """创建连接线"""
        if step_number <= 1:
            return None
        
        prev_y = position.y() - self.step_height + self.step_box_height
        line_item = QGraphicsLineItem(
            position.x() + self.step_width // 2, prev_y,
            position.x() + self.step_width // 2, position.y()
        )
        line_item.setPen(QPen(self.LINE_COLOR, 2))
        return line_item

    def dragEnterEvent(self, event):
        """拖拽进入事件"""
        if event.mimeData().hasFormat("application/x-instruction"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        """拖拽移动事件"""
        if event.mimeData().hasFormat("application/x-instruction"):
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        """拖拽放置事件"""
        if event.mimeData().hasFormat("application/x-instruction"):
            # 获取指令名称
            instruction_name = (
                event.mimeData().data("application/x-instruction").data().decode()
            )

            # 移除欢迎文本（如果存在）
            if hasattr(self, "welcome_text") and self.welcome_text:
                self.scene.removeItem(self.welcome_text)
                self.welcome_text = None

            # 计算新指令的位置（按顺序排列）
            step_number = len(self.workflow_steps) + 1
            position_y = self.start_y + (step_number - 1) * self.step_height
            position = self.scene.sceneRect().topLeft()
            position.setX(self.start_x)
            position.setY(position_y)

            # 在画布上添加指令图形项
            self.add_instruction_to_canvas(instruction_name, position, step_number)

            # 通知主窗口处理指令配置
            main_window = self.window()
            if hasattr(main_window, "on_instruction_dropped"):
                main_window.on_instruction_dropped(instruction_name, position)

            event.acceptProposedAction()
        else:
            event.ignore()

    def add_instruction_to_canvas(self, instruction_name, position, step_number):
        """在画布上添加指令图形项"""
        # 创建步骤编号圆圈
        circle_item = self._create_circle_item(position, step_number)

        # 步骤编号文本
        number_text = self._create_number_text(position, step_number)

        # 创建指令矩形框
        rect_item = self._create_rect_item(position)

        # 指令名称文本
        text_item = self._create_text_item(position, instruction_name)

        # 添加连接线（如果不是第一个步骤）
        line_item = self._create_line_item(position, step_number)

        # 添加到场景
        self.scene.addItem(circle_item)
        self.scene.addItem(number_text)
        self.scene.addItem(rect_item)
        self.scene.addItem(text_item)
        if line_item:
            self.scene.addItem(line_item)

        # 保存步骤信息
        step_info = {
            "name": instruction_name,
            "position": position,
            "step_number": step_number,
            "circle_item": circle_item,
            "number_text": number_text,
            "rect_item": rect_item,
            "text_item": text_item,
            "line_item": line_item,
        }
        self.workflow_steps.append(step_info)

        # 自动调整场景大小
        self.scene.setSceneRect(0, 0, 500, position.y() + self.step_box_height + 50)

    def remove_last_step(self):
        """移除最后一个步骤（用于取消配置时）"""
        if not self.workflow_steps:
            return

        last_step = self.workflow_steps[-1]

        # 移除所有图形项
        item_keys = ['circle_item', 'number_text', 'rect_item', 'text_item', 'line_item']
        for key in item_keys:
            if last_step[key]:
                self.scene.removeItem(last_step[key])

        # 从列表中移除
        self.workflow_steps.pop()

        # 如果没有步骤了，恢复欢迎文本
        if not self.workflow_steps:
            self.welcome_text = self.scene.addText(
                "从左侧拖入指令，像搭积木一样构建自动化流程",
                font=self.font()
            )
            self.welcome_text.setPos(self.start_x, self.start_y + 50)

    def mousePressEvent(self, event):
        """鼠标点击事件"""
        if event.button() == Qt.MouseButton.LeftButton:
            scene_pos = self.mapToScene(event.pos())
            clicked_step_index = self.get_step_at_position(scene_pos)
            if clicked_step_index != -1:
                self.select_step(clicked_step_index)
            else:
                self.clear_selection()
        super().mousePressEvent(event)

    def contextMenuEvent(self, event):
        """右键菜单事件"""
        scene_pos = self.mapToScene(event.pos())
        clicked_step_index = self.get_step_at_position(scene_pos)
        if clicked_step_index != -1:
            menu = QMenu(self)
            delete_action = menu.addAction("删除步骤")
            delete_action.triggered.connect(
                lambda: self.delete_step(clicked_step_index)
            )
            edit_action = menu.addAction("编辑步骤")
            edit_action.triggered.connect(lambda: self.edit_step(clicked_step_index))
            menu.exec(event.globalPos())

    def keyPressEvent(self, event):
        """键盘事件"""
        if event.key() == Qt.Key.Key_Delete and self.selected_step_index != -1:
            self.delete_step(self.selected_step_index)
        else:
            super().keyPressEvent(event)

    def get_step_at_position(self, scene_pos):
        """获取指定位置的步骤索引"""
        for i, step in enumerate(self.workflow_steps):
            rect_item = step["rect_item"]
            if rect_item.contains(rect_item.mapFromScene(scene_pos)):
                return i
        return -1

    def select_step(self, step_index):
        """选中步骤"""
        self.clear_selection()
        if 0 <= step_index < len(self.workflow_steps):
            self.selected_step_index = step_index
            step = self.workflow_steps[step_index]
            from PyQt6.QtGui import QPen, QColor

            step["rect_item"].setPen(QPen(self.SELECTED_BORDER_COLOR, 3))  # 蓝色边框

    def clear_selection(self):
        """清除选中状态"""
        if self.selected_step_index != -1:
            step = self.workflow_steps[self.selected_step_index]
            from PyQt6.QtGui import QPen, QColor

            step["rect_item"].setPen(QPen(self.RECT_BORDER_COLOR, 2))
        self.selected_step_index = -1

    def delete_step(self, step_index):
        """删除指定步骤"""
        if not (0 <= step_index < len(self.workflow_steps)):
            return
        
        from PyQt6.QtWidgets import QMessageBox
        step_name = self.workflow_steps[step_index]['name']
        reply = QMessageBox.question(
            self, '确认删除',
            f'确定要删除步骤 "{step_name}" 吗？',
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No
        )
        
        if reply != QMessageBox.StandardButton.Yes:
            return
        
        # 移除图形项
        step_to_remove = self.workflow_steps[step_index]
        item_keys = ['circle_item', 'number_text', 'rect_item', 'text_item', 'line_item']
        for key in item_keys:
            if step_to_remove[key]:
                self.scene.removeItem(step_to_remove[key])
        
        # 从列表中移除
        self.workflow_steps.pop(step_index)
        
        # 从主窗口的工作流中移除对应步骤
        main_window = self.window()
        if hasattr(main_window, 'current_workflow') and step_index < len(main_window.current_workflow):
            main_window.current_workflow.pop(step_index)
        
        # 重新排列剩余步骤
        self.rearrange_steps()
        
        # 清除选中状态
        self.selected_step_index = -1
        
        # 如果没有步骤了，恢复欢迎文本
        if not self.workflow_steps:
            self.welcome_text = self.scene.addText(
                "从左侧拖入指令，像搭积木一样构建自动化流程",
                font=self.font()
            )
            self.welcome_text.setPos(self.start_x, self.start_y + 50)

    def rearrange_steps(self):
        """重新排列步骤位置和编号"""
        for i, step in enumerate(self.workflow_steps):
            new_step_number = i + 1
            new_position_y = self.start_y + i * self.step_height
            step["step_number"] = new_step_number
            step["number_text"].setPlainText(str(new_step_number))
            step["circle_item"].setPos(self.start_x - 40, new_position_y + 15)
            step["number_text"].setPos(self.start_x - 32, new_position_y + 18)
            step["rect_item"].setPos(self.start_x, new_position_y)
            step["text_item"].setPos(self.start_x + 15, new_position_y + 20)
            if step["line_item"]:
                self.scene.removeItem(step["line_item"])
                step["line_item"] = None
            if i > 0:
                from PyQt6.QtWidgets import QGraphicsLineItem
                from PyQt6.QtGui import QPen, QColor

                prev_y = new_position_y - self.step_height + self.step_box_height
                line_item = QGraphicsLineItem(
                    self.start_x + self.step_width // 2,
                    prev_y,
                    self.start_x + self.step_width // 2,
                    new_position_y,
                )
                line_item.setPen(QPen(self.LINE_COLOR, 2))
                self.scene.addItem(line_item)
                step["line_item"] = line_item
        if self.workflow_steps:
            last_step_y = (
                self.start_y + (len(self.workflow_steps) - 1) * self.step_height
            )
            self.scene.setSceneRect(0, 0, 500, last_step_y + self.step_box_height + 50)

    def edit_step(self, step_index):
        """编辑步骤"""
        if not (0 <= step_index < len(self.workflow_steps)):
            return
        main_window = self.window()
        if hasattr(main_window, "edit_workflow_step"):
            main_window.edit_workflow_step(step_index)
        else:
            from PyQt6.QtWidgets import QMessageBox

            QMessageBox.information(self, "提示", "编辑功能暂未实现")


class ProjectExplorer(QTreeWidget):
    """项目管理面板"""

    def __init__(self):
        super().__init__()
        self.setHeaderLabel("流程")
        self.setFixedWidth(150)

        # 设置更大的字体
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        self.init_projects()

    def init_projects(self):
        """初始化项目结构"""
        # 当前项目
        current_project = QTreeWidgetItem(["未命名的应用"])
        current_project.addChild(QTreeWidgetItem(["引用"]))
        current_project.addChild(QTreeWidgetItem(["资源文件"]))

        # 流程节点
        main_flow = QTreeWidgetItem(["主流程.flow"])
        sub_flow = QTreeWidgetItem(["子流程1.flow"])
        current_project.addChild(main_flow)
        current_project.addChild(sub_flow)

        self.addTopLevelItem(current_project)
        self.expandAll()


class LogPanel(QTextEdit):
    """日志面板"""

    def __init__(self):
        super().__init__()
        self.setMaximumHeight(150)
        self.setReadOnly(True)

        # 设置更大的字体
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        # 添加示例日志
        self.append("=== 运行日志 ===")
        self.append("系统初始化完成")
        self.append("等待用户操作...")


class AutomationPluginDialog(QDialog):
    """自动化插件管理对话框"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("自动化插件")
        self.setModal(True)
        self.resize(800, 600)
        self.setup_ui()
    
    def setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        
        # 说明文本
        description = QLabel(
            "自动化插件是影刀RPA执行相应自动化必备的扩展程序，请按需安装，若不确定可根据应用运行时的错误指引进行安装"
        )
        description.setWordWrap(True)
        description.setStyleSheet("QLabel { padding: 10px; background-color: #f0f0f0; border-radius: 5px; }")
        layout.addWidget(description)
        
        # 创建滚动区域
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        scroll_layout = QVBoxLayout(scroll_widget)
        
        # 常规插件区域
        regular_label = QLabel("常规")
        regular_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; margin: 10px 0; }")
        scroll_layout.addWidget(regular_label)
        
        # 插件网格布局
        plugin_grid = QGridLayout()
        
        # 定义插件列表
        plugins = [
            {
                "name": "Google Chrome 自动化",
                "description": "支持谷歌浏览器实现自动化能力",
                "icon": "🌐",
                "status": "installed",  # installed, not_installed
                "action": "重新安装"
            },
            {
                "name": "Microsoft Edge 自动化", 
                "description": "支持微软 Edge 浏览器实现自动化能力",
                "icon": "🌐",
                "status": "not_installed",
                "action": "安装"
            },
            {
                "name": "Firefox 自动化",
                "description": "支持 Firefox 浏览器支持自动化能力", 
                "icon": "🦊",
                "status": "not_installed",
                "action": "安装"
            },
            {
                "name": "Java 自动化",
                "description": "支持 Java 桌面应用实现自动化能力",
                "icon": "☕",
                "status": "not_installed", 
                "action": "安装"
            },
            {
                "name": "Android 手机自动化",
                "description": "支持 Android 手机实现自动化能力",
                "icon": "🤖",
                "status": "not_installed",
                "action": "安装"
            },
            {
                "name": "360 安全浏览器自动化",
                "description": "支持360安全浏览器实现自动化能力",
                "icon": "🛡️",
                "status": "installed",
                "action": "重新安装"
            }
        ]
        
        # 创建插件卡片
        for i, plugin in enumerate(plugins):
            card = self.create_plugin_card(plugin)
            row = i // 2
            col = i % 2
            plugin_grid.addWidget(card, row, col)
        
        # 添加自定义插件卡片
        custom_card = self.create_custom_plugin_card()
        plugin_grid.addWidget(custom_card, len(plugins) // 2, len(plugins) % 2)
        
        scroll_layout.addLayout(plugin_grid)
        
        # 扩展区域
        extension_label = QLabel("扩展")
        extension_label.setStyleSheet("QLabel { font-size: 16px; font-weight: bold; margin: 10px 0; }")
        scroll_layout.addWidget(extension_label)
        
        # 扩展区域占位
        extension_placeholder = QLabel("暂无扩展插件")
        extension_placeholder.setStyleSheet("QLabel { color: #999; padding: 20px; }")
        extension_placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        scroll_layout.addWidget(extension_placeholder)
        
        scroll_layout.addStretch()
        
        # 设置滚动区域
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)
        
        # 底部按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        close_btn = QPushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)
        
        layout.addLayout(button_layout)
    
    def create_plugin_card(self, plugin):
        """创建插件卡片"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: white;
                border: 1px solid #ddd;
                border-radius: 8px;
                padding: 15px;
                margin: 5px;
            }
            QWidget:hover {
                border-color: #0078d4;
                box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            }
        """)
        
        layout = QVBoxLayout(card)
        
        # 插件标题和图标
        header_layout = QHBoxLayout()
        icon_label = QLabel(plugin["icon"])
        icon_label.setStyleSheet("font-size: 24px;")
        header_layout.addWidget(icon_label)
        
        title_label = QLabel(plugin["name"])
        title_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        layout.addLayout(header_layout)
        
        # 描述
        desc_label = QLabel(plugin["description"])
        desc_label.setWordWrap(True)
        desc_label.setStyleSheet("color: #666; margin: 5px 0;")
        layout.addWidget(desc_label)
        
        # 按钮区域
        button_layout = QHBoxLayout()
        button_layout.addStretch()
        
        # 详情按钮
        detail_btn = QPushButton("详情 ↗")
        detail_btn.setStyleSheet("""
            QPushButton {
                border: none;
                color: #0078d4;
                text-decoration: underline;
                padding: 5px;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
                border-radius: 3px;
            }
        """)
        detail_btn.clicked.connect(lambda: self.show_plugin_details(plugin))
        button_layout.addWidget(detail_btn)
        
        # 安装/重新安装按钮
        action_btn = QPushButton(plugin["action"])
        if plugin["status"] == "installed":
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #f0f0f0;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                    padding: 5px 15px;
                    color: #666;
                }
                QPushButton:hover {
                    background-color: #e0e0e0;
                }
            """)
        else:
            action_btn.setStyleSheet("""
                QPushButton {
                    background-color: #0078d4;
                    border: 1px solid #0078d4;
                    border-radius: 4px;
                    padding: 5px 15px;
                    color: white;
                }
                QPushButton:hover {
                    background-color: #106ebe;
                }
            """)
        
        action_btn.clicked.connect(lambda: self.install_plugin(plugin))
        button_layout.addWidget(action_btn)
        
        layout.addLayout(button_layout)
        
        return card
    
    def create_custom_plugin_card(self):
        """创建自定义插件卡片"""
        card = QWidget()
        card.setStyleSheet("""
            QWidget {
                background-color: #f8f9fa;
                border: 2px dashed #ccc;
                border-radius: 8px;
                padding: 20px;
                margin: 5px;
            }
            QWidget:hover {
                border-color: #0078d4;
                background-color: #f0f8ff;
            }
        """)
        
        layout = QVBoxLayout(card)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # 加号图标
        plus_label = QLabel("+")
        plus_label.setStyleSheet("font-size: 32px; color: #999; font-weight: bold;")
        plus_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(plus_label)
        
        # 文本
        text_label = QLabel("添加自定义浏览器自动化")
        text_label.setStyleSheet("color: #999; margin-top: 10px;")
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(text_label)
        
        return card
    
    def show_plugin_details(self, plugin):
        """显示插件详情"""
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(
            self, 
            f"{plugin['name']} - 详情",
            f"插件名称: {plugin['name']}\n\n"
            f"功能描述: {plugin['description']}\n\n"
            f"安装状态: {'已安装' if plugin['status'] == 'installed' else '未安装'}\n\n"
            f"版本信息: 1.0.0\n"
            f"兼容性: Windows 10/11\n"
            f"更新时间: 2024-01-01"
        )
    
    def install_plugin(self, plugin):
        """安装插件"""
        from PyQt6.QtWidgets import QMessageBox
        if plugin["status"] == "installed":
            QMessageBox.information(self, "重新安装", f"正在重新安装 {plugin['name']}...")
        else:
            QMessageBox.information(self, "安装插件", f"正在安装 {plugin['name']}...")


class MainWindow(QMainWindow):
    """主窗口"""
    
    # 指令名称映射常量
    INSTRUCTION_MAP = {
        "打开网页": "open_webpage",
        "点击元素(web)": "click_element",
        "填写输入框(web)": "input_text",
        "获取网页内容": "extract_text",
        "鼠标悬停在元素上(web)": "hover_element",
        "等待": "wait",
    }
    
    # 添加元素捕获信号
    element_captured_signal = pyqtSignal(dict)
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RPA自动化平台 - 影刀复刻版")
        self.setGeometry(100, 100, 1200, 800)
        self.center_window()
        self.showMaximized()

        # 设置更大的字体
        font = self.font()
        font.setPointSize(10)
        self.setFont(font)

        # 初始化自动化引擎
        self.automation_engine = AutomationEngine()
        self.automation_engine.set_status_callback(self.update_status)
        self.automation_engine.set_log_callback(self.add_log_message)

        # 当前工作流
        self.current_workflow = []
        self.execution_thread = None

        # 创建界面
        self.create_menu_bar()
        self.create_central_widget()
        self.create_status_bar()

        # 初始化HTTP服务器
        self.rpa_server = RPAServer(self, port=8888)
        self.rpa_server.start()
        
        # 连接元素捕获信号
        self.element_captured_signal.connect(self.on_element_captured)
        
        # 存储最近捕获的元素信息
        self.last_captured_element = None
    
    def _process_instruction(self, instruction_name: str, position=None):
        """处理指令的公共逻辑"""
        instruction_type = self.INSTRUCTION_MAP.get(instruction_name)
        if not instruction_type:
            self.add_log_message(f"未知指令: {instruction_name}")
            return False
        
        # 获取指令信息
        instruction_info = self.automation_engine.get_instruction_info(instruction_type)
        if not instruction_info:
            self.add_log_message(f"无法获取指令信息: {instruction_type}")
            return False
        
        # 根据指令类型选择不同的配置对话框
        if instruction_type == "click_element":
            # 使用专门的点击元素配置对话框
            dialog = ClickElementConfigDialog(instruction_info, self)
        else:
            # 使用通用配置对话框
            dialog = InstructionConfigDialog(instruction_type, instruction_info, self)
        
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # 验证参数（如果对话框有验证方法）
            if hasattr(dialog, 'validate_parameters') and not dialog.validate_parameters():
                return False
                
            parameters = dialog.get_parameters()
            
            # 添加到工作流
            step = {"type": instruction_type, "parameters": parameters}
            if position:
                step["position"] = {"x": position.x(), "y": position.y()}
            self.current_workflow.append(step)
            
            self.add_log_message(f"添加指令: {instruction_name} -> {instruction_type}")
            self.add_log_message(f"参数: {parameters}")
            return True
        else:
            # 如果用户取消配置，从画布移除指令
            if position and hasattr(self, 'canvas'):
                self.canvas.remove_last_step()
            return False
    
    def center_window(self):
        """将窗口移动到屏幕中央"""
        # 获取屏幕几何信息
        screen = self.screen()
        screen_geometry = screen.geometry()

        # 计算窗口应该放置的位置
        x = (screen_geometry.width() - self.width()) // 2
        y = (screen_geometry.height() - self.height()) // 2

        # 移动窗口到中央位置
        self.move(x, y)

    def create_menu_bar(self):
        """创建菜单栏"""
        menubar = self.menuBar()

        # 文件菜单
        file_menu = menubar.addMenu("文件")

        new_action = QAction("新建项目", self)
        new_action.setStatusTip("创建新的RPA项目")
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)

        open_action = QAction("打开项目", self)
        open_action.setStatusTip("打开现有项目")
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        exit_action = QAction("退出", self)
        exit_action.setStatusTip("退出应用程序")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # 运行菜单
        run_menu = menubar.addMenu("运行")

        start_action = QAction("开始执行", self)
        start_action.setStatusTip("开始执行当前流程")
        start_action.triggered.connect(self.start_workflow)
        run_menu.addAction(start_action)

        test_action = QAction("测试网页自动化", self)
        test_action.setStatusTip("运行网页自动化测试")
        test_action.triggered.connect(self.test_web_automation)
        run_menu.addAction(test_action)

        stop_action = QAction("停止执行", self)
        stop_action.setStatusTip("停止当前执行")
        stop_action.triggered.connect(self.stop_workflow)
        run_menu.addAction(stop_action)

        # 帮助菜单
        help_menu = menubar.addMenu("帮助")

        about_action = QAction("关于", self)
        about_action.setStatusTip("关于本软件")
        help_menu.addAction(about_action)

    def create_central_widget(self):
        """创建中央部件"""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 创建主布局
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)

        # 创建分割器
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)

        # 左侧面板
        left_panel = self.create_left_panel()
        splitter.addWidget(left_panel)

        # 中间面板
        middle_panel = self.create_middle_panel()
        splitter.addWidget(middle_panel)

        # 右侧面板
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)

        # 设置分割器比例
        splitter.setSizes([200, 600, 200])

    def create_status_bar(self):
        """创建状态栏"""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")

    def create_left_panel(self):
        """创建左侧指令库面板"""
        return InstructionPanel()

    def create_middle_panel(self):
        """创建中间工作区"""
        middle_widget = QWidget()
        layout = QVBoxLayout(middle_widget)

        # 工具栏
        toolbar_layout = QHBoxLayout()

        run_btn = QPushButton("▶ 运行")
        run_btn.clicked.connect(self.start_workflow)
        toolbar_layout.addWidget(run_btn)

        stop_btn = QPushButton("⏹ 停止")
        stop_btn.clicked.connect(self.stop_workflow)
        toolbar_layout.addWidget(stop_btn)

        test_btn = QPushButton("🧪 测试")
        test_btn.clicked.connect(self.test_web_automation)
        toolbar_layout.addWidget(test_btn)

        toolbar_layout.addStretch()

        debug_btn = QPushButton("🐛 调试")
        toolbar_layout.addWidget(debug_btn)
        
        # 添加自动化插件按钮
        plugin_btn = QPushButton("🔌 自动化插件")
        plugin_btn.clicked.connect(self.open_automation_plugins)
        toolbar_layout.addWidget(plugin_btn)

        layout.addLayout(toolbar_layout)

        # 画布
        self.canvas = WorkflowCanvas()
        layout.addWidget(self.canvas)

        # 日志面板
        self.log_panel = LogPanel()
        layout.addWidget(self.log_panel)

        return middle_widget

    def create_right_panel(self):
        """创建右侧项目管理面板"""
        return ProjectExplorer()

    def new_project(self):
        """新建项目"""
        self.status_bar.showMessage("创建新项目...")
        self.log_panel.append("创建新项目")
        logger.info("用户创建新项目")

    def on_instruction_selected(self, instruction_name: str):
        """处理指令选择"""
        self._process_instruction(instruction_name)

    def on_instruction_dropped(self, instruction_name: str, position):
        """处理指令拖放"""
        self._process_instruction(instruction_name, position)

    def start_workflow(self):
        """开始执行工作流"""
        if not self.current_workflow:
            self.add_log_message("工作流为空，无法执行")
            return

        if self.execution_thread and self.execution_thread.isRunning():
            self.add_log_message("已有工作流在执行中")
            return

        self.add_log_message("开始执行工作流...")

        # 创建执行线程
        self.execution_thread = WorkflowExecutionThread(
            self.automation_engine, self.current_workflow
        )
        self.execution_thread.finished.connect(self.on_workflow_finished)
        self.execution_thread.start()

    def test_web_automation(self):
        """测试网页自动化"""
        self.add_log_message("开始网页自动化测试...")

        # 使用示例工作流
        test_workflow = self.automation_engine.create_sample_workflow()

        if self.execution_thread and self.execution_thread.isRunning():
            self.add_log_message("已有工作流在执行中")
            return

        # 创建执行线程
        self.execution_thread = WorkflowExecutionThread(
            self.automation_engine, test_workflow
        )
        self.execution_thread.finished.connect(self.on_workflow_finished)
        self.execution_thread.start()

    def stop_workflow(self):
        """停止工作流执行"""
        if self.automation_engine.is_running:
            self.automation_engine.stop_execution()
            self.add_log_message("正在停止执行...")
        else:
            self.add_log_message("当前没有执行中的工作流")

    def on_workflow_finished(self, success: bool):
        """工作流执行完成"""
        if success:
            self.add_log_message("✅ 工作流执行成功完成")
        else:
            self.add_log_message("❌ 工作流执行失败或被中断")

        self.status_bar.showMessage("就绪")

    def update_status(self, status: str):
        """更新状态栏"""
        self.status_bar.showMessage(status)

    def add_log_message(self, message: str):
        """添加日志消息"""
        from datetime import datetime
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_panel.append(f"[{timestamp}] {message}")

    def open_automation_plugins(self):
        """打开自动化插件管理"""
        self.add_log_message("打开自动化插件管理...")
        dialog = AutomationPluginDialog(self)
        dialog.exec()

    def on_element_captured(self, element_info: dict):
        """处理元素捕获信号"""
        # 更新全局缓存
        global last_element_cache, cache_timestamp
        last_element_cache = element_info
        cache_timestamp = time.time()
        
        self.last_captured_element = element_info
        self.add_log_message(f"✅ 捕获到元素: {element_info.get('tagName', 'unknown')} - {element_info.get('text', '')[:30]}...")
        
        # 显示捕获成功的状态栏消息
        self.status_bar.showMessage(f"元素捕获成功: {element_info.get('tagName', 'unknown')}", 3000)

    def closeEvent(self, event):
        """关闭事件"""
        # 停止工作流执行
        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.terminate()
            self.execution_thread.wait()
        
        # 停止HTTP服务器
        if hasattr(self, 'rpa_server'):
            self.rpa_server.stop()
        
        # 清理自动化引擎
        if self.automation_engine:
            self.automation_engine.cleanup()
        
        event.accept()


def main():
    """主函数"""
    app = QApplication(sys.argv)

    # 设置应用程序属性
    app.setApplicationName("RPA自动化平台")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("RPA Dev Team")

    # 创建主窗口
    window = MainWindow()
    window.show()

    logger.info("应用程序启动完成")

    # 运行应用程序
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
