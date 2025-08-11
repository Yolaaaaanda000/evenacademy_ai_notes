// 练习对话框 JavaScript

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
        console.error('加载题目失败:', error);
        showError('加载题目失败');
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
    
    const difficultyText = question.difficulty_level ? `Level ${question.difficulty_level} (${question.difficulty || '未知'})` : question.difficulty || '未知';
    const relevanceText = question.relevance_score ? `${Math.round(question.relevance_score)}% 相关` : question.expected_match || '未知';
    
    difficultyElement.textContent = difficultyText;
    relevanceElement.textContent = relevanceText;
    
    questionContent.innerHTML = `
        <div class="question-header"><h4>${question.title || '题目'}</h4></div>
        <div class="question-text">${question.question_text || '题目内容加载中...'}</div>
        <div class="question-options">${generateOptions(question)}</div>
        <div class="question-actions">
            <button class="submit-btn" onclick="submitPracticeAnswer()">提交答案</button>
            <button class="next-btn" onclick="loadNextPracticeQuestion()">跳过，下一题</button>
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
        addPracticeChatMessage('ai', '请先选择一个答案，然后再提交哦。');
        return;
    }
    
    const selectedValue = selectedOption.dataset.option;
    addPracticeChatMessage('user', `我选择了答案: ${selectedValue}`);
    analyzeAnswer(selectedValue); // 直接调用分析函数
}

// 🆕 分析答案 (核心逻辑重构)
function analyzeAnswer(selectedAnswer) {
    const isCorrect = selectedAnswer === currentQuestion.answer;
    
    if (isCorrect) {
        addPracticeChatMessage('ai', '✅ 回答正确！非常棒！');
        // 答对了，延迟2秒后自动进入下一题
        setTimeout(() => {
            addPracticeChatMessage('ai', '正在为你加载下一题...');
            loadNextPracticeQuestion();
        }, 2000);
    } else {
        wrongAnswerCounter++; // 错误次数加1
        
        if (wrongAnswerCounter < 3) {
            // 第1、2次答错
            const attemptsLeft = 3 - wrongAnswerCounter;
            addPracticeChatMessage('ai', `❌ 答案不正确，请再思考一下哦。你还有 ${attemptsLeft} 次机会😉`);
        } else {
            // 第3次答错，调用LLM获取提示
            addPracticeChatMessage('ai', '🤔 看来这道题有点难度，别担心，我让AI老师来给你一个提示。');
            const specialPrompt = "我在这道题上已经连续答错了3次，请给我一个引导性的提示，但不要直接告诉我正确答案是什么。";
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
        <div class="no-questions"><h4>🎉 恭喜你完成了所有题目！</h4></div>`;
    addPracticeChatMessage('ai', '📊 练习总结：\n• 总题数：' + questions.length + '\n• 知识点：' + currentKnowledgePoint + '\n• 建议：继续巩固相关知识点');
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
    addPracticeChatMessage('ai', '🤔 正在思考中...');
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
            addPracticeChatMessage('ai', '抱歉，我暂时无法回复，请稍后再试。');
        }
    } catch (error) {
        console.error('调用LLM接口失败:', error);
        if (loadingMessage) messagesContainer.removeChild(loadingMessage); // 移除“正在思考”
        addPracticeChatMessage('ai', '抱歉，网络连接出现问题，请稍后再试。');
    }
}

// 通用的UI更新函数
function addPracticeChatMessage(type, content) {
    const messagesContainer = document.getElementById('chat-messages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `message ${type}-message`;
    messageDiv.innerHTML = `<div class="message-content">${content.replace(/\n/g, '<br>')}</div>`;
    messagesContainer.appendChild(messageDiv);
    messagesContainer.scrollTop = messagesContainer.scrollHeight;
}

function showNoQuestions() {
    document.getElementById('question-content').innerHTML = `<div class="no-questions"><h4>暂无相关题目</h4><p>当前知识点暂时没有匹配的练习题。</p></div>`;
}

function showError(message) {
    document.getElementById('question-content').innerHTML = `<div class="error"><h4>加载失败</h4><p>${message}</p><button onclick="loadPracticeQuestions()">重试</button></div>`;
}

// 将需要从HTML调用的函数暴露到全局
window.closePracticeDialog = closePracticeDialog;
window.sendPracticeMessage = sendPracticeMessage;
window.submitPracticeAnswer = submitPracticeAnswer;
window.loadNextPracticeQuestion = loadNextPracticeQuestion;