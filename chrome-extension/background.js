// RPA元素捕获器 - Background Script

// 存储捕获的元素
let capturedElements = [];
// 用户手势标志
let userGestureActive = false;

// RPA应用通信配置
const RPA_SERVER_URL = 'http://localhost:8888'; // 修改端口为8888

// 监听来自content script的消息
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background received message:', request);
    
    switch (request.action) {
        case 'elementCaptured':
            // 保存捕获的元素
            capturedElements.push(request.elementInfo);
            
            // 保存到本地存储
            chrome.storage.local.set({ 
                capturedElements: capturedElements 
            });
            
            // 保存到本地文件（供RPA应用读取）
            saveToLocalFile(request.elementInfo);
            
            // 更新badge显示捕获数量
            updateBadge();
            
            // 发送到RPA应用
            sendToRPAApp(request.elementInfo);
            
            sendResponse({ success: true });
            break;
            
        case 'getCapturedElements':
            sendResponse({ elements: capturedElements });
            break;
            
        case 'clearCapturedElements':
            capturedElements = [];
            chrome.storage.local.remove('capturedElements');
            updateBadge();
            sendResponse({ success: true });
            break;
            
        case 'exportElements':
            // 确保这是用户手势触发的导出
            userGestureActive = true;
            try {
                exportElements();
                sendResponse({ success: true });
            } catch (error) {
                console.error('导出失败:', error);
                sendResponse({ success: false, error: error.message });
            } finally {
                userGestureActive = false;
            }
            break;
            
        case 'sendToRPA':
            // 手动发送最后一个捕获的元素到RPA应用
            if (capturedElements.length > 0) {
                const lastElement = capturedElements[capturedElements.length - 1];
                sendToRPAApp(lastElement);
                sendResponse({ success: true, message: '已发送到RPA应用' });
            } else {
                sendResponse({ success: false, message: '没有可发送的元素' });
            }
            break;
    }
    
    return true; // 保持消息通道开放
});

// 发送元素信息到RPA应用
async function sendToRPAApp(elementInfo) {
    try {
        const response = await fetch(`${RPA_SERVER_URL}/capture_element`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'element_captured',
                element: elementInfo,
                timestamp: new Date().toISOString()
            })
        });
        
        if (response.ok) {
            console.log('元素信息已发送到RPA应用');
        } else {
            console.error('发送到RPA应用失败:', response.status);
        }
    } catch (error) {
        console.error('发送到RPA应用出错:', error);
    }
}

// 保存元素信息到本地文件
function saveToLocalFile(elementInfo) {
    try {
        // 创建数据对象
        const data = {
            capturedElements: [elementInfo],
            timestamp: new Date().toISOString(),
            source: 'chrome-extension'
        };
        chrome.storage.local.set({ 
            lastCapturedElement: data,
            lastCaptureTime: Date.now()
        }, () => {
            console.log('元素信息已保存到本地存储');
        });
    } catch (error) {
        console.error('保存元素信息失败:', error);
    }
}

// 插件安装时的初始化
chrome.runtime.onInstalled.addListener(() => {
    console.log('RPA元素捕获器已安装');
    
    // 从存储中恢复数据
    chrome.storage.local.get(['capturedElements'], (result) => {
        if (result.capturedElements) {
            capturedElements = result.capturedElements;
            updateBadge();
        }
    });
    
    // 设置默认图标
    chrome.action.setIcon({
        path: {
            "16": "icons/icon16.png",
            "48": "icons/icon48.png",
            "128": "icons/icon128.png"
        }
    });
});

// 更新badge显示
function updateBadge() {
    const count = capturedElements.length;
    if (count > 0) {
        chrome.action.setBadgeText({ text: count.toString() });
        chrome.action.setBadgeBackgroundColor({ color: '#0078d4' });
    } else {
        chrome.action.setBadgeText({ text: '' });
    }
}

// 导出元素数据（只在用户点击导出按钮时调用）
function exportElements() {
    if (!userGestureActive) {
        console.error('导出操作必须在用户手势下进行');
        throw new Error('导出操作必须在用户手势下进行');
    }
    
    if (capturedElements.length === 0) {
        console.log('没有可导出的元素');
        return;
    }
    
    try {
        const data = {
            timestamp: new Date().toISOString(),
            elements: capturedElements,
            total: capturedElements.length
        };
        const jsonString = JSON.stringify(data, null, 2);
        const dataUrl = 'data:application/json;charset=utf-8,' + encodeURIComponent(jsonString);
        
        // 使用setTimeout确保在用户手势期间执行
        setTimeout(() => {
            chrome.downloads.download({
                url: dataUrl,
                filename: `rpa-elements-${new Date().toISOString().split('T')[0]}.json`,
                saveAs: true
            }, (downloadId) => {
                if (chrome.runtime.lastError) {
                    console.error('下载失败:', chrome.runtime.lastError);
                } else {
                    console.log('导出成功，下载ID:', downloadId);
                }
            });
        }, 0);
        
    } catch (error) {
        console.error('导出元素失败:', error);
        throw error;
    }
}

// 监听标签页更新
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
    if (changeInfo.status === 'complete' && tab.url) {
        // 注入content script
        chrome.scripting.executeScript({
            target: { tabId: tabId },
            files: ['content.js']
        }).catch(err => {
            console.log('无法注入content script:', err);
        });
    }
});