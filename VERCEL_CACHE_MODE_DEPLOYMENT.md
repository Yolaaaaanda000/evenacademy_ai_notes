# Vercel缓存模式部署指南

## 概述

本项目已配置为缓存模式，专门用于Vercel部署。在此模式下，系统会跳过视频处理步骤，直接使用预处理的缓存数据生成Summary。

## 部署前准备

### 1. 确保缓存文件存在
在 `data/cache/` 目录中应该有预处理的分析缓存文件：
- `*_analysis.json` 文件（包含转录和分析数据）

### 2. 环境变量配置
在Vercel中设置以下环境变量：
- `GEMINI_API_KEY`: Google Gemini API密钥

## 部署配置

### 缓存模式开关
在 `app.py` 中：
```python
CACHE_ONLY_MODE = True  # 设置为True启用缓存模式
VERCEL_DEPLOYMENT = True  # Vercel部署标志
```

### 排除的文件
`.vercelignore` 文件已配置排除：
- 大文件（AMC10_realtest.csv等）
- 测试视频文件
- 开发文件

### 保留的文件
- `data/cache/*_analysis.json` - 必需的缓存文件
- `prompts/` - Prompt模板文件
- 核心代码文件

## 功能说明

### 缓存模式特性
1. **跳过视频处理**: 不进行whisper转录和ffmpeg处理
2. **使用预处理数据**: 直接加载缓存的分析结果
3. **保留LLM功能**: 继续使用Gemini生成Summary
4. **快速响应**: 避免耗时的视频处理步骤

### 支持的功能
- ✅ 视频内容分析
- ✅ 知识点提取
- ✅ LLM对话
- ✅ 练习功能
- ✅ Summary生成

### 限制的功能
- ❌ 新视频上传处理
- ❌ 实时视频转录
- ❌ 视频文件处理

## 部署步骤

1. **推送代码到GitHub**
   ```bash
   git add .
   git commit -m "Add cache-only mode for Vercel deployment"
   git push origin vercel-cache-only-mode
   ```

2. **在Vercel中部署**
   - 连接GitHub仓库
   - 选择 `vercel-cache-only-mode` 分支
   - 配置环境变量
   - 部署

3. **验证部署**
   - 访问部署的URL
   - 测试视频处理功能（应该使用缓存数据）
   - 检查LLM对话功能

## 故障排除

### 常见问题

1. **"未找到可用的缓存文件"**
   - 确保 `data/cache/` 目录中有 `*_analysis.json` 文件
   - 检查文件权限

2. **"data is too long"错误**
   - 检查是否还有大文件被包含
   - 确认 `.vercelignore` 配置正确

3. **API调用失败**
   - 检查 `GEMINI_API_KEY` 环境变量
   - 确认API配额充足

### 调试模式
如需调试，可以临时设置：
```python
CACHE_ONLY_MODE = False  # 临时禁用缓存模式
```

## 性能优化

### 缓存文件优化
- 定期清理不需要的缓存文件
- 压缩缓存文件大小
- 使用CDN加速缓存访问

### 代码优化
- 移除不必要的依赖
- 优化导入语句
- 减少内存使用

## 维护说明

### 更新缓存数据
如需更新缓存数据，需要：
1. 在本地开发环境处理新视频
2. 生成新的缓存文件
3. 更新部署的缓存文件

### 版本管理
- 缓存文件版本：`cache_version: "1.0"`
- 处理器版本：`processor_version: "cache_only"`
- 处理模式：`processing_mode: "cache_only"`

## 联系信息

如有问题，请检查：
1. 部署日志
2. 缓存文件完整性
3. 环境变量配置
4. API密钥有效性
