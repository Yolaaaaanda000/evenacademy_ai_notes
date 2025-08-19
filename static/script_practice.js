// 练习对话框 JavaScript

// Markdown渲染配置
marked.setOptions({
    highlight: function(code, lang) {
        if (lang && hljs.getLanguage(lang)) {
            try {
                return hljs.highlight(code, { language: lang }).value;
            } catch (err) {}
        }
        return hljs.highlightAuto(code).value;
    },
    breaks: true,
    gfm: true
});

// 全局变量
let currentKnowledgePoint = '';
let currentQuestion = null;
let questionIndex = 0;
let questions = [];
// 🆕 新增：当前题目错误次数计数器
let wrongAnswerCounter = 0;

// 页面加载完成后初始化
document.addEventListener('DOMContentLoaded', function() {
    const urlParams = new URLSearchParams(window.location.search);
    currentKnowledgePoint = urlParams.get('knowledge_point') || '';
    
    if (currentKnowledgePoint) {
        initializePracticeDialog();
        loadPracticeQuestions();
    }
    bindEvents();
});

// 初始化练习对话框
function initializePracticeDialog() {
    document.getElementById('knowledge-point-title').textContent = currentKnowledgePoint;
    document.getElementById('knowledge-point-value').textContent = currentKnowledgePoint;
    document.getElementById('practice-dialog').classList.add('show');
}

// 绑定通用事件
function bindEvents() {
    const chatInput = document.getElementById('chat-input');
    if (chatInput) {
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendPracticeMessage();
            }
        });
    }
    
    const closeBtn = document.querySelector('.close-btn');
    if (closeBtn) {
        closeBtn.addEventListener('click', closePracticeDialog);
    }
}

// 关闭练习对话框
function closePracticeDialog() {
    // 🆕 修复：直接关闭当前窗口
    window.close();
}

// 加载所有练习题目
async function loadPracticeQuestions() {
    try {
        const response = await fetch(`/get_practice_session/${encodeURIComponent(currentKnowledgePoint)}?limit=5`);
        const data = await response.json();
        
        if (data.success && data.session && data.session.questions.length > 0) {
            questions = data.session.questions;
            questionIndex = 0;
            displayPracticeQuestion(questions[questionIndex]);
        } else {
            showNoQuestions();
        }
    } catch (error) {
        console.error('Failed to load questions:', error);
        showError('Failed to load questions');
    }
}

// 显示一道指定的练习题目
function displayPracticeQuestion(question) {
    if (!question) {
        finishPractice();
        return;
    }
    
    currentQuestion = question;
    // 🆕 重置当前题目的错误计数器
    wrongAnswerCounter = 0;

    const questionContent = document.getElementById('question-content');
    const difficultyElement = document.getElementById('question-difficulty');
    const relevanceElement = document.getElementById('question-relevance');
    
    const difficultyText = question.difficulty_level ? `Level ${question.difficulty_level} (${question.difficulty || 'Unknown'})` : question.difficulty || 'Unknown';
    const relevanceText = question.relevance_score ? `${Math.round(question.relevance_score)}% relevant` : question.expected_match || 'Unknown';
    
    difficultyElement.textContent = difficultyText;
    relevanceElement.textContent = relevanceText;
    
    questionContent.innerHTML = `
        <div class="question-header"><h4>${question.title || 'Question'}</h4></div>
        <div class="question-text">${question.question_text || 'Loading question content...'}</div>
        <div class="question-options">${generateOptions(question)}</div>
        <div class="question-actions">
            <button class="submit-btn" onclick="submitPracticeAnswer()">Submit Answer</button>
            <button class="next-btn" onclick="loadNextPracticeQuestion()">Skip, Next Question</button>
        </div>
    `;
    
    bindOptionEvents();
}

// 生成选项HTML
function generateOptions(question) {
    return ['A', 'B', 'C', 'D', 'E'].map(option => {
        const optionText = question[`option${option}`];
        return optionText ? `<div class="option" data-option="${option}">${option}. ${optionText}</div>` : '';
    }).join('');
}

// 绑定选项点击事件
function bindOptionEvents() {
    document.querySelectorAll('.option').forEach(option => {
        option.addEventListener('click', function() {
            document.querySelectorAll('.option').forEach(opt => opt.classList.remove('selected'));
            this.classList.add('selected');
        });
    });
}

// 🆕 提交答案 (逻辑重构)
function submitPracticeAnswer() {
    const selectedOption = document.querySelector('.option.selected');
    if (!selectedOption) {
        addPracticeChatMessage('ai', 'Please select an answer first, then submit.');
        return;
    }
    
    const selectedValue = selectedOption.dataset.option;
    addPracticeChatMessage('user', `I selected answer: ${selectedValue}`);
    analyzeAnswer(selectedValue); // 直接调用分析函数
}

