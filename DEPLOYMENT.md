# Vercel 部署指南

## 部署前准备

### 1. 环境变量配置
在Vercel中需要设置以下环境变量：
- `GEMINI_API_KEY`: 你的Google Gemini API密钥

### 2. 项目结构要求
确保以下文件存在：
- `app.py`: 主应用文件
- `vercel.json`: Vercel配置文件
- `requirements.txt`: Python依赖文件

## 部署步骤

### 方法一：通过Vercel CLI部署

1. **安装Vercel CLI**
```bash
npm install -g vercel
```

2. **登录Vercel**
```bash
vercel login
```

3. **部署项目**
```bash
vercel
```

4. **设置环境变量**
```bash
vercel env add GEMINI_API_KEY
```

### 方法二：通过GitHub部署

1. **推送代码到GitHub**
```bash
git add .
git commit -m "准备Vercel部署"
git push origin main
```

2. **在Vercel控制台导入项目**
   - 访问 [vercel.com](https://vercel.com)
   - 点击 "New Project"
   - 选择你的GitHub仓库
   - 配置环境变量

3. **设置环境变量**
   - 在项目设置中添加 `GEMINI_API_KEY`
   - 值为你的Google Gemini API密钥

## 注意事项

### 1. 文件大小限制
- Vercel有文件大小限制，大视频文件可能无法处理
- 建议添加文件大小检查

### 2. 执行时间限制
- Vercel函数有执行时间限制（默认10秒，已配置为300秒）
- 视频处理可能需要较长时间

### 3. 依赖包限制
- 某些包可能不支持Vercel环境
- 已移除本地代理设置

### 4. 静态文件
- 静态文件会自动部署
- 确保路径正确

## 故障排除

### 常见问题

1. **导入错误**
   - 检查所有依赖是否在requirements.txt中
   - 确保没有使用本地路径

2. **环境变量问题**
   - 确保在Vercel中正确设置环境变量
   - 检查变量名是否正确

3. **文件上传问题**
   - Vercel不支持大文件上传
   - 考虑使用外部存储服务

4. **执行超时**
   - 检查vercel.json中的maxDuration设置
   - 优化代码执行时间

## 部署后验证

1. 访问部署的URL
2. 测试基本功能
3. 检查日志输出
4. 验证环境变量是否正确加载
