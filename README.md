# AI Video Notes Generator

一个基于AI的智能视频笔记生成器，专注于数学教育视频的内容分析和知识点提取。
> 🎯 **独立项目**：这是一个完全独立的AI视频学习平台，专注于智能知识点提取和个性化练习推荐。

## 功能特性

- 🎥 **智能视频分析**：自动分析视频内容，提取关键知识点
- 📚 **知识点标签化**：将视频内容按数学知识点进行分类
- 🎯 **智能题目匹配**：根据知识点自动匹配相关练习题
- 💬 **AI对话辅导**：提供个性化的学习辅导和答疑
- 📊 **学习进度跟踪**：记录学习历史和掌握程度

## 项目结构

```
video-player-app/
├── app.py                 # 主应用入口
├── core/                  # 核心功能模块
│   ├── ai_dialogue_handler.py      # AI对话处理
│   ├── knowledge_point_dialogue.py # 知识点对话
│   ├── knowledge_tagger.py         # 知识点标签化
│   ├── practice_tutor_handler.py   # 练习导师处理
│   ├── prompt_manager.py           # 提示词管理
│   ├── question_matcher.py         # 题目匹配器
│   ├── summary_integrator.py       # 总结整合器
│   └── video_processor.py          # 视频处理器
├── data/                  # 数据文件
│   ├── cache/            # 缓存文件
│   ├── knowledge/        # 知识点映射
│   └── questions/        # 题库文件
├── prompts/              # 提示词模板
├── static/               # 静态资源
├── templates/            # HTML模板
└── uploads/              # 上传文件目录
```

## 安装和运行

### 1. 环境要求

- Python 3.8+
- 必要的Python包（见requirements.txt）

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置环境变量

复制 `llm.env.example` 为 `llm.env` 并配置你的API密钥：

```bash
cp llm.env.example llm.env
# 编辑 llm.env 文件，添加你的API密钥
```

### 4. 运行应用

```bash
python app.py
```

访问 http://localhost:5000 开始使用。

## 主要功能模块

### 1. 视频处理器 (video_processor.py)
- 视频文件上传和处理
- 视频内容分析和提取
- 知识点识别和标签化

### 2. 题目匹配器 (question_matcher.py)
- 基于知识点的智能题目匹配
- 支持中英文关键词识别
- 提供匹配分数和推荐排序

### 3. AI对话处理器 (ai_dialogue_handler.py)
- 智能学习辅导对话
- 个性化答疑服务
- 学习进度跟踪

### 4. 知识点标签化 (knowledge_tagger.py)
- 自动识别视频中的数学知识点
- 生成结构化的知识点标签
- 支持多种数学领域

## 数据文件说明

### mapping.csv
知识点映射文件，包含：
- `division_code`: 学科分类代码
- `Division`: 学科分类名称
- `topic_code`: 具体知识点代码
- `Topic`: 知识点描述

### 题库文件
- `pdf_test_questions.csv`: 测试题库
- `AMC10_realtest.csv`: AMC10真题库

## 开发说明

### 添加新的知识点
1. 在 `data/knowledge/mapping.csv` 中添加新的知识点映射
2. 在 `core/question_matcher.py` 中更新关键词映射
3. 测试匹配功能

### 扩展题库
1. 将新的题库文件放入 `data/questions/` 目录
2. 确保题库文件包含必要的列（Topic, Division等）
3. 更新 `core/question_matcher.py` 中的文件路径

## 技术栈

- **后端**: Python Flask
- **前端**: HTML, CSS, JavaScript
- **AI**: OpenAI API, 自定义提示词工程
- **数据处理**: Pandas, NumPy
- **视频处理**: OpenCV (可选)

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request来改进这个项目！

## 更新日志

### v1.0.0 (2024-08-11)
- 初始版本发布
- 实现基础视频分析和知识点提取
- 添加智能题目匹配功能
- 集成AI对话辅导系统 