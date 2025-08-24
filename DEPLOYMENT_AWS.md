# AWS部署指南

## 部署前准备

### 1. 环境变量配置
在AWS服务器上设置以下环境变量：
```bash
export GEMINI_API_KEY="your_gemini_api_key_here"
```

### 2. 依赖安装
```bash
pip install -r requirements.txt
```

### 3. 缓存目录创建
```bash
mkdir -p data/cache
chmod 755 data/cache
```

## 部署方式

### 方式1：直接部署
```bash
# 克隆代码
git clone https://github.com/Yolaaaaanda000/evenacademy_ai_notes.git
cd evenacademy_ai_notes
git checkout vercel-cache-only-mode

# 安装依赖
pip install -r requirements.txt

# 启动应用
python app.py
```

### 方式2：使用Docker
```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . .
RUN pip install -r requirements.txt

EXPOSE 5012
CMD ["python", "app.py"]
```

### 方式3：使用AWS Elastic Beanstalk
1. 创建 `Procfile`：
```
web: python app.py
```

2. 配置环境变量在AWS控制台

## 注意事项

### 缓存管理
- 每个部署环境有独立的缓存
- 缓存文件不会影响其他用户
- 建议定期清理缓存文件

### 性能优化
- 使用AWS RDS存储缓存数据（可选）
- 配置负载均衡器
- 设置自动扩缩容

### 安全考虑
- 使用HTTPS
- 配置防火墙规则
- 定期更新依赖包

## 监控和维护

### 日志监控
```bash
# 查看应用日志
tail -f /var/log/app.log

# 监控系统资源
htop
```

### 备份策略
- 定期备份重要数据
- 使用AWS S3存储备份
- 测试恢复流程

## 故障排除

### 常见问题
1. **端口被占用**：修改 `app.py` 中的端口号
2. **内存不足**：增加服务器内存或优化代码
3. **API限制**：配置API密钥轮换

### 联系支持
如有问题，请查看GitHub Issues或联系开发团队。
