// RPA元素捕获器 - Content Script
class ElementCapture {
    constructor() {
        this.isCapturing = false;
        this.highlightedElement = null;
        this.capturedElements = [];
        this.init();
    }

    init() {
        // 监听键盘事件
        document.addEventListener('keydown', this.handleKeyDown.bind(this));
        document.addEventListener('keyup', this.handleKeyUp.bind(this));
        
        // 监听鼠标事件
        document.addEventListener('mousedown', this.handleMouseDown.bind(this));
        document.addEventListener('mouseover', this.handleMouseOver.bind(this));
        document.addEventListener('mouseout', this.handleMouseOut.bind(this));
        
        // 监听来自popup的消息
        chrome.runtime.onMessage.addListener(this.handleMessage.bind(this));
        
        console.log('RPA元素捕获器已启动');
    }

    handleKeyDown(event) {
        // 检测Ctrl键
        if (event.ctrlKey && !this.isCapturing) {
            this.startCapture();
        }
    }

    handleKeyUp(event) {
        // 释放Ctrl键时停止捕获
        if (!event.ctrlKey && this.isCapturing) {
            this.stopCapture();
        }
    }

    handleMouseDown(event) {
        if (this.isCapturing && event.button === 0) { // 左键
            event.preventDefault();
            event.stopPropagation();
            
            const element = event.target;
            this.captureElement(element, event);
        }
    }

    handleMouseOver(event) {
        if (this.isCapturing) {
            this.highlightElement(event.target);
        }
    }

    handleMouseOut(event) {
        if (this.isCapturing) {
            this.removeHighlight();
        }
    }

    startCapture() {
        this.isCapturing = true;
        document.body.style.cursor = 'crosshair';
        this.showNotification('元素捕获模式已启动，按住Ctrl+鼠标左键点击要捕获的元素');
        console.log('开始元素捕获模式');
    }

    stopCapture() {
        this.isCapturing = false;
        document.body.style.cursor = 'default';
        this.removeHighlight();
        this.hideNotification();
        console.log('停止元素捕获模式');
    }

    highlightElement(element) {
        this.removeHighlight();
        this.highlightedElement = element;
        
        // 添加高亮样式
        element.style.outline = '2px solid #0078d4';
        element.style.outlineOffset = '2px';
        element.style.backgroundColor = 'rgba(0, 120, 212, 0.1)';
        
        // 显示元素信息
        this.showElementInfo(element);
    }

    removeHighlight() {
        if (this.highlightedElement) {
            this.highlightedElement.style.outline = '';
            this.highlightedElement.style.outlineOffset = '';
            this.highlightedElement.style.backgroundColor = '';
            this.highlightedElement = null;
        }
        this.hideElementInfo();
    }

