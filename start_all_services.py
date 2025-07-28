#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动所有必要的服务
"""

import subprocess
import time
import threading
import os

def start_localstorage_server():
    """启动localStorage读取服务器"""
    print("正在启动localStorage读取服务器...")
    try:
        subprocess.Popen([
            "python", "localstorage_reader.py"
        ], creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("✅ localStorage读取服务器已启动（端口8080）")
    except Exception as e:
        print(f"❌ 启动localStorage读取服务器失败: {e}")

def start_rpa_app():
    """启动RPA应用"""
    print("正在启动RPA应用...")
    try:
        subprocess.Popen([
            "python", "main.py"
        ], creationflags=subprocess.CREATE_NEW_CONSOLE)
        print("✅ RPA应用已启动（端口3000）")
    except Exception as e:
        print(f"❌ 启动RPA应用失败: {e}")

def open_test_page():
    """打开测试页面"""
    print("正在打开测试页面...")
    try:
        import webbrowser
        test_page = os.path.abspath("test_page.html")
        webbrowser.open(f"file:///{test_page}")
        print("✅ 测试页面已打开")
    except Exception as e:
        print(f"❌ 打开测试页面失败: {e}")

def main():
    """主函数"""
    print("启动所有服务")
    print("=" * 50)
    
    # 启动localStorage读取服务器
    start_localstorage_server()
    time.sleep(2)
    
    # 启动RPA应用
    start_rpa_app()
    time.sleep(2)
    
    # 打开测试页面
    open_test_page()
    
    print("\n" + "=" * 50)
    print("✅ 所有服务已启动！")
    print("\n📋 服务状态:")
    print("- localStorage读取服务器: http://localhost:8080")
    print("- RPA应用: http://localhost:3000")
    print("- 测试页面: test_page.html")
    
    print("\n📋 测试步骤:")
    print("1. 在测试页面中点击'🚀 开始捕获'按钮")
    print("2. 点击页面上的任意元素")
    print("3. 在RPA应用中添加'点击元素(web)'指令")
    print("4. 点击'🔍 捕获元素'按钮")
    print("5. 验证选择器是否自动填入")
    
    print("\n🎯 预期结果:")
    print("✅ 元素捕获成功")
    print("✅ 数据保存到localStorage")
    print("✅ 数据保存到文件服务器")
    print("✅ RPA应用能正确读取元素数据")
    print("✅ 选择器自动填入正确的值")

if __name__ == "__main__":
    main() 