// 🆕 分析答案 (核心逻辑重构)
function analyzeAnswer(selectedAnswer) {
    const isCorrect = selectedAnswer === currentQuestion.answer;
    
    if (isCorrect) {
            addPracticeChatMessage('ai', '✅ You are correct! Great job!');
        // 答对了，延迟2秒后自动进入下一题
        setTimeout(() => {
            addPracticeChatMessage('ai', 'Loading next question...');
            loadNextPracticeQuestion();
        }, 2000);
    } else {
        wrongAnswerCounter++; // 错误次数加1
        
        if (wrongAnswerCounter < 3) {
            // 第1、2次答错
            const attemptsLeft = 3 - wrongAnswerCounter;
            addPracticeChatMessage('ai', `❌ The answer is incorrect. Please think again. You have ${attemptsLeft} more attempts 😉`);
        } else {
            // 第3次答错，调用LLM获取提示
            addPracticeChatMessage('ai', '🤔 This question seems a bit challenging. Don\'t worry, I\'ll let the AI teacher give you a hint.');
            const specialPrompt = "I have answered this question incorrectly 3 times in a row. Please give me a guiding hint, but do not tell me the correct answer directly.";
            generateAIResponse(specialPrompt);
        }
    }
}

// 加载下一题 (手动点击或自动加载)
function loadNextPracticeQuestion() {
    questionIndex++;
    if (questionIndex < questions.length) {
        displayPracticeQuestion(questions[questionIndex]);
    } else {
        finishPractice();
    }
}

// 完成所有练习
function finishPractice() {
    document.getElementById('question-content').innerHTML = `
        <div class="no-questions"><h4>🎉 Congratulations on completing all questions!</h4></div>`;
    addPracticeChatMessage('ai', '📊 Practice summary:\n• Total questions: ' + questions.length + '\n• Knowledge point: ' + currentKnowledgePoint + '\n• Suggestion: Continue to strengthen related knowledge points');
}

// 发送聊天消息
function sendPracticeMessage() {
    const input = document.getElementById('chat-input');
    const message = input.value.trim();
    if (message) {
        addPracticeChatMessage('user', message);
        input.value = '';
        generateAIResponse(message);
    }
}

// 生成AI回复 (调用后端)
async function generateAIResponse(userMessage) {
    addPracticeChatMessage('ai', '🤔 Thinking...');
    const messagesContainer = document.getElementById('chat-messages');
    const loadingMessage = messagesContainer.lastElementChild; // 获取“正在思考”那条消息

    try {
        const response = await fetch('/chat_for_practice', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                knowledge_point: currentKnowledgePoint,
                question: currentQuestion,
                user_message: userMessage
            })
        });
        const data = await response.json();
        
        if (loadingMessage) messagesContainer.removeChild(loadingMessage); // 移除“正在思考”

        if (data.success) {
            addPracticeChatMessage('ai', data.llm_response);
        } else {
            addPracticeChatMessage('ai', 'Sorry, I cannot reply at the moment. Please try again later.');
        }
    } catch (error) {
        console.error('Failed to call LLM interface:', error);
        if (loadingMessage) messagesContainer.removeChild(loadingMessage); // 移除“正在思考”
        addPracticeChatMessage('ai', 'Sorry, there is a problem with the network connection. Please try again later.');
    }
}

