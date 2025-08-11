#!/usr/bin/env python3
"""
Google Gemini API 连通性测试脚本
用于排查API配置和网络连接问题
"""

import os
import json
import requests
import google.generativeai as genai
from datetime import datetime

def test_api_key_from_env():
    """从环境变量测试API密钥"""
    print("🔍 步骤1: 检查环境变量中的API密钥")
    
    # 检查llm.env文件
    if os.path.exists('llm.env'):
        print("📁 发现llm.env文件")
        with open('llm.env', 'r') as f:
            content = f.read()
            print(f"📄 llm.env内容: {content.strip()}")
            
            # 提取API密钥
            for line in content.split('\n'):
                if line.startswith('GEMINI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    print(f"🔑 从llm.env提取的API密钥: {api_key[:10]}...{api_key[-4:]}")
                    return api_key
    
    # 检查环境变量
    api_key = os.getenv('GEMINI_API_KEY')
    if api_key:
        print(f"🔑 从环境变量获取的API密钥: {api_key[:10]}...{api_key[-4:]}")
        return api_key
    
    print("❌ 未找到API密钥")
    return None

def test_curl_api(api_key):
    """使用curl命令测试API"""
    print("\n🔍 步骤2: 使用curl测试API连通性")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
    
    headers = {
        "Content-Type": "application/json"
    }
    
    data = {
        "contents": [{
            "parts": [{
                "text": "你好，请简单回复'测试成功'"
            }]
        }]
    }
    
    try:
        print(f"🌐 请求URL: {url}")
        print(f"📤 请求数据: {json.dumps(data, ensure_ascii=False, indent=2)}")
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        print(f"📊 HTTP状态码: {response.status_code}")
        print(f"📋 响应头: {dict(response.headers)}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ curl测试成功!")
            print(f"📄 响应内容: {json.dumps(response_data, ensure_ascii=False, indent=2)}")
            return True
        else:
            print(f"❌ curl测试失败!")
            print(f"📄 错误响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ curl测试异常: {e}")
        return False

def test_python_sdk(api_key):
    """使用Python SDK测试API"""
    print("\n🔍 步骤3: 使用Python SDK测试API")
    
    try:
        # 配置API密钥
        genai.configure(api_key=api_key)
        print("✅ API密钥配置成功")
        
        # 创建模型实例
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        print("✅ 模型实例创建成功")
        
        # 简单测试
        prompt = "你好，请简单回复'Python SDK测试成功'"
        print(f"📝 测试Prompt: {prompt}")
        
        response = model.generate_content(prompt)
        print(f"✅ Python SDK调用成功!")
        print(f"📄 响应类型: {type(response)}")
        print(f"📄 响应内容: {response.text}")
        
        # 检查响应属性
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            print(f"🔍 候选属性: {list(candidate.__dict__.keys())}")
            if hasattr(candidate, 'finish_reason'):
                print(f"🔍 finish_reason: {candidate.finish_reason}")
        
        return True
        
    except Exception as e:
        print(f"❌ Python SDK测试失败: {e}")
        print(f"🔍 异常类型: {type(e).__name__}")
        return False

def test_simple_summary_prompt(api_key):
    """测试简单的Summary生成"""
    print("\n🔍 步骤4: 测试简单的Summary生成")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # 创建一个非常简单的测试Prompt
        simple_prompt = """
请为以下内容生成一个简单的总结：

课程标题：数学基础
内容：这是一个关于基础数学概念的课程，包括加法、减法、乘法和除法。

请用中文生成一个简短的课程总结。
"""
        
        print(f"📝 简单Prompt长度: {len(simple_prompt)} 字符")
        print(f"📝 Prompt内容: {simple_prompt[:100]}...")
        
        response = model.generate_content(simple_prompt)
        
        print(f"✅ 简单Summary测试成功!")
        print(f"📄 响应内容: {response.text}")
        
        return True
        
    except Exception as e:
        print(f"❌ 简单Summary测试失败: {e}")
        return False

def test_complex_summary_prompt(api_key):
    """测试复杂的Summary生成（模拟实际使用场景）"""
    print("\n🔍 步骤5: 测试复杂的Summary生成")
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('models/gemini-1.5-flash')
        
        # 模拟实际的分段内容
        segments_content = """
## 📚 知识点标题列表
以下是在视频中识别出的主要知识点标题，请在Summary中适当引用：
1. **基础数学运算**
2. **分数概念**
3. **小数运算**

## 📖 详细分段内容

### 分段 1: 基础数学运算
- **时间范围**: 00:00:00 - 00:05:00
- **类别**: 基础概念
- **难度**: 简单
- **重要性**: 高
- **内容描述**: 介绍基本的加减乘除运算
- **关键信息**: 四则运算的基本规则

### 分段 2: 分数概念
- **时间范围**: 00:05:00 - 00:10:00
- **类别**: 概念理解
- **难度**: 中等
- **重要性**: 高
- **内容描述**: 解释分数的基本概念和表示方法
- **关键信息**: 分子分母的概念
"""
        
        complex_prompt = f"""
你是一位专业的教育内容编辑。请基于以下视频分段内容，生成一个完整的、高可读性的课程总结文档。

## 语言要求：
- 输出语言：中文
- 保持整个文档语言一致

## 必需格式（严格按照以下结构）：

## 课程总结：数学基础课程

## **课程概述**
[提供2-3句话概括整个课程的主要内容和目标]

## **主要知识点**
[按逻辑顺序组织知识点]

## **重要公式或定义**
[列出所有重要公式和定义]

## **关键概念解释**
[提供重要概念的深入解释]

## 分段内容数据：
{segments_content}

## 生成要求：
1. 保持学术和专业语调，但语言要清晰易懂
2. 内容应连贯流畅，按知识点的逻辑关系组织
3. 重要公式必须完整准确，使用标准数学符号
4. 概念解释应深入但易于学习者理解
5. 避免重复内容，确保信息完整一致

请生成完整的总结文档：
"""
        
        print(f"📝 复杂Prompt长度: {len(complex_prompt)} 字符")
        print(f"📝 Prompt前200字符: {complex_prompt[:200]}...")
        
        response = model.generate_content(complex_prompt)
        
        print(f"✅ 复杂Summary测试成功!")
        print(f"📄 响应内容: {response.text[:500]}...")
        
        return True
        
    except Exception as e:
        print(f"❌ 复杂Summary测试失败: {e}")
        print(f"🔍 异常详情: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("🚀 开始Google Gemini API连通性测试")
    print("=" * 60)
    
    # 获取API密钥
    api_key = test_api_key_from_env()
    if not api_key:
        print("❌ 无法获取API密钥，测试终止")
        return
    
    # 执行测试
    tests = [
        ("curl API测试", lambda: test_curl_api(api_key)),
        ("Python SDK测试", lambda: test_python_sdk(api_key)),
        ("简单Summary测试", lambda: test_simple_summary_prompt(api_key)),
        ("复杂Summary测试", lambda: test_complex_summary_prompt(api_key))
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n{'='*20} {test_name} {'='*20}")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} 执行异常: {e}")
            results.append((test_name, False))
    
    # 输出测试结果总结
    print("\n" + "=" * 60)
    print("📊 测试结果总结")
    print("=" * 60)
    
    for test_name, result in results:
        status = "✅ 通过" if result else "❌ 失败"
        print(f"{test_name}: {status}")
    
    success_count = sum(1 for _, result in results if result)
    print(f"\n总体结果: {success_count}/{len(results)} 个测试通过")
    
    if success_count == len(results):
        print("🎉 所有测试通过！API配置正常")
    else:
        print("⚠️ 部分测试失败，请检查API配置")

if __name__ == "__main__":
    main() 