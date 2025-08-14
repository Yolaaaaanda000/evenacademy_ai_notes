// 知识点对话页面JavaScript

// 全局变量
let dialogueHistory = [];
let dialogueState = {
    round: 0,
    focus_deviation_count: 0
};
let knowledgePointData = {};
let currentLanguage = 'English';

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    initializePage();
    updateWelcomeTime();
});

// 初始化页面
function initializePage() {
    // 从URL参数获取知识点数据
    const urlParams = new URLSearchParams(window.location.search);
    const knowledgePointJson = urlParams.get('knowledge_point');
    
    if (knowledgePointJson) {
        try {
            knowledgePointData = JSON.parse(decodeURIComponent(knowledgePointJson));
            displayKnowledgePointInfo();
        } catch (error) {
                    console.error('Failed to parse knowledge point data:', error);
        showError('Failed to load knowledge point information');
        }
    } else {
        showError('Knowledge point information not found');
    }
    
    // 设置输入框事件
    setupInputEvents();
}

// 显示知识点信息
function displayKnowledgePointInfo() {
    document.getElementById('knowledge-point-title').textContent = knowledgePointData.title || 'Unknown Knowledge Point';
    document.getElementById('knowledge-point-timestamp').textContent = knowledgePointData.timestamp || '-';
    document.getElementById('video-title').textContent = knowledgePointData.video_title || '-';
    document.getElementById('related-concepts').textContent = knowledgePointData.related_concepts || '-';
    document.getElementById('knowledge-point-content').innerHTML = `<div class="content-text">${knowledgePointData.content || 'No content available'}</div>`;
    
    // 设置语言
    currentLanguage = knowledgePointData.language || 'English';
}

// 设置输入框事件
function setupInputEvents() {
    const chatInput = document.getElementById('chat-input');
    const charCount = document.getElementById('char-count');
    const sendBtn = document.getElementById('send-btn');
    
    // 字符计数
    chatInput.addEventListener('input', function() {
        const count = this.value.length;
        charCount.textContent = `${count}/500`;
        
        // 更新发送按钮状态
        sendBtn.disabled = count === 0;
    });
    
    // 回车发送（Shift+Enter换行）
    chatInput.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            if (!sendBtn.disabled) {
                sendMessage();
            }
        }
    });
}

// 发送消息
async function sendMessage() {
    const chatInput = document.getElementById('chat-input');
    const message = chatInput.value.trim();
    
    if (!message) return;
    
    // 添加用户消息到界面
    addMessageToChat('user', message);
    
    // 清空输入框
    chatInput.value = '';
    document.getElementById('char-count').textContent = '0/500';
    document.getElementById('send-btn').disabled = true;
    
    // 显示加载状态
    showLoading(true);
    
    try {
        // 准备请求数据
        const requestData = {
            message: message,
            knowledge_point_data: knowledgePointData,
            dialogue_history: dialogueHistory,
            dialogue_state: dialogueState,
            language: currentLanguage
        };
        
        // 发送API请求
        const response = await fetch('/chat_for_knowledge_point', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 添加AI回复到界面
            addMessageToChat('assistant', result.response);
            
            // 更新对话历史
            dialogueHistory.push({
                role: 'user',
                content: message,
                timestamp: new Date().toLocaleTimeString()
            });
            dialogueHistory.push({
                role: 'assistant',
                content: result.response,
                timestamp: new Date().toLocaleTimeString()
            });
            
            // 更新对话状态
            if (result.dialogue_state) {
                dialogueState = result.dialogue_state;
                updateStatusBar();
            }
            
            // 更新建议问题
            if (result.suggested_questions && result.suggested_questions.length > 0) {
                updateSuggestedQuestions(result.suggested_questions);
            }
            
        } else {
            showError(`AI回复失败: ${result.error}`);
        }
        
    } catch (error) {
        console.error('发送消息失败:', error);
        showError('网络错误，请稍后重试');
    } finally {
        showLoading(false);
    }
}

