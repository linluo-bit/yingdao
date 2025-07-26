#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RPA桌面软件主入口文件
复刻影刀RPA的功能
"""

import sys
import logging
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QHBoxLayout, QVBoxLayout, QWidget,
    QSplitter, QTreeWidget, QTreeWidgetItem, QTextEdit, QGraphicsView,
    QGraphicsScene, QPushButton, QStatusBar,
    QDialog, QFormLayout, QLineEdit, QComboBox, QSpinBox, QCheckBox, QDialogButtonBox,
    QMenu, QMessageBox, QGraphicsRectItem, QGraphicsTextItem, QGraphicsEllipseItem, QGraphicsLineItem
)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QMimeData
from PyQt6.QtGui import QAction, QDrag, QBrush, QPen, QFont, QColor

# 导入我们的自动化引擎
from src.core.engine import AutomationEngine

# 设置日志
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


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
        """初始化指令库"""
        # 网页自动化
        web_automation = QTreeWidgetItem(["网页自动化"])
        web_automation.addChild(QTreeWidgetItem(["打开网页"]))
        web_automation.addChild(QTreeWidgetItem(["点击元素(web)"]))
        web_automation.addChild(QTreeWidgetItem(["填写输入框(web)"]))
        web_automation.addChild(QTreeWidgetItem(["获取网页内容"]))
        web_automation.addChild(QTreeWidgetItem(["鼠标悬停在元素上(web)"]))
        self.addTopLevelItem(web_automation)

        # 桌面自动化
        desktop_automation = QTreeWidgetItem(["桌面自动化"])
        desktop_automation.addChild(QTreeWidgetItem(["点击坐标"]))
        desktop_automation.addChild(QTreeWidgetItem(["输入文本"]))
        desktop_automation.addChild(QTreeWidgetItem(["按键操作"]))
        desktop_automation.addChild(QTreeWidgetItem(["鼠标拖拽"]))
        desktop_automation.addChild(QTreeWidgetItem(["截图"]))
        self.addTopLevelItem(desktop_automation)

        # 数据处理
        data_processing = QTreeWidgetItem(["数据处理"])
        data_processing.addChild(QTreeWidgetItem(["读取Excel"]))
        data_processing.addChild(QTreeWidgetItem(["写入Excel"]))
        data_processing.addChild(QTreeWidgetItem(["读取文本文件"]))
        data_processing.addChild(QTreeWidgetItem(["写入文本文件"]))
        self.addTopLevelItem(data_processing)

        # 流程控制
        flow_control = QTreeWidgetItem(["流程控制"])
        flow_control.addChild(QTreeWidgetItem(["循环"]))
        flow_control.addChild(QTreeWidgetItem(["条件判断"]))
        flow_control.addChild(QTreeWidgetItem(["等待"]))
        flow_control.addChild(QTreeWidgetItem(["停止"]))
        self.addTopLevelItem(flow_control)

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
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("RPA自动化平台 - 影刀复刻版")
        self.setGeometry(100, 100, 1200, 800)
        
        # 设置更大的字体
        font = self.font()
        font.setPointSize(10)  # 从默认的9调整为10
        self.setFont(font)
        
        # 将窗口移动到屏幕中央
        self.center_window()
        
        # 自动全屏显示
        self.showMaximized()
        
        # 初始化自动化引擎
        self.automation_engine = AutomationEngine()
        self.automation_engine.set_status_callback(self.update_status)
        self.automation_engine.set_log_callback(self.add_log_message)
        
        # 工作流执行线程
        self.execution_thread = None
        
        # 当前工作流
        self.current_workflow = []
        
        # 创建菜单栏
        self.create_menu_bar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("就绪")
        
        # 创建中央部件
        self.create_central_widget()
        
        logger.info("主窗口初始化完成")
    
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
        
        # 打开配置对话框
        dialog = InstructionConfigDialog(instruction_type, instruction_info, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
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

        # 主要布局
        main_layout = QHBoxLayout(central_widget)

        # 创建分割器
        main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # 左侧面板
        left_panel = self.create_left_panel()
        main_splitter.addWidget(left_panel)

        # 中间面板（画布区域）
        middle_panel = self.create_middle_panel()
        main_splitter.addWidget(middle_panel)

        # 右侧面板
        right_panel = self.create_right_panel()
        main_splitter.addWidget(right_panel)

        # 设置分割器比例 - 调整为更紧凑的布局
        main_splitter.setSizes([200, 750, 150])

        main_layout.addWidget(main_splitter)

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

    def closeEvent(self, event):
        """关闭事件"""
        # 清理资源
        if self.automation_engine:
            self.automation_engine.cleanup()

        if self.execution_thread and self.execution_thread.isRunning():
            self.execution_thread.terminate()
            self.execution_thread.wait()

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
