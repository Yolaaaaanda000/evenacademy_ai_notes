# Vercel 部署配置说明

## 配置要点

### 1. vercel.json 配置
- 添加了 `systemDependencies` 来安装 ffmpeg
- 配置了 `maxLambdaSize: "15mb"` 以支持更大的包
- 设置了 `includeFiles` 来包含 prompts 目录

### 2. requirements.txt 优化
移除了未使用的包：
- ❌ pymupdf (PDF处理，代码中未使用)
- ❌ python-pptx (PowerPoint处理，代码中未使用)  
- ❌ pillow (图像处理，代码中未使用)
- ❌ scikit-learn (机器学习，代码中未使用)

保留了核心功能包：
- ✅ flask (Web框架)
- ✅ google-generativeai (AI服务)
- ✅ openai-whisper (音频处理)
- ✅ ffmpeg-python (视频处理)
- ✅ pandas (数据处理)

### 3. 系统依赖
- ffmpeg: 通过 `systemDependencies` 自动安装

## 部署步骤

1. 推送代码到GitHub
2. 在Vercel控制台导入项目
3. 设置环境变量 `GEMINI_API_KEY`
4. 部署项目

## 注意事项

- 视频处理功能需要 ffmpeg，已通过系统依赖配置
- 文件大小限制：4.5MB (已添加检查)
- 执行时间限制：已配置为支持长时间处理
