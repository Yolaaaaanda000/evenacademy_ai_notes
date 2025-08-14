#!/usr/bin/env python3
"""
测试知识点匹配功能
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.question_matcher import QuestionMatcher

def test_knowledge_point_matching():
    """测试知识点匹配功能"""
    
    print("🧪 开始测试知识点匹配功能...")
    
    # 创建匹配器实例
    matcher = QuestionMatcher()
    
    # 测试知识点列表
    test_knowledge_points = [
        "概率的基本概念和期望值计算",
        "几何图形的面积和周长计算",
        "代数方程的解法和多项式运算",
        "数论中的整除性和模运算",
        "计数原理和排列组合",
        "三角函数和角度计算",
        "统计数据的分析和分布",
        "复数和复平面的运算"
    ]
    
    for i, knowledge_point in enumerate(test_knowledge_points, 1):
        print(f"\n{'='*60}")
        print(f"📝 测试知识点 {i}: {knowledge_point}")
        print(f"{'='*60}")
        
        try:
            # 使用新的匹配方法
            matches = matcher.find_questions_by_knowledge_point(knowledge_point, limit=3)
            
            if matches:
                print(f"✅ 找到 {len(matches)} 道匹配题目:")
                for j, match in enumerate(matches, 1):
                    print(f"\n  {j}. 题目ID: {match.get('Problem ID', 'N/A')}")
                    print(f"     年份: {match.get('年份', 'N/A')} {match.get('竞赛类别', 'N/A')} {match.get('试卷', 'N/A')} Problem {match.get('题号', 'N/A')}")
                    print(f"     匹配分数: {match.get('match_score', 0):.1f}")
                    print(f"     相关度: {match.get('relevance_score', 0):.1f}%")
                    print(f"     匹配方法: {match.get('match_method', 'N/A')}")
                    print(f"     提取关键词: {match.get('extracted_keywords', [])}")
                    print(f"     匹配关键词: {match.get('matched_keywords', [])}")
                    print(f"     Topic: {match.get('Topic', 'N/A')}")
                    print(f"     Division: {match.get('Division', 'N/A')}")
                    print(f"     难度: {match.get('难度', 'N/A')}")
                    print(f"     题目预览: {match.get('题目', 'N/A')[:100]}...")
            else:
                print("❌ 未找到匹配的题目")
                
        except Exception as e:
            print(f"❌ 测试失败: {e}")
    
    print(f"\n{'='*60}")
    print("🎯 测试完成！")
    print(f"{'='*60}")

def test_practice_recommendations():
    """测试练习推荐功能"""
    
    print("\n🧪 开始测试练习推荐功能...")
    
    # 创建匹配器实例
    matcher = QuestionMatcher()
    
    # 测试知识点
    test_knowledge_point = "概率的基本概念和期望值计算"
    
    print(f"📝 测试知识点: {test_knowledge_point}")
    
    try:
        # 获取练习推荐
        recommendations = matcher.get_practice_recommendations(test_knowledge_point, limit=5)
        
        print(f"✅ 找到 {recommendations['total_matched']} 道匹配题目")
        print(f"📚 练习策略:\n{recommendations['practice_strategy']}")
        
        # 显示各优先级推荐
        for priority_level, questions in recommendations['recommendations'].items():
            if questions:
                print(f"\n{priority_level.upper()} 优先级 ({len(questions)}题):")
                for i, question in enumerate(questions, 1):
                    title = f"{question.get('年份', '')} {question.get('竞赛类别', '')} {question.get('试卷', '')} Problem {question.get('题号', '')}"
                    print(f"  {i}. {title} (分数: {question.get('match_score', 0):.1f})")
                    print(f"     Topic: {question.get('Topic', 'N/A')}, Division: {question.get('Division', 'N/A')}")
                    
    except Exception as e:
        print(f"❌ 测试失败: {e}")

if __name__ == "__main__":
    test_knowledge_point_matching()
    test_practice_recommendations()