// 添加消息到聊天界面
function addMessageToChat(role, content) {
    const chatMessages = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${role}-message`;
    
    const currentTime = new Date().toLocaleTimeString();
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                ${role === 'assistant' ? '<span class="ai-avatar">🤖</span>' : ''}
                <span class="message-time">${currentTime}</span>
            </div>
            <div class="message-text">${content}</div>
        </div>
    `;
    
    chatMessages.appendChild(messageDiv);
    
    // 滚动到底部
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

// 更新状态栏
function updateStatusBar() {
    document.getElementById('dialogue-round').textContent = dialogueState.round || 0;
    
    const focusStatus = document.getElementById('focus-status');
    const focusStatusText = dialogueState.focus_deviation_count > 0 ? '偏离' : '正常';
    focusStatus.textContent = focusStatusText;
    focusStatus.className = `status-value ${dialogueState.focus_deviation_count > 0 ? 'focus-deviated' : 'focus-normal'}`;
    
    // 更新理解进度（这里可以根据实际逻辑计算）
    const progress = Math.min((dialogueState.round * 10), 100);
    document.getElementById('understanding-progress').style.width = `${progress}%`;
}

// 更新建议问题
function updateSuggestedQuestions(questions) {
    const suggestionsList = document.getElementById('suggestions-list');
    suggestionsList.innerHTML = '';
    
    questions.forEach(question => {
        const suggestionItem = document.createElement('div');
        suggestionItem.className = 'suggestion-item';
        suggestionItem.textContent = question;
        suggestionItem.onclick = () => askSuggestion(question);
        suggestionsList.appendChild(suggestionItem);
    });
}

// 点击建议问题
function askSuggestion(question) {
    document.getElementById('chat-input').value = question;
    document.getElementById('char-count').textContent = `${question.length}/500`;
    document.getElementById('send-btn').disabled = false;
}

// 刷新建议问题
function refreshSuggestions() {
    // 这里可以调用API获取新的建议问题
    const defaultSuggestions = [
        'What is the core concept of this knowledge point?',
        'How is this knowledge point used in real-world applications?',
        'Can you show me a specific example?',
        'What are the connections between this knowledge point and other knowledge points?'
    ];
    updateSuggestedQuestions(defaultSuggestions);
}

// 重置对话
function resetDialogue() {
    if (confirm('Are you sure you want to reset the dialogue? This will clear all conversation history.')) {
        dialogueHistory = [];
        dialogueState = {
            round: 0,
            focus_deviation_count: 0
        };
        
        // 清空聊天消息，只保留欢迎消息
        const chatMessages = document.getElementById('chat-messages');
        const welcomeMessage = chatMessages.querySelector('.ai-message');
        chatMessages.innerHTML = '';
        chatMessages.appendChild(welcomeMessage);
        
        updateStatusBar();
        refreshSuggestions();
        
        showSuccess('对话已重置');
    }
}

// 回到焦点
function backToFocus() {
    const focusMessage = `Let's get back to "${knowledgePointData.title}". Please tell me which aspect of this knowledge point you want to know.`;
    addMessageToChat('assistant', focusMessage);
    
    // 更新对话历史
    dialogueHistory.push({
        role: 'assistant',
        content: focusMessage,
        timestamp: new Date().toLocaleTimeString()
    });
    
        showSuccess('You are now back on track with the knowledge point.');
}

// 关闭知识点对话
function closeKnowledgePointChat() {
    if (confirm('Are you sure you want to close the knowledge point dialogue?')) {
        window.close();
        // 如果是在iframe中，通知父窗口
        if (window.parent !== window) {
            window.parent.postMessage({ type: 'close_knowledge_point_chat' }, '*');
        }
    }
}

// 显示加载状态
function showLoading(show) {
    const loadingOverlay = document.getElementById('loading-overlay');
    loadingOverlay.style.display = show ? 'flex' : 'none';
}

// 显示错误信息
function showError(message) {
    const errorDiv = document.createElement('div');
    errorDiv.className = 'message ai-message';
    errorDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="ai-avatar">⚠️</span>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-text" style="color: #e53e3e;">${message}</div>
        </div>
    `;
    
    document.getElementById('chat-messages').appendChild(errorDiv);
}

// 显示成功信息
function showSuccess(message) {
    const successDiv = document.createElement('div');
    successDiv.className = 'message ai-message';
    successDiv.innerHTML = `
        <div class="message-content">
            <div class="message-header">
                <span class="ai-avatar">✅</span>
                <span class="message-time">${new Date().toLocaleTimeString()}</span>
            </div>
            <div class="message-text" style="color: #38a169;">${message}</div>
        </div>
    `;
    
    document.getElementById('chat-messages').appendChild(successDiv);
}

// 更新欢迎时间
function updateWelcomeTime() {
    const welcomeTime = document.getElementById('welcome-time');
    if (welcomeTime) {
        welcomeTime.textContent = new Date().toLocaleTimeString();
    }
}

// 监听父窗口消息
window.addEventListener('message', function(event) {
    if (event.data.type === 'close_knowledge_point_chat') {
        window.close();
    }
}); 