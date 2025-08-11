#!/usr/bin/env python3
"""
测试多语言Summary生成和知识点标签提取功能
"""

import os
import sys
import json
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.summary_integrator import SummaryIntegrator
from core.knowledge_tagger import KnowledgeTagger

def test_multilingual_summary():
    """测试多语言Summary生成功能"""
    
    print("🧪 开始测试多语言Summary生成功能...")
    
    # 模拟API密钥（实际使用时需要真实的密钥）
    api_key = "your_api_key_here"  # 请替换为真实的API密钥
    
    # 初始化组件
    integrator = SummaryIntegrator(api_key)
    tagger = KnowledgeTagger()
    
    # 测试数据
    test_analysis = {
        "content_segments": [
            {
                "id": "seg_001",
                "title": "Statistical Definition of Probability",
                "description": "Introduction to the statistical definition of probability",
                "key_phrase": "probability, frequency, long-term",
                "category": "concept_definition",
                "difficulty": "基础",
                "importance": "high",
                "start_time": "00:00:00",
                "end_time": "00:05:30",
                "start_seconds": 0,
                "end_seconds": 330,
                "duration_seconds": 330
            },
            {
                "id": "seg_002", 
                "title": "Experiment and Outcome",
                "description": "Understanding experiments and their outcomes",
                "key_phrase": "experiment, outcome, sample space",
                "category": "concept_definition",
                "difficulty": "基础",
                "importance": "medium",
                "start_time": "00:05:30",
                "end_time": "00:12:15",
                "start_seconds": 330,
                "end_seconds": 735,
                "duration_seconds": 405
            },
            {
                "id": "seg_003",
                "title": "Great Law of Large Numbers",
                "description": "The law of large numbers and its applications",
                "key_phrase": "law of large numbers, convergence, probability",
                "category": "theorem",
                "difficulty": "中等",
                "importance": "high",
                "start_time": "00:12:15",
                "end_time": "00:20:00",
                "start_seconds": 735,
                "end_seconds": 1200,
                "duration_seconds": 465
            }
        ]
    }
    
    test_transcription = {
        "text": "Today we will learn about probability theory. We start with the statistical definition of probability, which relates probability to long-term frequency. Then we discuss experiments and their outcomes, including the concept of sample space. Finally, we explore the great law of large numbers, which is fundamental to understanding probability convergence."
    }
    
    lecture_title = "Introduction to Probability Theory"
    
    # 测试中文Summary生成
    print("\n📝 测试中文Summary生成...")
    try:
        chinese_result = integrator.generate_summary(
            test_analysis, 
            test_transcription, 
            lecture_title, 
            "中文"
        )
        
        if chinese_result.get('success'):
            print("✅ 中文Summary生成成功")
            print(f"📊 Summary长度: {len(chinese_result['summary'])} 字符")
            
            # 测试知识点提取
            chinese_knowledge_points = tagger.extract_knowledge_points_from_summary(
                chinese_result['summary'], 
                "中文"
            )
            print(f"🔍 提取到 {len(chinese_knowledge_points)} 个中文知识点")
            for kp in chinese_knowledge_points:
                print(f"  - {kp['name']}")
        else:
            print(f"❌ 中文Summary生成失败: {chinese_result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 中文Summary生成异常: {e}")
    
    # 测试英文Summary生成
    print("\n📝 测试英文Summary生成...")
    try:
        english_result = integrator.generate_summary(
            test_analysis, 
            test_transcription, 
            lecture_title, 
            "English"
        )
        
        if english_result.get('success'):
            print("✅ 英文Summary生成成功")
            print(f"📊 Summary长度: {len(english_result['summary'])} 字符")
            
            # 测试知识点提取
            english_knowledge_points = tagger.extract_knowledge_points_from_summary(
                english_result['summary'], 
                "English"
            )
            print(f"🔍 提取到 {len(english_knowledge_points)} 个英文知识点")
            for kp in english_knowledge_points:
                print(f"  - {kp['name']}")
        else:
            print(f"❌ 英文Summary生成失败: {english_result.get('error', '未知错误')}")
            
    except Exception as e:
        print(f"❌ 英文Summary生成异常: {e}")
    
    # 测试Prompt模板验证
    print("\n🔧 测试Prompt模板验证...")
    try:
        chinese_headers = integrator._get_language_header_structure("中文", lecture_title)
        english_headers = integrator._get_language_header_structure("English", lecture_title)
        
        print("✅ 中文文档结构:")
        print(chinese_headers)
        print("\n✅ 英文文档结构:")
        print(english_headers)
        
    except Exception as e:
        print(f"❌ Prompt模板验证异常: {e}")
    
    # 测试质量检查
    print("\n🔍 测试质量检查功能...")
    try:
        # 模拟Summary内容
        test_chinese_summary = """
## 课程总结: Introduction to Probability Theory
## **课程概览**
本课程介绍了概率论的基础概念。
## **主要知识点**
我们学习了[KP:Statistical Definition of Probability]和[KP:Experiment and Outcome]。
## **重要公式或定义**
## **关键概念解释**
"""
        
        test_english_summary = """
## Course Summary: Introduction to Probability Theory
## **Course Overview**
This course introduces fundamental concepts of probability theory.
## **Main Knowledge Points**
We learned about [KP:Statistical Definition of Probability] and [KP:Experiment and Outcome].
## **Important Formulas or Definitions**
## **Key Concept Explanations**
"""
        
        chinese_quality = integrator.validate_summary_quality(test_chinese_summary, "中文")
        english_quality = integrator.validate_summary_quality(test_english_summary, "English")
        
        print("✅ 中文质量检查结果:", chinese_quality)
        print("✅ 英文质量检查结果:", english_quality)
        
    except Exception as e:
        print(f"❌ 质量检查异常: {e}")
    
    print("\n🎉 多语言Summary测试完成!")

