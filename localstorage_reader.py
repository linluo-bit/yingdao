#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
localStorage数据读取服务器
"""

import json
import os
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

class LocalStorageReader(BaseHTTPRequestHandler):
    """localStorage数据读取处理器"""
    
    def do_GET(self):
        """处理GET请求"""
        if self.path == '/get_last_element':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            
            # 返回模拟的元素数据（用于测试）
            element_data = {
                'tagName': 'button',
                'id': 'startCapture',
                'className': 'button success',
                'text': '开始捕获',
                'xpath': '//*[@id="startCapture"]',
                'cssSelector': '#startCapture',
                'position': {
                    'x': 217,
                    'y': 547.5499877929688,
                    'width': 127.11250305175781,
                    'height': 44
                },
                'attributes': {
                    'id': 'startCapture',
                    'class': 'button success'
                },
                'timestamp': time.strftime('%Y-%m-%dT%H:%M:%S.000Z'),
                'url': 'file:///C:/Users/lin/Desktop/影刀/test_page.html'
            }
            
            self.wfile.write(json.dumps(element_data).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def do_POST(self):
        """处理POST请求"""
        if self.path == '/save_element':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                # 保存元素数据到文件
                self.save_element_to_file(data)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'status': 'success'}).encode())
            except Exception as e:
                self.send_response(500)
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()
    
    def save_element_to_file(self, element_data):
        """保存元素数据到文件"""
        try:
            # 创建数据目录
            data_dir = os.path.join(os.getcwd(), "captured_elements")
            if not os.path.exists(data_dir):
                os.makedirs(data_dir)
            
            # 保存最新元素
            latest_file = os.path.join(data_dir, "latest_element.json")
            with open(latest_file, 'w', encoding='utf-8') as f:
                json.dump(element_data, f, ensure_ascii=False, indent=2)
            
            # 保存带时间戳的文件
            timestamp = int(time.time() * 1000)
            timestamp_file = os.path.join(data_dir, f"element_{timestamp}.json")
            with open(timestamp_file, 'w', encoding='utf-8') as f:
                json.dump(element_data, f, ensure_ascii=False, indent=2)
            
            print(f"元素数据已保存: {latest_file}")
            print(f"时间戳文件: {timestamp_file}")
            
        except Exception as e:
            print(f"保存元素数据失败: {e}")
    
    def log_message(self, format, *args):
        """重写日志方法"""
        pass

def start_server(port=8080):
    """启动服务器"""
    try:
        server = HTTPServer(('localhost', port), LocalStorageReader)
        print(f"localStorage读取服务器已启动，端口: {port}")
        print(f"访问地址: http://localhost:{port}/get_last_element")
        server.serve_forever()
    except Exception as e:
        print(f"启动服务器失败: {e}")

if __name__ == "__main__":
    start_server() 