// RPA元素捕获器 - Popup Script

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const statusEl = document.getElementById('status');
    const startBtn = document.getElementById('startBtn');
    const stopBtn = document.getElementById('stopBtn');
    const exportBtn = document.getElementById('exportBtn');
    const clearBtn = document.getElementById('clearBtn');
    const sendToRPABtn = document.getElementById('sendToRPABtn');
    const elementsList = document.getElementById('elementsList');
    
    let isCapturing = false;
    let capturedElements = [];
    
    // 初始化
    init();
    
    // 事件监听
    startBtn.addEventListener('click', startCapture);
    stopBtn.addEventListener('click', stopCapture);
    exportBtn.addEventListener('click', exportElements);
    clearBtn.addEventListener('click', clearElements);
    sendToRPABtn.addEventListener('click', sendToRPA);
    
    function init() {
        // 获取当前标签页
        chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
            const currentTab = tabs[0];
            
            // 获取已捕获的元素
            chrome.runtime.sendMessage({ action: 'getCapturedElements' }, function(response) {
                if (response && response.elements) {
                    capturedElements = response.elements;
                    updateElementsList();
                }
            });
            
            // 检查当前页面是否支持捕获
            if (currentTab.url.startsWith('http')) {
                updateStatus('准备就绪 - 按住Ctrl键开始捕获');
            } else {
                updateStatus('当前页面不支持元素捕获', 'error');
            }
        });
    }
    
    function startCapture() {
        chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
            const currentTab = tabs[0];
            
            chrome.tabs.sendMessage(currentTab.id, { action: 'startCapture' }, function(response) {
                if (response && response.success) {
                    isCapturing = true;
                    updateStatus('捕获模式已启动 - 按住Ctrl+鼠标左键点击元素', 'active');
                    startBtn.disabled = true;
                    stopBtn.disabled = false;
                } else {
                    updateStatus('启动捕获失败', 'error');
                }
            });
        });
    }
    
    function stopCapture() {
        chrome.tabs.query({ active: true, currentWindow: true }, function(tabs) {
            const currentTab = tabs[0];
            
            chrome.tabs.sendMessage(currentTab.id, { action: 'stopCapture' }, function(response) {
                if (response && response.success) {
                    isCapturing = false;
                    updateStatus('捕获模式已停止', 'inactive');
                    startBtn.disabled = false;
                    stopBtn.disabled = true;
                }
            });
        });
    }
    
    function exportElements() {
        chrome.runtime.sendMessage({ action: 'exportElements' }, function(response) {
            if (response && response.success) {
                updateStatus('数据导出成功', 'success');
            } else {
                updateStatus('导出失败', 'error');
            }
        });
    }
    
    function clearElements() {
        if (confirm('确定要清空所有捕获的元素吗？')) {
            chrome.runtime.sendMessage({ action: 'clearCapturedElements' }, function(response) {
                if (response && response.success) {
                    capturedElements = [];
                    updateElementsList();
                    updateStatus('元素列表已清空', 'success');
                }
            });
        }
    }
    
    function sendToRPA() {
        chrome.runtime.sendMessage({ action: 'sendToRPA' }, function(response) {
            if (response && response.success) {
                updateStatus(response.message, 'success');
            } else {
                updateStatus(response.message || '发送失败', 'error');
            }
        });
    }
    
    function updateStatus(message, type = 'normal') {
        statusEl.textContent = message;
        statusEl.className = 'status';
        
        if (type === 'active') {
            statusEl.classList.add('active');
        } else if (type === 'error') {
            statusEl.style.background = '#f8d7da';
            statusEl.style.borderColor = '#dc3545';
            statusEl.style.color = '#721c24';
        } else if (type === 'success') {
            statusEl.style.background = '#d4edda';
            statusEl.style.borderColor = '#28a745';
            statusEl.style.color = '#155724';
        }
    }
    
    function updateElementsList() {
        if (capturedElements.length === 0) {
            elementsList.innerHTML = '<div class="empty-state">暂无捕获的元素</div>';
            return;
        }
        
        elementsList.innerHTML = '';
        
        capturedElements.forEach((element, index) => {
            const elementItem = document.createElement('div');
            elementItem.className = 'element-item';
            
            const tagName = element.tagName || 'unknown';
            const id = element.id || '';
            const text = element.text || '';
            
            elementItem.innerHTML = `
                <div>
                    <span class="element-tag">${tagName}</span>
                    ${id ? `<span class="element-id">#${id}</span>` : ''}
                </div>
                ${text ? `<div class="element-text">"${text}"</div>` : ''}
            `;
            
            // 点击元素项显示详细信息
            elementItem.addEventListener('click', function() {
                showElementDetails(element, index);
            });
            
            elementsList.appendChild(elementItem);
        });
    }
    
    function showElementDetails(element, index) {
        const details = `
元素详细信息 (${index + 1}/${capturedElements.length}):

标签名: ${element.tagName}
ID: ${element.id || '无'}
类名: ${element.className || '无'}
文本内容: ${element.text || '无'}
XPath: ${element.xpath}
CSS选择器: ${element.cssSelector}
位置: (${element.position.x}, ${element.position.y})
尺寸: ${element.position.width} x ${element.position.height}
URL: ${element.url}
时间: ${new Date(element.timestamp).toLocaleString()}
        `;
        
        alert(details);
    }
    
    // 监听来自background的消息
    chrome.runtime.onMessage.addListener(function(request, sender, sendResponse) {
        if (request.action === 'elementCaptured') {
            // 刷新元素列表
            chrome.runtime.sendMessage({ action: 'getCapturedElements' }, function(response) {
                if (response && response.elements) {
                    capturedElements = response.elements;
                    updateElementsList();
                }
            });
        }
    });
    
    // 页面卸载时停止捕获
    window.addEventListener('beforeunload', function() {
        if (isCapturing) {
            stopCapture();
        }
    });
}); 