def test_knowledge_point_extraction():
    """测试知识点提取功能"""
    
    print("\n🧪 开始测试知识点提取功能...")
    
    tagger = KnowledgeTagger()
    
    # 测试中英文Summary中的知识点提取
    test_summaries = {
        "中文": """
## 课程总结: 概率论基础
## **课程概览**
本课程介绍了概率论的基本概念。
## **主要知识点**
我们学习了[KP:概率的统计定义]和[KP:实验与结果]。
## **重要公式或定义**
[KP:大数定律]是概率论的核心定理。
## **关键概念解释**
""",
        "English": """
## Course Summary: Probability Theory Basics
## **Course Overview**
This course introduces fundamental concepts of probability theory.
## **Main Knowledge Points**
We learned about [KP:Statistical Definition of Probability] and [KP:Experiment and Outcome].
## **Important Formulas or Definitions**
The [KP:Great Law of Large Numbers] is a core theorem in probability theory.
## **Key Concept Explanations**
"""
    }
    
    for language, summary in test_summaries.items():
        print(f"\n📝 测试{language}知识点提取...")
        try:
            knowledge_points = tagger.extract_knowledge_points_from_summary(summary, language)
            print(f"✅ 提取到 {len(knowledge_points)} 个{language}知识点:")
            for kp in knowledge_points:
                print(f"  - {kp['name']} (语言: {kp.get('language', '未知')})")
        except Exception as e:
            print(f"❌ {language}知识点提取异常: {e}")

if __name__ == "__main__":
    print("🚀 多语言Summary功能测试")
    print("=" * 50)
    
    # 测试知识点提取
    test_knowledge_point_extraction()
    
    # 测试完整Summary生成（需要API密钥）
    print("\n" + "=" * 50)
    print("⚠️  注意: 以下测试需要真实的API密钥")
    print("请将脚本中的 'your_api_key_here' 替换为真实的API密钥")
    
    # 取消注释以下行来运行完整测试
    # test_multilingual_summary()
    
    print("\n✅ 测试完成!") 