    captureElement(element, event) {
        const elementInfo = this.getElementInfo(element);
        
        // 添加到捕获列表
        this.capturedElements.push(elementInfo);
        
        // 显示捕获成功提示
        this.showCaptureSuccess(elementInfo);
        
        // 直接保存到localStorage，避免chrome.runtime.sendMessage的问题
        this.saveToLocalStorage(elementInfo);
        
        // 尝试发送消息到background script（可选）
        try {
            if (chrome && chrome.runtime && chrome.runtime.sendMessage) {
                chrome.runtime.sendMessage({
                    action: 'elementCaptured',
                    elementInfo: elementInfo
                }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.log('Background script通信失败，但数据已保存到localStorage');
                    } else {
                        console.log('消息发送成功:', response);
                    }
                });
            }
        } catch (error) {
            console.log('Chrome扩展API不可用，但数据已保存到localStorage');
        }
        
        console.log('元素已捕获:', elementInfo);
    }

    getElementInfo(element) {
        const rect = element.getBoundingClientRect();
        const computedStyle = window.getComputedStyle(element);
        
        return {
            tagName: element.tagName.toLowerCase(),
            id: element.id || '',
            className: element.className || '',
            text: element.textContent?.trim().substring(0, 50) || '',
            xpath: this.getXPath(element),
            cssSelector: this.getCSSSelector(element),
            position: {
                x: rect.left + window.scrollX,
                y: rect.top + window.scrollY,
                width: rect.width,
                height: rect.height
            },
            attributes: this.getAttributes(element),
            timestamp: new Date().toISOString(),
            url: window.location.href
        };
    }

    getXPath(element) {
        if (element.id) {
            return `//*[@id="${element.id}"]`;
        }
        
        if (element === document.body) {
            return '/html/body';
        }
        
        let path = '';
        while (element && element.nodeType === Node.ELEMENT_NODE) {
            let index = 1;
            let sibling = element.previousSibling;
            
            while (sibling) {
                if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === element.tagName) {
                    index++;
                }
                sibling = sibling.previousSibling;
            }
            
            const tagName = element.tagName.toLowerCase();
            const pathIndex = index > 1 ? `[${index}]` : '';
            path = `/${tagName}${pathIndex}${path}`;
            
            element = element.parentNode;
        }
        
        return path;
    }

    getCSSSelector(element) {
        if (element.id) {
            return `#${element.id}`;
        }
        
        let selector = element.tagName.toLowerCase();
        
        if (element.className) {
            const classes = element.className.split(' ').filter(c => c.trim());
            if (classes.length > 0) {
                selector += '.' + classes.join('.');
            }
        }
        
        // 添加属性选择器
        const attributes = ['name', 'type', 'value', 'title', 'alt'];
        for (const attr of attributes) {
            if (element.hasAttribute(attr)) {
                selector += `[${attr}="${element.getAttribute(attr)}"]`;
            }
        }
        
        return selector;
    }

    getAttributes(element) {
        const attributes = {};
        for (const attr of element.attributes) {
            attributes[attr.name] = attr.value;
        }
        return attributes;
    }

    showNotification(message) {
        let notification = document.getElementById('rpa-capture-notification');
        if (!notification) {
            notification = document.createElement('div');
            notification.id = 'rpa-capture-notification';
            notification.style.cssText = `
                position: fixed;
                top: 20px;
                right: 20px;
                background: #0078d4;
                color: white;
                padding: 10px 15px;
                border-radius: 5px;
                z-index: 10000;
                font-family: Arial, sans-serif;
                font-size: 14px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.2);
            `;
            document.body.appendChild(notification);
        }
        notification.textContent = message;
        notification.style.display = 'block';
    }

    hideNotification() {
        const notification = document.getElementById('rpa-capture-notification');
        if (notification) {
            notification.style.display = 'none';
        }
    }

    showElementInfo(element) {
        let info = document.getElementById('rpa-element-info');
        if (!info) {
            info = document.createElement('div');
            info.id = 'rpa-element-info';
            info.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 20px;
                background: #333;
                color: white;
                padding: 10px;
                border-radius: 5px;
                z-index: 10000;
                font-family: monospace;
                font-size: 12px;
                max-width: 300px;
                word-wrap: break-word;
            `;
            document.body.appendChild(info);
        }
        
        const elementInfo = this.getElementInfo(element);
        info.innerHTML = `
            <strong>元素信息:</strong><br>
            标签: ${elementInfo.tagName}<br>
            ID: ${elementInfo.id || '无'}<br>
            类名: ${elementInfo.className || '无'}<br>
            文本: ${elementInfo.text || '无'}<br>
            位置: (${Math.round(elementInfo.position.x)}, ${Math.round(elementInfo.position.y)})
        `;
        info.style.display = 'block';
    }

    hideElementInfo() {
        const info = document.getElementById('rpa-element-info');
        if (info) {
            info.style.display = 'none';
        }
    }

    showCaptureSuccess(elementInfo) {
        let success = document.getElementById('rpa-capture-success');
        if (!success) {
            success = document.createElement('div');
            success.id = 'rpa-capture-success';
            success.style.cssText = `
                position: fixed;
                top: 50%;
                left: 50%;
                transform: translate(-50%, -50%);
                background: #28a745;
                color: white;
                padding: 15px 20px;
                border-radius: 5px;
                z-index: 10001;
                font-family: Arial, sans-serif;
                font-size: 16px;
                box-shadow: 0 4px 15px rgba(0,0,0,0.3);
            `;
            document.body.appendChild(success);
        }
        
        success.textContent = `✅ 元素已捕获: ${elementInfo.tagName}${elementInfo.id ? '#' + elementInfo.id : ''}`;
        success.style.display = 'block';
        
        // 2秒后自动隐藏
        setTimeout(() => {
            success.style.display = 'none';
        }, 2000);
    }

    saveToLocalStorage(elementInfo) {
        try {
            // 保存到localStorage作为备用方案
            const storageKey = 'rpa_captured_element_' + Date.now();
            localStorage.setItem(storageKey, JSON.stringify(elementInfo));
            
            // 同时保存最新的元素信息
            localStorage.setItem('rpa_last_captured_element', JSON.stringify(elementInfo));
            localStorage.setItem('rpa_last_capture_time', Date.now().toString());
            
            console.log('元素信息已保存到localStorage:', storageKey);
            
            // 通过消息传递发送到background script，而不是直接调用
            try {
                chrome.runtime.sendMessage({
                    action: 'elementCaptured',
                    elementInfo: elementInfo
                }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.log('Background script通信失败，但数据已保存到localStorage');
                    } else {
                        console.log('消息发送成功:', response);
                    }
                });
            } catch (error) {
                console.log('Chrome扩展API不可用，但数据已保存到localStorage');
            }
            
            // 尝试保存到文件系统（通过HTTP请求）
            this.saveToFileSystem(elementInfo);
            
            // 显示保存成功提示
            this.showNotification('元素信息已保存到本地存储', 'success');
        } catch (error) {
            console.error('保存到localStorage失败:', error);
            this.showNotification('保存失败，请重试', 'error');
        }
    }

    saveToFileSystem(elementInfo) {
        // 修改为正确的路径
        const rpaServerUrl = 'http://localhost:8888/capture_element'; // 改为capture_element
        
        fetch(rpaServerUrl, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'element_captured', // 改为element_captured
                element: elementInfo,
                timestamp: new Date().toISOString()
            })
        })
        .then(response => {
            if (response.ok) {
                console.log('元素信息已保存到文件系统');
            } else {
                console.log('保存到文件系统失败，但数据已保存到localStorage');
            }
        })
        .catch(error => {
            console.log('无法连接到文件系统服务器，但数据已保存到localStorage:', error);
        });
    }

    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.style.cssText = `
            position: fixed;
            top: 20px;
            right: 20px;
            padding: 10px 15px;
            border-radius: 5px;
            color: white;
            font-size: 14px;
            z-index: 10000;
            max-width: 300px;
            word-wrap: break-word;
        `;
        
        if (type === 'success') {
            notification.style.backgroundColor = '#28a745';
        } else if (type === 'error') {
            notification.style.backgroundColor = '#dc3545';
        } else {
            notification.style.backgroundColor = '#007bff';
        }
        
        notification.textContent = message;
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            if (notification.parentNode) {
                notification.parentNode.removeChild(notification);
            }
        }, 3000);
    }

    handleMessage(request, sender, sendResponse) {
        switch (request.action) {
            case 'getCapturedElements':
                sendResponse({ elements: this.capturedElements });
                break;
            case 'clearCapturedElements':
                this.capturedElements = [];
                sendResponse({ success: true });
                break;
            case 'startCapture':
                this.startCapture();
                sendResponse({ success: true });
                break;
            case 'stopCapture':
                this.stopCapture();
                sendResponse({ success: true });
                break;
        }
    }
}

// 初始化元素捕获器
const elementCapture = new ElementCapture();