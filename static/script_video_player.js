document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const videoFileInput = document.getElementById('video-file');
    const videoTitleInput = document.getElementById('video-title');
    const videoLanguageSelect = document.getElementById('video-language');
    const processVideoBtn = document.getElementById('process-video-btn');
    const uploadSection = document.getElementById('upload-section');
    const playerSection = document.getElementById('player-section');
    const processingStatus = document.getElementById('processing-status');
    const statusText = document.getElementById('status-text');

    // 视频播放器元素
    const videoPlayer = document.getElementById('video-player');
    const videoSource = document.getElementById('video-source');
    const videoTitleDisplay = document.getElementById('video-title-display');

    const fullscreenBtn = document.getElementById('fullscreen-btn');

    // 知识点面板元素
    const knowledgeList = document.getElementById('knowledge-list');
    const summaryContent = document.getElementById('summary-content');
    const autoScrollBtn = document.getElementById('auto-scroll-btn');
    const filterBtn = document.getElementById('filter-btn');

    // 底部操作按钮
    const exportNotesBtn = document.getElementById('export-notes-btn');
    const exportTimestampsBtn = document.getElementById('export-timestamps-btn');
    const shareBtn = document.getElementById('share-btn');

    // 全局变量
    let currentVideoData = null;
    let currentAnalysis = null;
    let knowledgePoints = [];
    let currentActiveItem = null;
    let autoScrollEnabled = true;
    let updateTimer = null;
    let currentSummary = null; // 添加summary变量
    
    // 🆕 在现有全局变量中添加
    let currentView = 'knowledge'; // 'knowledge' 或 'summary'
    let detailedSummary = null;
    let timestampMapping = {};

    // 🆕 初始化Summary功能
    initializeSummaryView();
    
    // 🆕 初始化页面语言显示
    updatePageLanguage();
    
    // 🆕 监听语言选择变化
    videoLanguageSelect.addEventListener('change', function() {
        updatePageLanguage();
    });

    // 视频文件上传处理
    videoFileInput.addEventListener('change', function(e) {
        const file = e.target.files[0];
        if (file) {
            // 显示视频信息输入区域
            document.getElementById('video-info').style.display = 'grid';

            // 创建视频预览
            const url = URL.createObjectURL(file);
            videoSource.src = url;
            videoPlayer.load();

            // 重置播放器区域
            playerSection.style.display = 'none';
            currentVideoData = null;
            currentAnalysis = null;
            knowledgePoints = [];
            currentSummary = null; // 重置summary
        }
    });

    // 处理视频按钮点击事件
    processVideoBtn.addEventListener('click', async function() {
        const file = videoFileInput.files[0];
        if (!file) {
            alert('Please select a video file first');
            return;
        }

        const title = videoTitleInput.value.trim() || 'Untitled Video';
        const language = videoLanguageSelect.value;

        // 显示处理状态
        uploadSection.style.display = 'none';
        processingStatus.style.display = 'block';

        // 初始化处理状态
        initializeProcessingStatus();

        try {
            // 创建FormData
            const formData = new FormData();
            formData.append('video_file', file);
            formData.append('title', title);
            formData.append('language', language);
            formData.append('output_type', 'analysis');

            // 开始处理计时
            const startTime = Date.now();
            const timeInterval = setInterval(() => {
                const elapsed = Math.floor((Date.now() - startTime) / 1000);
                document.getElementById('processing-time').textContent = `已用时: ${elapsed}秒`;
            }, 1000);

            // 模拟处理步骤进度
            simulateProcessingSteps();

            // 发送请求
            const response = await fetch('/process_video', {
                method: 'POST',
                body: formData
            });

            const result = await response.json();

            // 清除计时器
            clearInterval(timeInterval);

            if (result.success) {
                // 完成所有步骤
                completeAllSteps();

                // 保存数据
                currentVideoData = result;
                currentAnalysis = result.analysis;

                // 处理不同版本的数据结构
                if (result.processor_version === 'new' && result.integrated_summary) {
                    // 新版本：使用integrated_summary和相关数据
                    currentSummary = result.integrated_summary;
                    knowledgePoints = result.knowledge_points || [];
                } else {
                    // 旧版本：使用analysis中的数据
                    currentSummary = result.analysis?.summary || result.summary || '';
                    knowledgePoints = result.analysis?.content_segments ||
                        result.analysis?.knowledge_points || [];
                }
                
                // 🆕 修复：确保正确提取知识点数据
                console.log('接收到的数据:', result);
                console.log('analysis数据:', result.analysis);
                
                // 如果knowledgePoints为空，尝试从analysis.content_segments获取
                if (!knowledgePoints || knowledgePoints.length === 0) {
                    if (result.analysis && result.analysis.content_segments) {
                        knowledgePoints = result.analysis.content_segments;
                        console.log('从analysis.content_segments获取知识点:', knowledgePoints);
                    }
                }
                
                console.log('最终知识点数据:', knowledgePoints);
                
                // 检查并修复时间戳数据
                if (knowledgePoints && knowledgePoints.length > 0) {
                    knowledgePoints.forEach((kp, index) => {
                        // 确保时间戳数据存在
                        if (!kp.start_seconds && kp.start_time) {
                            kp.start_seconds = parseTimestampToSeconds(kp.start_time);
                        }
                        if (!kp.end_seconds && kp.end_time) {
                            kp.end_seconds = parseTimestampToSeconds(kp.end_time);
                        }
                        if (!kp.duration_seconds && kp.start_seconds && kp.end_seconds) {
                            kp.duration_seconds = kp.end_seconds - kp.start_seconds;
                        }
                        
                        console.log(`知识点 ${index}:`, {
                            title: kp.title,
                            start_time: kp.start_time,
                            start_seconds: kp.start_seconds,
                            end_time: kp.end_time,
                            end_seconds: kp.end_seconds,
                            duration_seconds: kp.duration_seconds
                        });
                    });
                }
                
                // 🆕 提取时间戳映射
                extractTimestampMappingFromData(result);

                // 使用保存的视频文件
                if (result.video_path) {
                    videoSource.src = result.video_path;
                    videoPlayer.load();
                } else {
                    // 如果没有返回video_path，继续使用之前的URL
                    console.log('继续使用现有视频源');
                }

                // 显示成功消息
                showSuccessMessage();

                // 延迟显示播放器区域
                setTimeout(() => {
                    processingStatus.style.display = 'none';
                    playerSection.style.display = 'block';

                    // 设置视频标题
                    videoTitleDisplay.textContent = title;

                    // 生成知识点列表
                    generateKnowledgePointsList();

                    // 生成摘要 - 确保显示summary
                    generateSummary(currentSummary);

                    // 初始化视频播放器事件
                    initializeVideoPlayer();
                }, 2000);
            } else {
                throw new Error(result.error || '处理失败');
            }
        } catch (error) {
            console.error('处理视频时出错:', error);
            showErrorMessage(error.message);

            // 恢复上传区域
            setTimeout(() => {
                processingStatus.style.display = 'none';
                uploadSection.style.display = 'block';
            }, 3000);
        }
    });

    // 初始化处理状态
    function initializeProcessingStatus() {
        const progressFill = document.getElementById('progress-fill');
        const statusText = document.getElementById('status-text');

        progressFill.style.width = '0%';
        statusText.textContent = '正在初始化处理流程...';

        // 重置所有步骤状态
        const steps = document.querySelectorAll('.processing-step');
        steps.forEach(step => {
            step.classList.remove('active', 'completed');
            const icon = step.querySelector('.step-icon');
            icon.className = 'step-icon pending';
        });
    }

    // 模拟处理步骤进度
    function simulateProcessingSteps() {
        const steps = [{
            step: 'transcribe',
            title: '语音转录',
            description: '正在将视频音频转换为文字...',
            duration: 3000
        }, {
            step: 'analyze',
            title: '内容分析',
            description: 'AI正在识别重要知识点和内容片段...',
            duration: 4000
        }, {
            step: 'timestamp',
            title: '精确匹配时间戳',
            description: '正在基于关键句子精确定位时间...',
            duration: 3000
        }, {
            step: 'generate',
            title: '生成笔记',
            description: '正在生成结构化笔记...',
            duration: 2000
        }, ];

        let currentStep = 0;
        const totalSteps = steps.length;

        function processNextStep() {
            if (currentStep >= totalSteps) return;

            const step = steps[currentStep];
            const stepElement = document.querySelector(`[data-step="${step.step}"]`);
            const statusText = document.getElementById('status-text');
            const progressFill = document.getElementById('progress-fill');

            // 激活当前步骤
            stepElement.classList.add('active');
            const icon = stepElement.querySelector('.step-icon');
            icon.className = 'step-icon active';

            // 更新状态文本
            statusText.textContent = step.description;

            // 更新进度条
            const progress = ((currentStep + 1) / totalSteps) * 100;
            progressFill.style.width = `${progress}%`;

            // 延迟后完成当前步骤
            setTimeout(() => {
                stepElement.classList.remove('active');
                stepElement.classList.add('completed');
                icon.className = 'step-icon completed';

                currentStep++;
                if (currentStep < totalSteps) {
                    processNextStep();
                }
            }, step.duration);
        }

        // 开始处理步骤
        setTimeout(processNextStep, 1000);
    }

    // 完成所有步骤
    function completeAllSteps() {
        const steps = document.querySelectorAll('.processing-step');
        const progressFill = document.getElementById('progress-fill');
        const statusText = document.getElementById('status-text');

        steps.forEach(step => {
            step.classList.remove('active');
            step.classList.add('completed');
            const icon = step.querySelector('.step-icon');
            icon.className = 'step-icon completed';
        });

        progressFill.style.width = '100%';
        statusText.textContent = '✅ 视频分析完成！正在准备播放器...';
    }

    // 显示成功消息
    function showSuccessMessage() {
        const statusText = document.getElementById('status-text');
        const processingTitle = document.querySelector('.processing-title');
        const processingSubtitle = document.querySelector('.processing-subtitle');

        processingTitle.textContent = '🎉 分析完成！';
        processingSubtitle.textContent = '视频内容已成功分析，正在加载播放器...';
        statusText.textContent = '✅ 所有步骤已完成，准备就绪！';
    }

    // 显示错误消息
    function showErrorMessage(error) {
        const statusText = document.getElementById('status-text');
        const processingTitle = document.querySelector('.processing-title');
        const processingSubtitle = document.querySelector('.processing-subtitle');

        processingTitle.textContent = '❌ 处理失败';
        processingSubtitle.textContent = '视频处理过程中遇到问题';
        statusText.textContent = `错误信息: ${error}`;
    }

    // 生成知识点列表
    function generateKnowledgePointsList() {
        // 获取当前选择的语言
        const currentLanguage = document.getElementById('video-language')?.value || '中文';
        const isEnglish = currentLanguage.toLowerCase() === 'english';
        
        if (!knowledgePoints || knowledgePoints.length === 0) {
            const errorText = isEnglish ? {
                title: "⚠️ No knowledge points identified",
                subtitle: "This might be because:",
                reasons: [
                    "Video content is unclear",
                    "Speech recognition quality is low", 
                    "Video content is too complex"
                ]
            } : {
                title: "⚠️ 未能识别到具体的知识点",
                subtitle: "这可能是因为：",
                reasons: [
                    "视频内容不清晰",
                    "语音识别质量较低",
                    "视频内容过于复杂"
                ]
            };
            
            knowledgeList.innerHTML = `
                <div style="text-align: center; padding: 40px; color: #666;">
                    <p>${errorText.title}</p>
                    <p>${errorText.subtitle}</p>
                    <ul style="text-align: left; margin: 20px 0;">
                        ${errorText.reasons.map(reason => `<li>${reason}</li>`).join('')}
                    </ul>
                </div>
            `;
            return;
        }

        let html = '';
        knowledgePoints.forEach((kp, index) => {
            const startTime = kp.start_time || kp.startTime || '00:00:00';
            const endTime = kp.end_time || kp.endTime || '00:00:00';
            const title = kp.title || kp.concept || kp.name || (isEnglish ? 'Unknown Segment' : '未知片段');
            const description = kp.description || '';
            const keyPhrase = kp.key_phrase || '';
            const importance = kp.importance || 'medium';
            const category = kp.category || (isEnglish ? 'Concept' : '概念');
            const difficulty = kp.difficulty || (isEnglish ? 'Basic' : '基础');
            const startSeconds = kp.start_seconds || 0;
            const endSeconds = kp.end_seconds || 0;
            const durationSeconds = kp.duration_seconds || 0;

            html += `
                <div class="knowledge-item" 
                     data-index="${index}"
                     data-start-seconds="${startSeconds}"
                     data-end-seconds="${endSeconds}"
                     data-start-time="${startTime}"
                     data-end-time="${endTime}">
                    <div class="knowledge-item-header">
                        <span class="knowledge-time">${startTime}</span>
                        <span class="knowledge-title">${title}</span>
                    </div>
                    <div class="knowledge-description">${description}</div>
                    ${keyPhrase ? `<div class="knowledge-keyphrase"><strong>${isEnglish ? 'Key Content:' : '关键内容:'}</strong> ${keyPhrase}</div>` : ''}
                    <div class="knowledge-meta">
                        <span class="importance-${importance}">${isEnglish ? 'Importance:' : '重要性:'} ${importance}</span>
                        <span>${isEnglish ? 'Category:' : '类别:'} ${category}</span>
                        <span>${isEnglish ? 'Difficulty:' : '难度:'} ${difficulty}</span>
                        <span>${isEnglish ? 'Duration:' : '时长:'} ${durationSeconds}${isEnglish ? 's' : '秒'}</span>
                    </div>
                </div>
            `;
        });

        knowledgeList.innerHTML = html;

        // 添加点击事件
        const knowledgeItems = knowledgeList.querySelectorAll('.knowledge-item');
        knowledgeItems.forEach(item => {
            item.addEventListener('click', function() {
                const index = parseInt(this.getAttribute('data-index'));
                jumpToKnowledgePoint(index);
            });
        });
    }

    // 跳转到知识点
    function jumpToKnowledgePoint(index) {
        if (index < 0 || index >= knowledgePoints.length) {
            console.error('无效的知识点索引:', index);
            return;
        }

        const kp = knowledgePoints[index];
        console.log('准备跳转到知识点:', kp);
        
        // 🆕 改进：多种方式获取开始时间
        let startSeconds = kp.start_seconds;
        
        if (!startSeconds && kp.start_time) {
            startSeconds = parseTimestampToSeconds(kp.start_time);
            console.log('从start_time解析时间:', kp.start_time, '->', startSeconds);
        }
        
        if (!startSeconds) {
            console.error('无法获取开始时间:', kp);
            return;
        }

        if (videoPlayer && videoPlayer.readyState >= 2) {
            console.log('设置视频时间:', startSeconds, '秒');
            videoPlayer.currentTime = startSeconds;
            videoPlayer.play();

            // 添加视觉反馈
            videoPlayer.style.boxShadow = '0 0 20px rgba(102, 126, 234, 0.5)';
            setTimeout(() => {
                videoPlayer.style.boxShadow = '';
            }, 2000);

            // 高亮当前知识点
            highlightKnowledgePoint(index);

            console.log('跳转到知识点:', kp.concept || kp.title, '时间:', startSeconds, '秒');
        } else {
            console.error('视频播放器未准备好, readyState:', videoPlayer?.readyState);
        }
    }

    // 高亮知识点
    function highlightKnowledgePoint(index) {
        // 移除之前的高亮
        if (currentActiveItem) {
            currentActiveItem.classList.remove('active');
        }

        // 添加新的高亮
        const knowledgeItems = knowledgeList.querySelectorAll('.knowledge-item');
        if (index >= 0 && index < knowledgeItems.length) {
            currentActiveItem = knowledgeItems[index];
            currentActiveItem.classList.add('active');

            // 自动滚动到当前项目
            if (autoScrollEnabled) {
                currentActiveItem.scrollIntoView({
                    behavior: 'smooth',
                    block: 'center'
                });
            }
        }
    }

    // 初始化视频播放器
    function initializeVideoPlayer() {
        // 视频加载完成事件
        videoPlayer.addEventListener('loadedmetadata', function() {
            console.log('视频加载完成');
        });



        // 时间更新事件
        videoPlayer.addEventListener('timeupdate', function() {
            updateActiveKnowledgePoint();
        });

        // 全屏按钮事件
        fullscreenBtn.addEventListener('click', function() {
            if (videoPlayer.requestFullscreen) {
                videoPlayer.requestFullscreen();
            } else if (videoPlayer.webkitRequestFullscreen) {
                videoPlayer.webkitRequestFullscreen();
            } else if (videoPlayer.msRequestFullscreen) {
                videoPlayer.msRequestFullscreen();
            }
        });
    }



    // 格式化时间
    function formatTime(seconds) {
        if (isNaN(seconds)) return '00:00:00';

        const hours = Math.floor(seconds / 3600);
        const minutes = Math.floor((seconds % 3600) / 60);
        const secs = Math.floor(seconds % 60);

        return `${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
    }



    // 更新当前活跃的知识点
    function updateActiveKnowledgePoint() {
        const currentTime = videoPlayer.currentTime;
        let activeIndex = -1;

        // 查找当前时间对应的知识点
        for (let i = 0; i < knowledgePoints.length; i++) {
            const kp = knowledgePoints[i];
            const startSeconds = kp.start_seconds || 0;
            const endSeconds = kp.end_seconds || 0;

            if (currentTime >= startSeconds && currentTime <= endSeconds) {
                activeIndex = i;
                break;
            }
        }

        // 如果当前时间不在任何知识点范围内，查找最近的知识点
        if (activeIndex === -1) {
            let minDistance = Infinity;
            for (let i = 0; i < knowledgePoints.length; i++) {
                const kp = knowledgePoints[i];
                const startSeconds = kp.start_seconds || 0;
                const distance = Math.abs(currentTime - startSeconds);

                if (distance < minDistance) {
                    minDistance = distance;
                    activeIndex = i;
                }
            }
        }

        highlightKnowledgePoint(activeIndex);
    }

    // 自动滚动切换
    autoScrollBtn.addEventListener('click', function() {
        autoScrollEnabled = !autoScrollEnabled;
        this.classList.toggle('active');
        this.title = autoScrollEnabled ? '自动滚动' : '手动滚动';
    });

    // 筛选功能
    filterBtn.addEventListener('click', function() {
        // 这里可以实现筛选功能，比如按重要性、类别等筛选
        alert('Filter feature is under development...');
    });

    // 导出笔记 - 修复导出功能
    exportNotesBtn.addEventListener('click', function() {
        let contentToExport = '';

        if (currentSummary) {
            contentToExport = currentSummary;
        } else if (currentVideoData && currentVideoData.content) {
            contentToExport = currentVideoData.content;
        } else if (currentVideoData && currentVideoData.notes) {
            contentToExport = currentVideoData.notes;
        } else {
            alert('No notes content available for export');
            return;
        }

        const title = videoTitleDisplay.textContent || 'video';
        downloadFile(contentToExport, `${title}_完整笔记`, '.md');
    });

    // 导出时间戳
    exportTimestampsBtn.addEventListener('click', function() {
        if (knowledgePoints && knowledgePoints.length > 0) {
            const timestamps = knowledgePoints.map((kp, index) => {
                const startTime = kp.start_time || '00:00:00';
                const concept = kp.concept || kp.title || '未知知识点';
                return `${startTime} - ${concept}`;
            }).join('\n');

            const title = videoTitleDisplay.textContent || 'video';
            downloadFile(timestamps, `${title}_时间戳`, '.txt');
        } else {
            alert('No timestamps available for export');
        }
    });

    // 分享功能
    shareBtn.addEventListener('click', function() {
        if (navigator.share) {
            navigator.share({
                title: videoTitleDisplay.textContent,
                text: '查看这个视频的知识点分析',
                url: window.location.href
            });
        } else {
            // 复制链接到剪贴板
            navigator.clipboard.writeText(window.location.href).then(() => {
                alert('Link copied to clipboard');
            });
        }
    });

    // 下载文件
    function downloadFile(content, filename, extension) {
        const formData = new FormData();
        formData.append('content', content);
        formData.append('filename', filename);
        formData.append('file_extension', extension);

        fetch('/download', {
                method: 'POST',
                body: formData
            })
            .then(response => response.blob())
            .then(blob => {
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${filename}${extension}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                document.body.removeChild(a);
            })
            .catch(error => {
                console.error('下载文件时出错:', error);
                alert('Download failed, please try again');
            });
    }

    // 简单的Markdown转HTML函数
    function convertMarkdownToHtml(markdown) {
        if (!markdown) return '';

        let html = markdown
            // 处理标题
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // 处理粗体
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            // 处理斜体
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            // 处理时间戳链接
            .replace(/\[(\d{2}:\d{2}:\d{2})(?:-\d{2}:\d{2}:\d{2})?\]/g, (match, startTime) => {
                return `<a href="#" onclick="jumpToTimestamp('${startTime}'); return false;" class="timestamp-link">${match}</a>`;
            })
            // 处理换行
            .replace(/\n/g, '<br>');

        return html;
    }

    // 解析时间戳为秒数
    function parseTimestamp(timestamp) {
        if (!timestamp || typeof timestamp !== 'string') {
            return -1;
        }

        timestamp = timestamp.trim();
        const parts = timestamp.split(':');

        if (parts.length === 3) {
            // 格式: HH:MM:SS
            const hours = parseInt(parts[0]);
            const minutes = parseInt(parts[1]);
            const seconds = parseInt(parts[2]);

            if (isNaN(hours) || isNaN(minutes) || isNaN(seconds)) {
                return -1;
            }

            return hours * 3600 + minutes * 60 + seconds;
        } else if (parts.length === 2) {
            // 格式: MM:SS
            const minutes = parseInt(parts[0]);
            const seconds = parseInt(parts[1]);

            if (isNaN(minutes) || isNaN(seconds)) {
                return -1;
            }

            return minutes * 60 + seconds;
        }

        return -1;
    }

    // 🆕 新增：解析时间戳为秒数的辅助函数
    function parseTimestampToSeconds(timestamp) {
        if (!timestamp || typeof timestamp !== 'string') {
            return 0;
        }

        timestamp = timestamp.trim();
        const parts = timestamp.split(':');

        if (parts.length === 3) {
            // 格式: HH:MM:SS
            const hours = parseInt(parts[0]);
            const minutes = parseInt(parts[1]);
            const seconds = parseInt(parts[2]);

            if (isNaN(hours) || isNaN(minutes) || isNaN(seconds)) {
                return 0;
            }

            return hours * 3600 + minutes * 60 + seconds;
        } else if (parts.length === 2) {
            // 格式: MM:SS
            const minutes = parseInt(parts[0]);
            const seconds = parseInt(parts[1]);

            if (isNaN(minutes) || isNaN(seconds)) {
                return 0;
            }

            return minutes * 60 + seconds;
        }

        return 0;
    }

    // 键盘快捷键支持
    document.addEventListener('keydown', function(e) {
        // Ctrl/Cmd + Enter 处理视频
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            e.preventDefault();
            if (!processVideoBtn.disabled) {
                processVideoBtn.click();
            }
        }

        // 空格键播放/暂停视频
        if (e.code === 'Space' && document.activeElement !== videoPlayer) {
            e.preventDefault();
            if (videoPlayer.paused) {
                videoPlayer.play();
            } else {
                videoPlayer.pause();
            }
        }

        // 左右箭头键快进/快退
        if (e.code === 'ArrowLeft') {
            e.preventDefault();
            videoPlayer.currentTime = Math.max(0, videoPlayer.currentTime - 10);
        }

        if (e.code === 'ArrowRight') {
            e.preventDefault();
            videoPlayer.currentTime = Math.min(videoPlayer.duration, videoPlayer.currentTime + 10);
        }
    });
    
    // 🆕 更新页面语言显示
    function updatePageLanguage() {
        const currentLanguage = document.getElementById('video-language')?.value || '中文';
        const isEnglish = currentLanguage.toLowerCase() === 'english';
        
        // 更新面板标题
        const panelTitle = document.getElementById('panel-title');
        if (panelTitle && currentView === 'knowledge') {
            panelTitle.textContent = isEnglish ? '🎯 Knowledge Points' : '🎯 知识点标签';
        }
        
        // 更新摘要标题
        const summaryTitle = document.getElementById('summary-title');
        if (summaryTitle) {
            summaryTitle.textContent = isEnglish ? '📋 Content Summary' : '📋 内容摘要';
        }
        
        // 更新知识点数量文本
        const conceptCountText = document.getElementById('concept-count-text');
        if (conceptCountText) {
            conceptCountText.textContent = isEnglish ? 'knowledge points' : '个知识点';
        }
        
        // 更新空摘要文本
        const emptySummaryText = document.getElementById('empty-summary-text');
        if (emptySummaryText) {
            emptySummaryText.textContent = isEnglish ? 
                '📤 Complete course summary will be displayed after video processing' : 
                '📤 处理视频后将显示完整的课程Summary';
        }
        
        // 更新按钮标题
        const autoScrollBtn = document.getElementById('auto-scroll-btn');
        if (autoScrollBtn) {
            autoScrollBtn.title = isEnglish ? 'Auto Scroll' : '自动滚动';
        }
        
        const filterBtn = document.getElementById('filter-btn');
        if (filterBtn) {
            filterBtn.title = isEnglish ? 'Filter' : '筛选';
        }
    }
    
    // 🆕 初始化Summary视图功能
    function initializeSummaryView() {
        const viewToggleBtn = document.getElementById('view-toggle-btn');
        const panelTitle = document.getElementById('panel-title');
        const knowledgeListView = document.getElementById('knowledge-list-view');
        const summaryDetailView = document.getElementById('summary-detail-view');
        
        if (!viewToggleBtn) return; // Guard against missing element

        // 获取当前语言
        function getCurrentLanguage() {
            return document.getElementById('video-language')?.value || '中文';
        }

        // 视图切换按钮事件
        viewToggleBtn.addEventListener('click', function() {
            const currentLanguage = getCurrentLanguage();
            const isEnglish = currentLanguage.toLowerCase() === 'english';
            
            if (currentView === 'knowledge') {
                // 切换到Summary视图
                currentView = 'summary';
                knowledgeListView.style.display = 'none';
                summaryDetailView.style.display = 'block';
                panelTitle.textContent = isEnglish ? '📚 Course Summary' : '📚 课程Summary';
                this.textContent = '🎯';
                this.title = isEnglish ? 'Switch to Knowledge Points View' : '切换到知识点视图';
                this.classList.add('active');
            } else {
                // 切换到知识点视图
                currentView = 'knowledge';
                knowledgeListView.style.display = 'block';
                summaryDetailView.style.display = 'none';
                panelTitle.textContent = isEnglish ? '🎯 Knowledge Points' : '🎯 知识点标签';
                this.textContent = '📚';
                this.title = isEnglish ? 'Switch to Summary View' : '切换到Summary视图';
                this.classList.remove('active');
            }
        });
    }

    // 🆕 修改现有的生成摘要函数
    function generateSummary(summary) {
        console.log('生成摘要，接收到的summary:', summary);

        // 获取当前语言
        const currentLanguage = document.getElementById('video-language')?.value || '中文';
        const isEnglish = currentLanguage.toLowerCase() === 'english';

        // 更新原有的简单摘要区域 (assuming 'summaryContent' is for a brief summary now)
        if (!summary || summary.trim() === '') {
            summaryContent.innerHTML = `
                <div style="text-align: center; padding: 20px; color: #666;">
                    <p>⚠️ ${isEnglish ? 'Unable to generate summary' : '无法生成摘要'}</p>
                </div>
            `;
            return;
        }
        
        // 保存详细Summary数据
        detailedSummary = summary;
        
        // 更新简单摘要（原有功能）
        const briefSummary = summary.substring(0, 200) + (summary.length > 200 ? '...' : '');
        summaryContent.innerHTML = `
            <p>${briefSummary}</p>
            <button class="timestamp-btn" onclick="switchToSummaryView()" style="margin-top: 10px;">
                📚 ${isEnglish ? 'View Full Summary' : '查看完整Summary'}
            </button>
        `;
        
        // 🆕 更新详细Summary视图
        updateDetailedSummaryView(summary);
        
        console.log('摘要已显示到页面');
    }

    // 🆕 更新详细Summary视图
    function updateDetailedSummaryView(summary) {
        const detailedSummaryContent = document.getElementById('detailed-summary-content');
        const conceptCountSummary = document.getElementById('concept-count-summary');
        const videoDurationSummary = document.getElementById('video-duration-summary');
        
        if (!detailedSummaryContent) return; // Guard clause

        // 获取当前语言
        const currentLanguage = document.getElementById('video-language')?.value || '中文';
        const isEnglish = currentLanguage.toLowerCase() === 'english';

        if (!summary || summary.trim() === '') {
            detailedSummaryContent.innerHTML = `
                <div class="empty-summary">
                    <p>⚠️ ${isEnglish ? 'Unable to generate detailed summary' : '无法生成详细Summary'}</p>
                </div>
            `;
            return;
        }
        
        // 更新统计信息
        if(conceptCountSummary) conceptCountSummary.textContent = knowledgePoints.length;
        if (videoPlayer && videoPlayer.duration && videoDurationSummary) {
            videoDurationSummary.textContent = formatTime(videoPlayer.duration);
        }
        
        // 将Summary转换为可交互的HTML
        const interactiveSummary = makeInteractiveSummary(summary);
        detailedSummaryContent.innerHTML = interactiveSummary;
    }

// 将Summary转换为可交互版本的【最终正确版本】
    function makeInteractiveSummary(summary) {
        // 修复 1: 添加对 summary 的有效性检查
        if (!summary) return '';

        // 修复 2: 初始化 html 变量，首先进行基础的 Markdown 转换
        let html = convertMarkdownToHtml(summary);
        
        const regex = /\[KP:(.*?)\]/g;
        
        // 在 html 变量上执行替换操作
        html = html.replace(regex, (match, conceptTitle) => {
            const trimmedTitle = conceptTitle.trim();
            const mapping = timestampMapping[trimmedTitle];
            
            // 创建可点击的知识点标签
            let clickableConcept = '';
            if (mapping) {
                clickableConcept = `<span class="clickable-concept" 
                    data-timestamp="${mapping.start_seconds || 0}" 
                    data-title="${trimmedTitle}"
                    onclick="jumpToConceptTimestamp('${trimmedTitle.replace(/'/g, "\\'")}')">
                    ${trimmedTitle}
                    <span class="timestamp-tooltip">${mapping.start_time || '00:00'}</span>
                </span>`;
            } else {
                // 如果没有映射，仅作为普通文本显示
                clickableConcept = `<span class="non-clickable-concept">${trimmedTitle}</span>`;
            }
            
            // 添加练习和对话按钮
            const practiceButton = `<button class="practice-btn" onclick="openPracticeDialog('${trimmedTitle.replace(/'/g, "\\'")}', event)" title="做题练习">📝</button>`;
            const dialogueButton = `<button class="dialogue-btn" onclick="openKnowledgePointDialogue('${trimmedTitle.replace(/'/g, "\\'")}', '${mapping ? mapping.start_time || '00:00' : '00:00'}', '${mapping ? mapping.start_seconds || 0 : 0}', event)" title="与AI对话讨论这个知识点">💬</button>`;
            
            return clickableConcept + practiceButton + dialogueButton;
        });

        // 修复 3: 返回处理后的 html 字符串
        return html;
    }

    // 将Summary转换为可交互版本的【最终正确版本】
    // function makeInteractiveSummary(summary) {
    //     if (!summary) return '';
        
    //     console.log('开始处理摘要:', summary.substring(0, 200) + '...');
    //     console.log('当前timestampMapping:', timestampMapping);
    //     console.log('timestampMapping键值:', Object.keys(timestampMapping));
        
    //     let html = convertMarkdownToHtml(summary);
        
    //     // 检查Summary中是否包含[KP:]格式的知识点
    //     const regex = /\[KP:(.*?)\]/g;
    //     const matches = [...summary.matchAll(regex)];
    //     console.log('找到的知识点标记:', matches.map(m => m[1]));
        
    //     // 如果没有找到[KP:]格式的知识点，但有timestampMapping数据，则手动添加知识点按钮
    //     if (matches.length === 0 && Object.keys(timestampMapping).length > 0) {
    //         console.log('未找到[KP:]格式，但有时间戳映射，将手动添加知识点按钮');
            
    //         // 在Summary末尾添加知识点按钮区域
    //         const knowledgePointsSection = `
    //             <div style="margin-top: 30px; padding: 20px; background: #f8f9fa; border-radius: 10px; border: 1px solid #e9ecef;">
    //                 <h3 style="margin-bottom: 15px; color: #333;">🎯 相关知识点</h3>
    //                 <div style="display: flex; flex-wrap: wrap; gap: 10px;">
    //                     ${Object.keys(timestampMapping).map(concept => {
    //                         const mapping = timestampMapping[concept];
    //                         const clickableConcept = `<span class="clickable-concept" 
    //                             data-timestamp="${mapping.start_seconds || 0}" 
    //                             data-title="${concept}"
    //                             onclick="jumpToConceptTimestamp('${concept.replace(/'/g, "\\'")}')">
    //                             ${concept}
    //                             <span class="timestamp-tooltip">${mapping.start_time || '00:00'}</span>
    //                         </span>`;
                            
    //                         const practiceButton = `<button class="practice-btn" onclick="openPracticeDialog('${concept.replace(/'/g, "\\'")}', event)" title="做题练习">
    //                             📝
    //                         </button>`;
                            
    //                         const dialogueButton = `<button class="dialogue-btn" onclick="openKnowledgePointDialogue('${concept.replace(/'/g, "\\'")}', '${mapping.start_time || '00:00'}', '${mapping.start_seconds || 0}', event)" title="与AI对话讨论这个知识点">
    //                             💬
    //                         </button>`;
                            
    //                         return `<div style="display: inline-flex; align-items: center; margin: 5px;">${clickableConcept}${practiceButton}${dialogueButton}</div>`;
    //                     }).join('')}
    //                 </div>
    //             </div>
    //         `;
            
    //         html += knowledgePointsSection;
    //     } else {
    //         // 处理[KP:]格式的知识点
    //         html = html.replace(regex, (match, conceptTitle) => {
    //             const trimmedTitle = conceptTitle.trim();
    //             const mapping = timestampMapping[trimmedTitle];
                
    //             console.log(`处理知识点: "${trimmedTitle}", 找到映射:`, mapping);
                
    //             let clickableConcept = '';
    //             let practiceButton = '';
    //             let dialogueButton = '';

    //             if (mapping) {
    //                 // 1. 创建可点击的、用于视频跳转的SPAN
    //                 clickableConcept = `<span class="clickable-concept" 
    //                             data-timestamp="${mapping.start_seconds || 0}" 
    //                             data-title="${trimmedTitle}"
    //                             onclick="jumpToConceptTimestamp('${trimmedTitle.replace(/'/g, "\\'")}')">
    //                             ${trimmedTitle}
    //                             <span class="timestamp-tooltip">${mapping.start_time || '00:00'}</span>
    //                         </span>`;
    //                 console.log(`创建可点击知识点: ${trimmedTitle}`);
    //             } else {
    //                 // 如果没有视频时间戳映射，只创建一个普通的SPAN
    //                 console.warn(`警告: 在timestampMapping中未找到概念 '${trimmedTitle}' 的映射`);
    //                 clickableConcept = `<span class="non-clickable-concept">${trimmedTitle}</span>`;
    //                 console.log(`创建不可点击知识点: ${trimmedTitle}`);
    //             }

    //             // 2. 创建用于打开练习对话框的BUTTON
    //             // 这个按钮的onclick事件只会触发练习功能
    //             practiceButton = `<button class="practice-btn" onclick="openPracticeDialog('${trimmedTitle.replace(/'/g, "\\'")}', event)" title="做题练习">
    //                                 📝
    //                             </button>`;

    //             // 3. 创建用于打开知识点对话的BUTTON
    //             // 这个按钮的onclick事件只会触发对话功能
    //             dialogueButton = `<button class="dialogue-btn" onclick="openKnowledgePointDialogue('${trimmedTitle.replace(/'/g, "\\'")}', '${mapping ? mapping.start_time || '00:00' : '00:00'}', '${mapping ? mapping.start_seconds || 0 : 0}', event)" title="与AI对话讨论这个知识点">
    //                                 💬
    //                             </button>`;

    //             const result = clickableConcept + practiceButton + dialogueButton;
    //             console.log(`生成的HTML: ${result}`);
                
    //             // 4. 将三者并列返回
    //             return result;
    //         });
    //     }
        
    //     console.log('最终生成的HTML长度:', html.length);
    //     return html;
    // }



    // 简单的Markdown转HTML函数 (确保它不会错误地处理我们的标记)
    function convertMarkdownToHtml(markdown) {
        if (!markdown) return '';

        // 这个函数只处理基本的Markdown，例如标题、粗体、换行等
        // 它现在不应该处理任何跟时间戳相关的逻辑
        let html = markdown
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
            .replace(/\*(.*?)\*/g, '<em>$1</em>')
            .replace(/\n/g, '<br>');

        return html;
    }

    // 🆕 从后端数据中提取时间戳映射
    function extractTimestampMappingFromData(data) {
        timestampMapping = {};
        
        console.log('开始提取时间戳映射，数据:', data);
        
        // 处理新版本数据结构
        if (data.timestamp_mapping) {
            timestampMapping = data.timestamp_mapping;
            console.log('使用timestamp_mapping:', timestampMapping);
        }
        // 处理从knowledge_points构建映射
        else if (data.knowledge_points && Array.isArray(data.knowledge_points)) {
            data.knowledge_points.forEach(kp => {
                const title = kp.title || kp.concept || kp.name;
                if (title) {
                    timestampMapping[title] = {
                        start_time: kp.start_time || '00:00:00',
                        end_time: kp.end_time || '00:00:00',
                        start_seconds: kp.start_seconds || 0,
                        end_seconds: kp.end_seconds || 0,
                        description: kp.description || ''
                    };
                }
            });
            console.log('从knowledge_points构建映射:', timestampMapping);
        }
        // 处理从analysis.content_segments构建映射
        else if (data.analysis && data.analysis.content_segments) {
            data.analysis.content_segments.forEach(segment => {
                const title = segment.title || segment.concept;
                if (title) {
                    timestampMapping[title] = {
                        start_time: segment.start_time || '00:00:00',
                        end_time: segment.end_time || '00:00:00',
                        start_seconds: segment.start_seconds || 0,
                        end_seconds: segment.end_seconds || 0,
                        description: segment.description || ''
                    };
                }
            });
            console.log('Build mapping from analysis.content_segments:', timestampMapping);
        }
        
        console.log('Final timestamp mapping:', timestampMapping);
        console.log('Keys in mapping:', Object.keys(timestampMapping));
    }

    // 🆕 跳转到概念对应的时间戳
    function jumpToConceptTimestamp(concept) {
        // Use encodeURIComponent/decodeURIComponent if concepts can have special characters
        const mapping = timestampMapping[concept];
        if (!mapping) {
            console.error('No timestamp mapping found for concept:', concept);
            return;
        }
        
        const startSeconds = mapping.start_seconds || 0;
        
        if (videoPlayer && videoPlayer.readyState >= 2) {
            videoPlayer.currentTime = startSeconds;
            videoPlayer.play();
            
            // 添加视觉反馈
            videoPlayer.style.boxShadow = '0 0 20px rgba(102, 126, 234, 0.5)';
            setTimeout(() => {
                videoPlayer.style.boxShadow = '';
            }, 2000);
            
            // 显示提示
            console.log(`Jump to concept: ${concept}, time: ${mapping.start_time}`);

        } else {
            console.error('Video player not ready');
        }
    }

    // 🆕 切换到Summary视图的便捷函数
    function switchToSummaryView() {
        const viewToggleBtn = document.getElementById('view-toggle-btn');
        if (currentView !== 'summary' && viewToggleBtn) {
            viewToggleBtn.click();
        }
    }

    // 🆕 切换到知识点视图的便捷函数
    function switchToKnowledgeView() {
        const viewToggleBtn = document.getElementById('view-toggle-btn');
        if (currentView !== 'knowledge' && viewToggleBtn) {
            viewToggleBtn.click();
        }
    }
    
    // 🆕 辅助函数：转义正则表达式特殊字符
    function escapeRegExp(string) {
        return string.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    }

    // 全局函数，供HTML调用
    window.jumpToKnowledgePoint = jumpToKnowledgePoint;
    window.jumpToTimestamp = function(timestamp) {
        const timeInSeconds = parseTimestamp(timestamp);
        if (timeInSeconds >= 0 && videoPlayer) {
            videoPlayer.currentTime = timeInSeconds;
            videoPlayer.play();
        }
    };

    // 🆕 全局函数供HTML调用
    // Assign all functions that need to be called from HTML to the window object.
    window.jumpToConceptTimestamp = jumpToConceptTimestamp;
    window.switchToSummaryView = switchToSummaryView;
    window.switchToKnowledgeView = switchToKnowledgeView;
    window.openPracticeDialog = openPracticeDialog; // Now this will work correctly.
    window.openKnowledgePointDialogue = openKnowledgePointDialogue; // 添加对话功能

    // 🆕 打开练习对话框 - 适中大小版本
    function openPracticeDialog(knowledgePoint, event) {
        if (event) {
            // 阻止事件冒泡，这样点击练习按钮就不会触发动机视频跳转
            event.stopPropagation();
            event.preventDefault();
        }
        
        // 🆕 计算适中大小的窗口
        const screenWidth = window.screen.availWidth;
        const screenHeight = window.screen.availHeight;
        
        // 设置窗口大小为屏幕的70%
        const windowWidth = Math.floor(screenWidth * 0.7);
        const windowHeight = Math.floor(screenHeight * 0.7);
        
        // 计算居中位置
        const left = Math.floor((screenWidth - windowWidth) / 2);
        const top = Math.floor((screenHeight - windowHeight) / 2);
        
        // 打开新窗口进行练习
        const practiceUrl = `/practice_dialog?knowledge_point=${encodeURIComponent(knowledgePoint)}`;
        const windowFeatures = `width=${windowWidth},height=${windowHeight},left=${left},top=${top},scrollbars=yes,resizable=yes,menubar=no,toolbar=no,location=no,status=no`;
        
        window.open(practiceUrl, 'practice_dialog', windowFeatures);
    }

    // 🆕 打开知识点对话窗口
    function openKnowledgePointDialogue(concept, timestamp, startSeconds, event) {
        if (event) {
            // 阻止事件冒泡，这样点击对话按钮就不会触发动机视频跳转
            event.stopPropagation();
            event.preventDefault();
        }
        
        try {
            // 获取当前视频信息
            const videoTitle = document.getElementById('video-title-display')?.textContent || '当前视频';
            
            // 构建知识点数据
            const knowledgePointData = {
                title: concept,
                content: `This is the knowledge point content about "${concept}". The knowledge point appears at the ${timestamp} time point in the video.`,
                timestamp: timestamp,
                video_title: videoTitle,
                related_concepts: concept,
                language: '中文'
            };
            
            // 计算适中大小的窗口
            const screenWidth = window.screen.availWidth;
            const screenHeight = window.screen.availHeight;
            const windowWidth = Math.floor(screenWidth * 0.7);
            const windowHeight = Math.floor(screenHeight * 0.7);
            const left = Math.floor((screenWidth - windowWidth) / 2);
            const top = Math.floor((screenHeight - windowHeight) / 2);
            
            // 打开知识点对话页面
            const url = `/knowledge_point_chat?knowledge_point=${encodeURIComponent(JSON.stringify(knowledgePointData))}`;
            const windowFeatures = `width=${windowWidth},height=${windowHeight},left=${left},top=${top},scrollbars=yes,resizable=yes,menubar=no,toolbar=no,location=no,status=no`;
            
            const newWindow = window.open(url, 'knowledge_point_dialogue', windowFeatures);
            
            if (!newWindow) {
                console.error('无法打开知识点对话窗口');
                alert('Unable to open knowledge point dialogue window, please check browser popup settings');
            }
        } catch (error) {
            console.error('Failed to open knowledge point dialogue window:', error);
            alert('Failed to open knowledge point dialogue window: ' + error.message);
        }
    }




    // 🆕 AI对话框功能 - 移到全局作用域
    window.dialogueHistory = [];
    window.isDialogueVisible = false;

    // 初始化对话框功能
    window.initDialogueSystem = function() {
        console.log('🔄 初始化对话框系统...');
        
        const toggleBtn = document.getElementById('toggle-dialogue-btn');
        const clearBtn = document.getElementById('clear-dialogue-btn');
        const sendBtn = document.getElementById('send-dialogue-btn');
        const input = document.getElementById('dialogue-input');
        const charCount = document.getElementById('char-count');
        
        console.log('找到的元素:', {
            toggleBtn: !!toggleBtn,
            clearBtn: !!clearBtn,
            sendBtn: !!sendBtn,
            input: !!input,
            charCount: !!charCount
        });
        
        if (toggleBtn) {
            toggleBtn.addEventListener('click', window.toggleDialogue);
            console.log('✅ 切换按钮事件已绑定');
        } else {
            console.error('❌ 未找到切换按钮');
        }
        
        if (clearBtn) {
            clearBtn.addEventListener('click', window.clearDialogue);
            console.log('✅ 清空按钮事件已绑定');
        }
        
        if (sendBtn) {
            sendBtn.addEventListener('click', window.sendDialogueMessage);
            console.log('✅ 发送按钮事件已绑定');
        }
        
        if (input) {
            input.addEventListener('input', window.updateCharCount);
            input.addEventListener('keypress', window.handleInputKeypress);
            console.log('✅ 输入框事件已绑定');
        }
        
        console.log('🔄 对话框系统初始化完成');
    };

    // 切换对话框显示状态
    window.toggleDialogue = function() {
        console.log('🔄 切换对话框状态...');
        
        const container = document.getElementById('dialogue-container');
        const toggleBtn = document.getElementById('toggle-dialogue-btn');
        
        console.log('找到的元素:', {
            container: !!container,
            toggleBtn: !!toggleBtn,
            currentState: window.isDialogueVisible
        });
        
        if (container) {
            window.isDialogueVisible = !window.isDialogueVisible;
            container.style.display = window.isDialogueVisible ? 'flex' : 'none';
            
            console.log('对话框状态:', window.isDialogueVisible ? '显示' : '隐藏');
            
            if (toggleBtn) {
                toggleBtn.textContent = window.isDialogueVisible ? '📝' : '💬';
                toggleBtn.title = window.isDialogueVisible ? '收起对话框' : '展开对话框';
            }
            
            if (window.isDialogueVisible) {
                container.scrollIntoView({ behavior: 'smooth' });
            }
        } else {
            console.error('❌ 未找到对话框容器');
        }
    };

    // 清空对话历史
    window.clearDialogue = function() {
        const messagesContainer = document.getElementById('dialogue-messages');
        if (messagesContainer) {
            // 保留第一条AI欢迎消息
            const welcomeMessage = messagesContainer.querySelector('.message.ai-message');
            messagesContainer.innerHTML = '';
            if (welcomeMessage) {
                messagesContainer.appendChild(welcomeMessage);
            }
        }
        
        window.dialogueHistory = [];
    };

    // 更新字符计数
    window.updateCharCount = function() {
        const input = document.getElementById('dialogue-input');
        const charCount = document.getElementById('char-count');
        const sendBtn = document.getElementById('send-dialogue-btn');
        
        if (input && charCount && sendBtn) {
            const length = input.value.length;
            charCount.textContent = `${length}/500`;
            
            // 启用/禁用发送按钮
            sendBtn.disabled = length === 0;
            
            // 字符计数颜色变化
            if (length > 450) {
                charCount.style.color = '#e53e3e';
            } else if (length > 400) {
                charCount.style.color = '#dd6b20';
            } else {
                charCount.style.color = '#6c757d';
            }
        }
    }

    // 处理输入框按键事件
    window.handleInputKeypress = function(event) {
        if (event.key === 'Enter' && !event.shiftKey) {
            event.preventDefault();
            sendDialogueMessage();
        }
    };

    // 发送对话消息
    window.sendDialogueMessage = async function() {
        const input = document.getElementById('dialogue-input');
        const sendBtn = document.getElementById('send-dialogue-btn');
        
        if (!input || !sendBtn || input.value.trim() === '') return;
        
        const message = input.value.trim();
        
        // 添加用户消息到界面
        addMessageToDialogue('user', message);
        
        // 清空输入框
        input.value = '';
        window.updateCharCount();
        
        // 禁用发送按钮，显示加载状态
        sendBtn.disabled = true;
        sendBtn.textContent = '发送中...';
        
        try {
            // 获取当前视频数据
            const videoData = getCurrentVideoData();
            
            // 发送到后端API
            const response = await fetch('/chat_for_video', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                            body: JSON.stringify({
                message: message,
                video_data: videoData,
                dialogue_history: window.dialogueHistory
            })
            });
            
            if (response.ok) {
                const data = await response.json();
                addMessageToDialogue('ai', data.response);
            } else {
                throw new Error('网络请求失败');
            }
        } catch (error) {
            console.error('发送消息失败:', error);
            addMessageToDialogue('ai', '抱歉，我遇到了一些问题。请稍后再试。');
        } finally {
            // 恢复发送按钮状态
            sendBtn.disabled = false;
            sendBtn.textContent = '发送';
        }
    };

    // 添加消息到对话框
    window.addMessageToDialogue = function(type, content) {
        const messagesContainer = document.getElementById('dialogue-messages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${type}-message`;
        
        const currentTime = new Date().toLocaleTimeString('zh-CN', {
            hour: '2-digit',
            minute: '2-digit'
        });
        
        if (type === 'user') {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-header">
                        <span class="user-avatar">👤</span>
                        <span class="message-time">${currentTime}</span>
                    </div>
                    <div class="message-text">${escapeHtml(content)}</div>
                </div>
            `;
        } else {
            messageDiv.innerHTML = `
                <div class="message-content">
                    <div class="message-header">
                        <span class="ai-avatar">🤖</span>
                        <span class="message-time">${currentTime}</span>
                    </div>
                    <div class="message-text">${formatAIResponse(content)}</div>
                </div>
            `;
        }
        
        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
        
        // 添加到历史记录
        window.dialogueHistory.push({ type, content, timestamp: new Date() });
    };

    // 快速提问功能
    window.askQuestion = function(type) {
        const questions = {
            explain: '请解释一下当前视频中的主要知识点',
            summary: '请总结一下这个视频的核心要点',
            practice: '请为这个视频内容生成一些练习题',
            review: '请提供一些复习建议'
        };
        
        const question = questions[type];
        if (question) {
            const input = document.getElementById('dialogue-input');
            if (input) {
                input.value = question;
                window.updateCharCount();
                window.sendDialogueMessage();
            }
        }
    };

    // 获取当前视频数据
    function getCurrentVideoData() {
        return {
            title: document.getElementById('video-title-display')?.textContent || '未知视频',
            current_time: getCurrentVideoTime(),
            duration: getVideoDuration(),
            knowledge_points: getKnowledgePoints(),
            summary: getVideoSummary()
        };
    }

    // 获取当前视频时间
    function getCurrentVideoTime() {
        const videoPlayer = document.getElementById('video-player');
        return videoPlayer ? videoPlayer.currentTime : 0;
    }

    // 获取视频总时长
    function getVideoDuration() {
        const videoPlayer = document.getElementById('video-player');
        return videoPlayer ? videoPlayer.duration : 0;
    }

    // 获取知识点数据
    function getKnowledgePoints() {
        const knowledgeList = document.getElementById('knowledge-list');
        if (!knowledgeList) return [];
        
        const points = [];
        const items = knowledgeList.querySelectorAll('.knowledge-item');
        items.forEach(item => {
            const title = item.querySelector('.knowledge-title')?.textContent;
            const time = item.querySelector('.knowledge-time')?.textContent;
            if (title) {
                points.push({ title, time });
            }
        });
        
        return points;
    }

    // 获取视频摘要
    function getVideoSummary() {
        const summaryContent = document.getElementById('summary-content');
        return summaryContent ? summaryContent.textContent : '';
    }

    // 格式化AI响应
    function formatAIResponse(content) {
        return content.replace(/\n/g, '<br>');
    }

    // HTML转义
    function escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    // 更新当前时间显示
    function updateCurrentTime() {
        const timeDisplay = document.getElementById('current-time-display');
        if (timeDisplay) {
            const now = new Date();
            timeDisplay.textContent = now.toLocaleTimeString('zh-CN', {
                hour: '2-digit',
                minute: '2-digit'
            });
        }
    }

    // 初始化页面状态
    console.log('视频播放器页面已加载');
    
    // 🆕 立即测试对话框元素是否存在
    console.log('🔍 检查对话框元素...');
    const testToggleBtn = document.getElementById('toggle-dialogue-btn');
    const testContainer = document.getElementById('dialogue-container');
    console.log('对话框元素检查结果:', {
        toggleBtn: !!testToggleBtn,
        container: !!testContainer
    });
    
    // 🆕 延迟初始化对话框功能，确保DOM完全加载
    setTimeout(() => {
        console.log('🔄 延迟初始化对话框...');
        if (window.initDialogueSystem) {
            window.initDialogueSystem();
        } else {
            console.error('❌ initDialogueSystem函数未定义');
        }
        updateCurrentTime();
        
        // 每分钟更新一次时间显示
        setInterval(updateCurrentTime, 60000);
    }, 1000);
});
