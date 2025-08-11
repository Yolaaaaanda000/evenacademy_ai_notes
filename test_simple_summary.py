#!/usr/bin/env python3
"""
简单的Summary生成测试
验证修复后的功能是否正常
"""

import os
import sys
from core.summary_integrator import SummaryIntegrator

def test_summary_generation():
    """测试Summary生成功能"""
    print("🚀 开始测试Summary生成功能")
    
    # 获取API密钥
    api_key = None
    if os.path.exists('llm.env'):
        with open('llm.env', 'r') as f:
            for line in f:
                if line.startswith('GEMINI_API_KEY='):
                    api_key = line.split('=', 1)[1].strip()
                    break
    
    if not api_key:
        print("❌ 未找到API密钥")
        return False
    
    try:
        # 创建Summary整合器
        print("🔧 初始化Summary整合器...")
        integrator = SummaryIntegrator(api_key)
        
        # 模拟测试数据
        test_analysis = {
            "content_segments": [
                {
                    "id": "seg_001",
                    "title": "基础数学运算",
                    "description": "介绍基本的加减乘除运算",
                    "key_phrase": "四则运算的基本规则",
                    "category": "基础概念",
                    "difficulty": "简单",
                    "importance": "高",
                    "start_time": "00:00:00",
                    "end_time": "00:05:00",
                    "start_seconds": 0,
                    "end_seconds": 300,
                    "duration_seconds": 300
                },
                {
                    "id": "seg_002", 
                    "title": "分数概念",
                    "description": "解释分数的基本概念和表示方法",
                    "key_phrase": "分子分母的概念",
                    "category": "概念理解",
                    "difficulty": "中等",
                    "importance": "高",
                    "start_time": "00:05:00",
                    "end_time": "00:10:00",
                    "start_seconds": 300,
                    "end_seconds": 600,
                    "duration_seconds": 300
                }
            ]
        }
        
        test_transcription = {
            "text": "这是一个关于基础数学概念的课程，包括加法、减法、乘法和除法。"
        }
        
        lecture_title = "数学基础课程"
        language = "中文"
        
        print("📝 开始生成Summary...")
        result = integrator.generate_summary(
            analysis=test_analysis,
            transcription=test_transcription,
            lecture_title=lecture_title,
            language=language
        )
        
        print(f"📊 生成结果: {result['success']}")
        
        if result['success']:
            print("✅ Summary生成成功!")
            print(f"📄 Summary长度: {len(result['summary'])} 字符")
            print(f"📄 Summary前200字符: {result['summary'][:200]}...")
            print(f"📊 知识点数量: {len(result['knowledge_points'])}")
            return True
        else:
            print("❌ Summary生成失败!")
            print(f"📄 错误信息: {result.get('error', '未知错误')}")
            return False
            
    except Exception as e:
        print(f"❌ 测试异常: {e}")
        return False

if __name__ == "__main__":
    success = test_summary_generation()
    if success:
        print("\n🎉 测试通过！Summary生成功能正常")
    else:
        print("\n⚠️ 测试失败，请检查配置")
        sys.exit(1) 