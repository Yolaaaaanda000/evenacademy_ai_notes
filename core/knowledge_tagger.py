"""
知识点标签器 - 从Summary中提取知识点并与题库匹配
"""

import re
import json
from typing import List, Dict, Optional, Tuple
from core.question_matcher import QuestionMatcher


class KnowledgeTagger:
    """知识点标签器"""
    
    def __init__(self):
        self.question_matcher = QuestionMatcher()
        self.knowledge_points_cache = {}
        
    def extract_knowledge_points_from_summary(self, summary: str) -> List[Dict]:
        """
        从Summary中提取知识点标签
        
        Args:
            summary: 包含[KP:知识点]标签的Summary文本
            
        Returns:
            List[Dict]: 提取的知识点列表
        """
        # 正则表达式匹配 [KP:知识点] 格式
        pattern = r'\[KP:(.*?)\]'
        matches = re.findall(pattern, summary)
        
        knowledge_points = []
        for i, match in enumerate(matches):
            knowledge_point = match.strip()
            if knowledge_point:
                knowledge_points.append({
                    'id': f'kp_{i+1:03d}',
                    'name': knowledge_point,
                    'original_text': f'[KP:{knowledge_point}]',
                    'position': summary.find(f'[KP:{knowledge_point}]'),
                    'context': self._extract_context(summary, knowledge_point)
                })
        
        print(f"🔍 从Summary中提取到 {len(knowledge_points)} 个知识点:")
        for kp in knowledge_points:
            print(f"  - {kp['name']}")
        
        return knowledge_points
    
    def _extract_context(self, summary: str, knowledge_point: str) -> str:
        """提取知识点周围的上下文"""
        pattern = f'\\[KP:{re.escape(knowledge_point)}\\]'
        match = re.search(pattern, summary)
        if match:
            start = max(0, match.start() - 100)
            end = min(len(summary), match.end() + 100)
            return summary[start:end].strip()
        return ""
    
    def match_questions_for_knowledge_points(self, knowledge_points: List[Dict], 
                                           limit_per_kp: int = 3) -> Dict[str, List[Dict]]:
        """
        为每个知识点匹配相关题目
        
        Args:
            knowledge_points: 知识点列表
            limit_per_kp: 每个知识点最多匹配的题目数量
            
        Returns:
            Dict[str, List[Dict]]: 知识点到题目的映射
        """
        matches = {}
        
        for kp in knowledge_points:
            kp_name = kp['name']
            print(f"\n🎯 为知识点 '{kp_name}' 匹配题目...")
            
            # 使用QuestionMatcher匹配题目
            matched_questions = self.question_matcher.find_questions_by_topics(
                predicted_topics=[kp_name], 
                limit=limit_per_kp
            )
            
            # 如果没有直接匹配，尝试关键词匹配
            if not matched_questions:
                print(f"  ⚠️  直接匹配失败，尝试关键词匹配...")
                matched_questions = self._match_by_keywords(kp_name, limit_per_kp)
            
            matches[kp_name] = matched_questions
            print(f"  ✅ 匹配到 {len(matched_questions)} 道题目")
            
            # 显示匹配的题目
            for i, question in enumerate(matched_questions[:2]):  # 只显示前2道
                print(f"    {i+1}. {question.get('formatted_title', 'Unknown')}")
        
        return matches
    
    def _match_by_keywords(self, knowledge_point: str, limit: int) -> List[Dict]:
        """基于关键词匹配题目"""
        # 定义关键词映射
        keyword_mapping = {
            '概率': ['probability', 'prob', 'chance', 'random'],
            '统计': ['statistics', 'stat', 'data', 'distribution'],
            '组合': ['combination', 'combinatorics', 'permutation'],
            '几何': ['geometry', 'geometric', 'triangle', 'circle'],
            '代数': ['algebra', 'equation', 'polynomial'],
            '数论': ['number theory', 'divisibility', 'prime'],
            '函数': ['function', 'graph', 'domain', 'range']
        }
        
        # 查找匹配的关键词
        matched_keywords = []
        for chinese_keyword, english_keywords in keyword_mapping.items():
            if chinese_keyword in knowledge_point:
                matched_keywords.extend(english_keywords)
        
        if matched_keywords:
            return self.question_matcher.find_questions_by_topics(
                predicted_topics=matched_keywords, 
                limit=limit
            )
        
        return []
    
    def generate_knowledge_point_report(self, knowledge_points: List[Dict], 
                                      question_matches: Dict[str, List[Dict]]) -> Dict:
        """
        生成知识点匹配报告
        
        Args:
            knowledge_points: 知识点列表
            question_matches: 题目匹配结果
            
        Returns:
            Dict: 匹配报告
        """
        report = {
            'summary': {
                'total_knowledge_points': len(knowledge_points),
                'total_matched_questions': sum(len(questions) for questions in question_matches.values()),
                'average_questions_per_kp': sum(len(questions) for questions in question_matches.values()) / len(knowledge_points) if knowledge_points else 0
            },
            'knowledge_points': [],
            'question_statistics': self.question_matcher.get_question_statistics()
        }
        
        for kp in knowledge_points:
            kp_name = kp['name']
            matched_questions = question_matches.get(kp_name, [])
            
            kp_report = {
                'id': kp['id'],
                'name': kp_name,
                'context': kp['context'],
                'matched_questions_count': len(matched_questions),
                'questions': matched_questions,
                'difficulty_distribution': self._analyze_difficulty(matched_questions),
                'topic_coverage': self._analyze_topic_coverage(matched_questions)
            }
            
            report['knowledge_points'].append(kp_report)
        
        return report
    
    def _analyze_difficulty(self, questions: List[Dict]) -> Dict:
        """分析题目难度分布"""
        difficulty_counts = {}
        for question in questions:
            # 根据题目特征判断难度
            score = question.get('total_score', 0)
            if score >= 5:
                difficulty = 'hard'
            elif score >= 3:
                difficulty = 'medium'
            else:
                difficulty = 'easy'
            
            difficulty_counts[difficulty] = difficulty_counts.get(difficulty, 0) + 1
        
        return difficulty_counts
    
    def _analyze_topic_coverage(self, questions: List[Dict]) -> Dict:
        """分析题目主题覆盖"""
        topic_counts = {}
        for question in questions:
            topic = question.get('topics', '')
            if topic:
                topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        return topic_counts
    
    def create_practice_session(self, knowledge_point: str, 
                              questions: List[Dict]) -> Dict:
        """
        为指定知识点创建练习会话
        
        Args:
            knowledge_point: 知识点名称
            questions: 匹配的题目列表
            
        Returns:
            Dict: 练习会话配置
        """
        session = {
            'knowledge_point': knowledge_point,
            'total_questions': len(questions),
            'questions': [],
            'session_id': f"session_{knowledge_point}_{len(questions)}",
            'created_at': self._get_current_timestamp()
        }
        
        for i, question in enumerate(questions):
            session['questions'].append({
                'id': f"q_{i+1:03d}",
                'problem_id': question.get('Problem ID', ''),
                'title': question.get('formatted_title', ''),
                'question_text': question.get('question_text', ''),
                'topics': question.get('topics', ''),
                'difficulty': self._estimate_difficulty(question),
                'difficulty_level': question.get('difficulty_level', 3),
                'relevance_score': question.get('relevance_score', 0),
                'practice_priority': question.get('practice_priority', 5),
                'expected_match': question.get('expected_match', 'MEDIUM'),
                'recommended_order': question.get('recommended_order', 'standard'),
                # 🆕 添加缺失的关键字段
                'answer': question.get('answer', ''),
                'explanation': question.get('explanation', ''),
                'hint': question.get('hint', ''),
                # 🆕 添加选项字段
                'optionA': question.get('optionA', ''),
                'optionB': question.get('optionB', ''),
                'optionC': question.get('optionC', ''),
                'optionD': question.get('optionD', ''),
                'optionE': question.get('optionE', '')
            })
        
        return session
    
    def _estimate_difficulty(self, question: Dict) -> str:
        """估算题目难度"""
        score = question.get('total_score', 0)
        if score >= 5:
            return 'hard'
        elif score >= 3:
            return 'medium'
        else:
            return 'easy'
    
    def _get_current_timestamp(self) -> str:
        """获取当前时间戳"""
        from datetime import datetime
        return datetime.now().isoformat()
    
    def save_matching_results(self, results: Dict, filename: str = None) -> str:
        """
        保存匹配结果到文件
        
        Args:
            results: 匹配结果
            filename: 文件名（可选）
            
        Returns:
            str: 保存的文件路径
        """
        if filename is None:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"knowledge_matching_results_{timestamp}.json"
        
        filepath = f"data/results/{filename}"
        
        # 确保目录存在
        import os
        os.makedirs("data/results", exist_ok=True)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        print(f"💾 匹配结果已保存到: {filepath}")
        return filepath


# 使用示例
if __name__ == "__main__":
    # 创建知识点标签器
    tagger = KnowledgeTagger()
    
    # 示例Summary文本
    sample_summary = """
    本课程介绍了概率论的基础概念。
    
    首先讲解了[KP:概率的统计学诠释]，包括大数定律和长期运行平均值的概念。
    接着介绍了[KP:两种概率类型]，即样本概率和实验概率的区别。
    最后详细定义了[KP:实验与结果]这两个核心概念。
    """
    
    # 提取知识点
    knowledge_points = tagger.extract_knowledge_points_from_summary(sample_summary)
    
    # 匹配题目
    question_matches = tagger.match_questions_for_knowledge_points(knowledge_points)
    
    # 生成报告
    report = tagger.generate_knowledge_point_report(knowledge_points, question_matches)
    
    print("\n📊 匹配报告:")
    print(f"总知识点数: {report['summary']['total_knowledge_points']}")
    print(f"匹配题目数: {report['summary']['total_matched_questions']}")
    print(f"平均每题知识点: {report['summary']['average_questions_per_kp']:.1f}") 