// 通用的UI更新函数
function addPracticeChatMessage(type, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    
    // 为AI消息添加交互按钮
    const interactionButtons = type === 'ai' ? `
        <div class="message-actions">
            <button class="action-btn like-btn" onclick="likePracticeMessage(this)" title="支持">
                <span class="action-icon">▲</span>
            </button>
            <button class="action-btn dislike-btn" onclick="dislikePracticeMessage(this)" title="反对">
                <span class="action-icon">▼</span>
            </button>
            <button class="action-btn copy-btn" onclick="copyPracticeMessage(this)" title="复制">
                <span class="action-icon">📋</span>
            </button>
            <button class="action-btn refresh-btn" onclick="refreshPracticeMessage(this)" title="重新生成">
                <span class="action-icon">🔄</span>
            </button>
        </div>
    ` : '';
    
    // 对AI消息进行Markdown渲染
    const renderedContent = type === 'ai' ? marked.parse(content) : content;
    
    messageDiv.innerHTML = `
        <div class="message-content">
            <div class="message-text markdown-content">${renderedContent}</div>
            ${interactionButtons}
        </div>
    `;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showNoQuestions() {
    document.getElementById('question-content').innerHTML = `<div class="no-questions"><h4>No related questions</h4><p>There are no matching practice questions for the current knowledge point.</p></div>`;
}

function showError(message) {
    document.getElementById('question-content').innerHTML = `<div class="error"><h4>Failed to load</h4><p>${message}</p><button onclick="loadPracticeQuestions()">Retry</button></div>`;
}

// 将需要从HTML调用的函数暴露到全局
window.closePracticeDialog = closePracticeDialog;
window.sendPracticeMessage = sendPracticeMessage;
window.submitPracticeAnswer = submitPracticeAnswer;
window.loadNextPracticeQuestion = loadNextPracticeQuestion;

// 交互按钮功能函数

// 支持/点赞消息
function likePracticeMessage(button) {
    const messageDiv = button.closest('.message');
    const likeBtn = messageDiv.querySelector('.like-btn');
    const dislikeBtn = messageDiv.querySelector('.dislike-btn');
    
    // 切换点赞状态
    if (likeBtn.classList.contains('active')) {
        likeBtn.classList.remove('active');
    } else {
        likeBtn.classList.add('active');
        dislikeBtn.classList.remove('active');
    }
    
    // 这里可以添加发送反馈到后端的逻辑
    console.log('User liked the AI reply');
}

// 反对/踩消息
function dislikePracticeMessage(button) {
    const messageDiv = button.closest('.message');
    const likeBtn = messageDiv.querySelector('.like-btn');
    const dislikeBtn = messageDiv.querySelector('.dislike-btn');
    
    // 切换反对状态
    if (dislikeBtn.classList.contains('active')) {
        dislikeBtn.classList.remove('active');
    } else {
        dislikeBtn.classList.add('active');
        likeBtn.classList.remove('active');
    }
    
    // 这里可以添加发送反馈到后端的逻辑
    console.log('User disliked the AI reply');
}

// 复制消息内容
function copyPracticeMessage(button) {
    const messageDiv = button.closest('.message');
    // 获取原始文本内容，而不是HTML
    const messageText = messageDiv.querySelector('.message-text').textContent || messageDiv.querySelector('.message-text').innerText;
    
    navigator.clipboard.writeText(messageText).then(() => {
        // 显示复制成功提示
        const copyBtn = messageDiv.querySelector('.copy-btn');
        const originalIcon = copyBtn.innerHTML;
        copyBtn.innerHTML = '<span class="action-icon">✅</span>';
        copyBtn.title = 'Copied';
        
        setTimeout(() => {
            copyBtn.innerHTML = originalIcon;
            copyBtn.title = 'Copy';
        }, 2000);
        
        console.log('Message copied to clipboard');
    }).catch(err => {
        console.error('Copy failed:', err);
        alert('Copy failed, please copy manually');
    });
}

// 重新生成消息
async function refreshPracticeMessage(button) {
    const messageDiv = button.closest('.message');
    const messageText = messageDiv.querySelector('.message-text').textContent;
    
    // 显示重新生成中的状态
    const refreshBtn = messageDiv.querySelector('.refresh-btn');
    const originalIcon = refreshBtn.innerHTML;
    refreshBtn.innerHTML = '<span class="action-icon">⏳</span>';
    refreshBtn.disabled = true;
    refreshBtn.title = 'Regenerating...';
    
    try {
        // 找到对应的用户消息（通常是AI消息的前一条）
        const messages = document.querySelectorAll('.message');
        let userMessage = null;
        let userMessageIndex = -1;
        
        for (let i = 0; i < messages.length; i++) {
            if (messages[i] === messageDiv) {
                userMessageIndex = i - 1;
                break;
            }
        }
        
        if (userMessageIndex >= 0 && messages[userMessageIndex].classList.contains('user-message')) {
            userMessage = messages[userMessageIndex].querySelector('.message-text').textContent;
        }
        
        if (!userMessage) {
            throw new Error('Cannot find the corresponding user message');
        }
        
        // 准备请求数据
        const requestData = {
            knowledge_point: currentKnowledgePoint,
            question: currentQuestion,
            user_message: userMessage
        };
        
        // 发送API请求
        const response = await fetch('/chat_for_practice', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(requestData)
        });
        
        const result = await response.json();
        
        if (result.success) {
            // 更新消息内容，使用Markdown渲染
            const renderedContent = marked.parse(result.llm_response);
            messageDiv.querySelector('.message-text').innerHTML = renderedContent;
            
            console.log('Message regenerated');
        } else {
            throw new Error(result.error || 'Regeneration failed');
        }
        
    } catch (error) {
        console.error('Regeneration failed:', error);
        alert('Regeneration failed: ' + error.message);
    } finally {
        // 恢复按钮状态
        refreshBtn.innerHTML = originalIcon;
        refreshBtn.disabled = false;
        refreshBtn.title = 'Regenerate';
    }
}