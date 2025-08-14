"""
题目匹配器 - 根据知识点标签匹配相关题目
"""

import pandas as pd
import os
import re
from typing import List, Dict, Optional

# ---------------- VVVV NEW CSVMatcher Class VVVV ----------------

class CSVMatcher:
    """
    CSV题库匹配器 - [V2 - 数据驱动版本]
    在初始化时从 mapping.csv 动态加载知识点和关键词。
    """
    
    def __init__(self, mapping_filepath='data/knowledge/mapping.csv'):
        self.questions_cache = None
        # 🆕 新增：扩展的关键词映射
        self.extended_keyword_mapping = self._create_extended_keyword_mapping()
        # 加载知识点关键词映射
        self.topic_keywords = self._load_topic_keywords_from_csv(mapping_filepath)

    def _create_extended_keyword_mapping(self) -> Dict[str, List[str]]:
        """
        🆕 创建扩展的关键词映射，包含更多中英文关键词
        """
        return {
            # 概率相关
            'prob': ['probability', 'prob', 'chance', 'random', 'likely', 'unlikely', 'odds', '概率', '随机', '可能性', '期望', '期望值'],
            'Expectation': ['expectation', 'expected value', 'mean', '期望', '期望值', '平均值', '数学期望'],
            
            # 几何相关
            'geom': ['geometry', 'geometric', 'triangle', 'circle', 'area', 'perimeter', 'volume', '几何', '图形', '面积', '周长', '体积', '三角形', '圆形', '正方形', '矩形'],
            'area': ['area', 'surface', 'square', 'rectangle', '面积', '表面积', '平方', '矩形'],
            'circle': ['circle', 'circumference', 'radius', 'diameter', 'arc', '圆', '圆周', '半径', '直径', '弧'],
            'angle': ['angle', 'degree', 'radian', 'trigonometry', '角', '角度', '弧度', '三角函数'],
            'sim': ['similar', 'similarity', 'proportion', 'ratio', '相似', '比例', '相似性'],
            'length': ['length', 'distance', 'perimeter', '长度', '距离', '周长'],
            '3d': ['3d', 'three dimensional', 'volume', 'solid', '三维', '体积', '立体'],
            'coor': ['coordinate', 'coordinate geometry', 'graph', '坐标', '坐标系', '图形'],
            
            # 代数相关
            'misa': ['miscellaneous algebra', 'algebra', 'algebraic', '代数', '代数运算'],
            'complex': ['complex', 'imaginary', 'real', 'plane', '复数', '虚数', '实数', '复平面'],
            'function': ['function', 'functional', 'equation', '函数', '方程', 'f(x)', 'y='],
            'equation': ['equation', 'inequality', 'solve', 'solution', '方程', '不等式', '解', '求解'],
            'poly': ['polynomial', 'degree', 'coefficient', '多项式', '次数', '系数'],
            'seq': ['sequence', 'series', 'arithmetic', 'geometric', '数列', '级数', '等差数列', '等比数列'],
            'log': ['logarithm', 'log', 'exponential', '对数', '指数', '对数函数'],
            'exp': ['exponent', 'exponential', 'power', '指数', '幂', '指数函数'],
            'trig': ['trigonometry', 'sine', 'cosine', 'tangent', '三角', '三角函数', '正弦', '余弦', '正切'],
            'stats': ['statistics', 'stat', 'data', 'distribution', '统计', '数据', '分布', '均值', '中位数'],
            
            # 数论相关
            'div': ['divisibility', 'divisible', 'factor', 'multiple', '整除', '整除性', '倍数', '因数'],
            'mod': ['modular', 'modulo', 'remainder', 'congruent', '模', '模运算', '同余', '余数'],
            'factor': ['factor', 'divisor', 'prime', 'composite', '因数', '因子', '质数', '合数'],
            'base': ['base', 'representation', 'number system', '进制', '表示', '数制'],
            'lcm': ['lcm', 'least common multiple', 'multiple', '最小公倍数', '公倍数'],
            'digit': ['digit', 'number', 'representation', '数字', '数位', '表示'],
            
            # 计数相关
            'count': ['counting', 'combinatorics', 'permutation', 'combination', '计数', '排列', '组合', '组合数学'],
            'set': ['set', 'set theory', 'element', 'subset', 'union', 'intersection', 'complement', '集合', '集合论', '元素', '子集', '并集', '交集', '补集'],
            'Markov': ['markov', 'chain', 'probability', 'state', '马尔可夫', '链', '状态'],
            'Recursion': ['recursion', 'recursive', 'recurrence', '递归', '递推', '递推关系'],
            'logic': ['logic', 'logical', 'boolean', '逻辑', '布尔', '逻辑运算'],
            'uniform': ['uniform', 'distribution', 'probability', '均匀', '分布', '均匀分布'],
            'game': ['game', 'strategy', 'winning', '游戏', '策略', '获胜'],
        }

    def _load_topic_keywords_from_csv(self, filepath: str) -> Dict[str, List[str]]:
        """
        NEW: 从mapping.csv文件加载并解析主题关键词。
        返回一个字典，键是Topic代码(如'prob', 'geom'),值是关键词列表。
        """
        try:
            mapping_df = pd.read_csv(filepath)
            topic_dict = {}
            for _, row in mapping_df.iterrows():
                # 使用 'topic_code' 列作为键, 例如 'prob', 'geom'
                topic_code = row['topic_code']
                # 使用 'Topic' 列作为关键词描述
                topic_description = row.get('Topic', '')
                if pd.notna(topic_code) and pd.notna(topic_description):
                    # 将主题描述作为关键词，并添加扩展的关键词
                    keywords = [topic_description.lower()]
                    
                    # 添加扩展的关键词映射
                    if topic_code in self.extended_keyword_mapping:
                        keywords.extend(self.extended_keyword_mapping[topic_code])
                    
                    topic_dict[topic_code] = keywords
            print(f"✅ 成功从 {filepath} 加载 {len(topic_dict)} 个知识点关键词。")
            return topic_dict
        except FileNotFoundError:
            print(f"❌ 错误: 映射文件 {filepath} 未找到。")
            return {}
        except Exception as e:
            print(f"❌ 解析映射文件时出错: {e}")
            return {}

    def match_by_knowledge_point_keywords(self, knowledge_point: str, questions_data: List[Dict]) -> List[Dict]:
        """
        🆕 新增：基于知识点关键词的直接匹配方法
        从知识点文本中提取关键词，直接与题目的topic进行匹配
        """
        # 1. 从知识点文本中提取关键词
        extracted_keywords = self._extract_keywords_from_knowledge_point(knowledge_point)
        
        if not extracted_keywords:
            print(f"⚠️ 对于知识点 '{knowledge_point[:30]}...'，未能提取出任何关键词。")
            return []

        print(f"🔍 从知识点提取的关键词: {extracted_keywords}")

        # 2. 匹配题目
        matches = []
        for question in questions_data:
            question_topic = str(question.get('Topic', '')).lower()
            question_division = str(question.get('Division', '')).lower()
            question_text = str(question.get('题目', ''))
            
            # 计算匹配分数
            match_score = self._calculate_keyword_match_score(extracted_keywords, question_topic, question_division, question_text)
            
            if match_score > 0:
                question_with_score = question.copy()
                question_with_score['match_score'] = match_score
                question_with_score['extracted_keywords'] = extracted_keywords
                question_with_score['matched_keywords'] = self._get_matched_keywords(extracted_keywords, question_topic, question_division, question_text)
                matches.append(question_with_score)
        
        # 按匹配分数排序
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches

    def _extract_keywords_from_knowledge_point(self, knowledge_point: str) -> List[str]:
        """
        🆕 从知识点文本中提取关键词
        """
        kp_lower = knowledge_point.lower()
        extracted_keywords = []
        
        # 1. 直接匹配topic_code
        for topic_code, keywords in self.topic_keywords.items():
            for keyword in keywords:
                if keyword.lower() in kp_lower:
                    extracted_keywords.append(topic_code)
                    break
        
        # 2. 提取中文关键词
        chinese_keywords = self._extract_chinese_keywords(kp_lower)
        extracted_keywords.extend(chinese_keywords)
        
        # 3. 提取英文关键词
        english_keywords = self._extract_english_keywords(kp_lower)
        extracted_keywords.extend(english_keywords)
        
        # 去重并返回
        return list(set(extracted_keywords))

    def _extract_chinese_keywords(self, text: str) -> List[str]:
        """
        🆕 提取中文关键词
        """
        chinese_keywords = []
        
        # 定义中文关键词列表
        chinese_keyword_list = [
            '概率', '随机', '期望', '统计', '数据', '分布',
            '几何', '图形', '面积', '周长', '体积', '三角形', '圆形', '正方形', '矩形',
            '代数', '函数', '方程', '不等式', '多项式', '数列', '对数', '指数',
            '数论', '整除', '模运算', '因数', '质数', '合数', '进制', '数字',
            '计数', '排列', '组合', '递归', '逻辑', '游戏', '策略',
            '集合', '集合论', '元素', '子集', '并集', '交集', '补集'
        ]
        
        for keyword in chinese_keyword_list:
            if keyword in text:
                chinese_keywords.append(keyword)
        
        return chinese_keywords

    def _extract_english_keywords(self, text: str) -> List[str]:
        """
        🆕 提取英文关键词
        """
        english_keywords = []
        
        # 定义英文关键词列表
        english_keyword_list = [
            'probability', 'random', 'expectation', 'statistics', 'data', 'distribution',
            'geometry', 'triangle', 'circle', 'area', 'perimeter', 'volume',
            'algebra', 'function', 'equation', 'polynomial', 'sequence', 'logarithm', 'exponent',
            'divisibility', 'modulo', 'factor', 'prime', 'composite', 'base', 'digit',
            'counting', 'permutation', 'combination', 'recursion', 'logic', 'game', 'strategy',
            'set', 'set theory', 'element', 'subset', 'union', 'intersection', 'complement'
        ]
        
        for keyword in english_keyword_list:
            if keyword in text:
                english_keywords.append(keyword)
        
        return english_keywords

    def _calculate_keyword_match_score(self, extracted_keywords: List[str], 
                                     question_topic: str, question_division: str, 
                                     question_text: str) -> float:
        """
        🆕 计算关键词匹配分数
        """
        score = 0.0
        
        # 1. Topic匹配（权重最高）
        for keyword in extracted_keywords:
            if keyword.lower() in question_topic:
                score += 10.0  # Topic匹配得10分
        
        # 2. Division匹配（权重中等）
        for keyword in extracted_keywords:
            if keyword.lower() in question_division:
                score += 5.0  # Division匹配得5分
        
        # 3. 题目文本匹配（权重较低）
        for keyword in extracted_keywords:
            if keyword.lower() in question_text.lower():
                score += 2.0  # 文本匹配得2分
        
        # 4. 扩展关键词匹配
        for keyword in extracted_keywords:
            if keyword in self.extended_keyword_mapping:
                for extended_keyword in self.extended_keyword_mapping[keyword]:
                    if extended_keyword.lower() in question_topic.lower():
                        score += 8.0  # 扩展关键词Topic匹配得8分
                    if extended_keyword.lower() in question_text.lower():
                        score += 3.0  # 扩展关键词文本匹配得3分
        
        return score

    def _get_matched_keywords(self, extracted_keywords: List[str], 
                            question_topic: str, question_division: str, 
                            question_text: str) -> List[str]:
        """
        🆕 获取匹配的关键词列表
        """
        matched_keywords = []
        
        for keyword in extracted_keywords:
            if (keyword.lower() in question_topic.lower() or 
                keyword.lower() in question_division.lower() or 
                keyword.lower() in question_text.lower()):
                matched_keywords.append(keyword)
        
        return matched_keywords

    def match_by_topic_code(self, knowledge_point: str, questions_data: List[Dict]) -> List[Dict]:
        """
        UPDATED: 匹配逻辑更新，以使用动态加载的关键词和新的匹配分数计算。
        """
        # 1. 预测知识点的topic_code (例如 'C01', 'G03')
        predicted_codes = self._predict_topic_codes(knowledge_point)
        
        if not predicted_codes:
            print(f"⚠️ 对于知识点 '{knowledge_point[:30]}...'，未能预测出任何topic code。")
            return []

        # 2. 从CSV中筛选匹配的题目
        matches = []
        for question in questions_data:
            # UPDATED: 从题库的 'Topic' 列获取该题目的代码
            question_topic_code = question.get('Topic')
            
            if not question_topic_code or pd.isna(question_topic_code):
                continue

            # 3. 计算匹配分数
            match_score = self._calculate_topic_match_score(predicted_codes, str(question_topic_code))
            
            if match_score > 0:
                question_with_score = question.copy()
                question_with_score['match_score'] = match_score
                question_with_score['predicted_codes_for_kp'] = predicted_codes
                matches.append(question_with_score)
        
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        return matches

    def _predict_topic_codes(self, knowledge_point: str) -> List[str]:
        """
        UPDATED: 预测逻辑现在使用从CSV加载的动态关键词库。
        """
        kp_lower = knowledge_point.lower()
        predicted = []
        
        # 遍历从 mapping.csv 加载的所有知识点
        for topic_code, keywords in self.topic_keywords.items():
            if any(keyword.lower() in kp_lower for keyword in keywords):
                predicted.append(topic_code)
        
        return predicted

    def _calculate_topic_match_score(self, predicted_codes: List[str], 
                                   question_topic_code: str) -> float:
        """
        UPDATED: 分数计算逻辑更新。
        如果题目的topic code在我们为知识点预测出的code列表里，就认为匹配。
        """
        if question_topic_code in predicted_codes:
            # 可以根据需要设计更复杂的分数，目前匹配上即给1分
            return 1.0 
        return 0.0

# ---------------- ^^^^ NEW CSVMatcher Class ^^^^ ----------------

class QuestionMatcher:
    """题目匹配器"""
    
    def __init__(self):
        self.questions_cache = None
        # 🆕 新增：CSV匹配器实例
        self.csv_matcher = CSVMatcher()
        # 🆕 新增：CSV匹配器实例
        self.csv_matcher = CSVMatcher()
        
    def load_questions(self) -> pd.DataFrame:
        """加载题目数据"""
        if self.questions_cache is None:
            # 尝试加载多个题库文件
            csv_files = [
                'data/questions/pdf_test_questions.csv',
                'data/questions/AMC10_realtest.csv', 
                'data/questions/AMC10_v250722.csv'
            ]
            
            for csv_file in csv_files:
                if os.path.exists(csv_file):
                    try:
                        self.questions_cache = pd.read_csv(csv_file)
                        print(f"✅ 成功加载题库: {csv_file} ({len(self.questions_cache)}道题)")
                        return self.questions_cache
                    except Exception as e:
                        print(f"❌ 加载{csv_file}失败: {e}")
                        continue
            
            print("❌ 未找到任何可用的题库文件")
            return pd.DataFrame()
        
        return self.questions_cache
    
    def find_questions_by_knowledge_point(self, knowledge_point: str, limit: int = 5) -> List[Dict]:
        """
        🆕 新增：基于知识点的智能匹配方法
        结合关键词提取和topic匹配，提供更准确的题目推荐
        """
        questions_df = self.load_questions()
        if questions_df.empty:
            return []
        
        # 转换为字典列表
        questions_data = questions_df.to_dict('records')
        
        # 1. 使用新的关键词匹配方法
        keyword_matches = self.csv_matcher.match_by_knowledge_point_keywords(knowledge_point, questions_data)
        
        # 2. 使用原有的topic code匹配方法
        topic_matches = self.csv_matcher.match_by_topic_code(knowledge_point, questions_data)
        
        # 3. 合并结果并去重
        all_matches = {}
        
        # 添加关键词匹配结果
        for match in keyword_matches:
            problem_id = match.get('Problem ID', '')
            if problem_id not in all_matches:
                all_matches[problem_id] = match
            else:
                # 如果已存在，取更高的分数
                all_matches[problem_id]['match_score'] = max(
                    all_matches[problem_id]['match_score'], 
                    match['match_score']
                )
        
        # 添加topic匹配结果
        for match in topic_matches:
            problem_id = match.get('Problem ID', '')
            if problem_id not in all_matches:
                all_matches[problem_id] = match
            else:
                # 如果已存在，取更高的分数
                all_matches[problem_id]['match_score'] = max(
                    all_matches[problem_id]['match_score'], 
                    match['match_score']
                )
        
        # 转换为列表并排序
        final_matches = list(all_matches.values())
        final_matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # 添加匹配信息
        for match in final_matches:
            match['knowledge_point'] = knowledge_point
            match['match_method'] = 'keyword_and_topic'
            match['relevance_score'] = min(100, match['match_score'] * 10)  # 转换为0-100的分数
        
        return final_matches[:limit]
    
    def find_questions_by_topics(self, predicted_topics: List[str], limit: int = 5) -> List[Dict]:
        """
        根据预测的topic_codes匹配题目 - 优化版本（优先Division和Topic字段）
        
        Args:
            predicted_topics: 预测的知识点标签列表
            limit: 返回题目数量限制
            
        Returns:
            List[Dict]: 匹配的题目列表
        """
        questions_df = self.load_questions()
        if questions_df.empty:
            return []
        
        matches = []
        for _, question in questions_df.iterrows():
            # 获取关键字段
            question_topic = str(question.get('Topic', '')).lower()
            question_division = str(question.get('Division', '')).lower()
            question_text = str(question.get('题目', ''))
            
            # 🆕 改进1: 优先使用Division和Topic字段匹配
            division_score = 0
            topic_score = 0
            
            # Division匹配（权重最高）
            for predicted_topic in predicted_topics:
                predicted_lower = predicted_topic.lower()
                
                # 检查Division字段
                if predicted_lower in question_division:
                    division_score += 5  # Division匹配得5分
                
                # 检查Topic字段
                if predicted_lower in question_topic:
                    topic_score += 3  # Topic匹配得3分
                
                # 🆕 改进2: 支持多Topic匹配（用逗号分隔）
                topic_list = [t.strip() for t in question_topic.split(',')]
                for topic in topic_list:
                    if predicted_lower in topic:
                        topic_score += 3
            
            # 🆕 改进3: 题目文本关键词匹配
            keyword_score = 0
            for predicted_topic in predicted_topics:
                predicted_lower = predicted_topic.lower()
                
                # 🆕 改进：更通用的中文关键词映射
                keyword_mapping = {
                    # 概率相关
                    '概率': ['probability', 'prob', 'chance', 'random', 'likely', 'unlikely', 'odds'],
                    '统计': ['statistics', 'stat', 'data', 'distribution', 'mean', 'median', 'mode'],
                    
                    # 几何相关
                    '几何': ['geometry', 'geometric', 'triangle', 'circle', 'area', 'perimeter', 'volume'],
                    '三角形': ['triangle', 'trigonometric', 'sine', 'cosine', 'tangent'],
                    '圆': ['circle', 'circumference', 'radius', 'diameter', 'arc'],
                    '面积': ['area', 'surface', 'square', 'rectangle'],
                    '周长': ['perimeter', 'circumference', 'boundary'],
                    '相似': ['similar', 'similarity', 'proportion', 'ratio'],
                    '全等': ['congruent', 'congruence', 'equal', 'identical'],
                    
                    # 代数相关
                    '代数': ['algebra', 'equation', 'polynomial', 'solve', 'factor', 'expression'],
                    '函数': ['function', 'graph', 'domain', 'range', 'f(x)', 'y='],
                    '方程': ['equation', 'solve', 'solution', 'root', 'zero'],
                    '多项式': ['polynomial', 'degree', 'coefficient', 'term'],
                    
                    # 数论相关
                    '数论': ['number theory', 'divisibility', 'prime', 'factor', 'modulo'],
                    '整除': ['divisible', 'divisibility', 'factor', 'multiple', 'divide'],
                    '模运算': ['modulo', 'mod', 'remainder', 'congruent', 'modular'],
                    '因数': ['factor', 'divisor', 'multiple', 'prime'],
                    '质数': ['prime', 'prime number', 'composite'],
                    
                    # 计数相关
                    '计数': ['count', 'counting', 'arrangement', 'combination'],
                    '组合': ['combination', 'combinatorics', 'permutation', 'arrangement'],
                    '排列': ['permutation', 'arrangement', 'order'],
                    
                    # 其他数学概念
                    '集合': ['set', 'element', 'subset', 'union', 'intersection'],
                    '逻辑': ['logic', 'logical', 'if', 'then', 'and', 'or'],
                    '不等式': ['inequality', 'greater than', 'less than', '≥', '≤'],
                    '绝对值': ['absolute value', '|x|', 'magnitude'],
                    '分数': ['fraction', 'numerator', 'denominator', 'ratio'],
                    '小数': ['decimal', 'decimal point', 'tenth', 'hundredth'],
                    '百分比': ['percent', 'percentage', '%', 'hundredth']
                }
                
                # 检查中文关键词映射
                for chinese_keyword, english_keywords in keyword_mapping.items():
                    if chinese_keyword in predicted_lower:
                        for english_keyword in english_keywords:
                            if english_keyword in question_text.lower():
                                keyword_score += 1
                
                # 直接英文关键词匹配
                if predicted_lower in question_text.lower():
                    keyword_score += 1
            
            # 🆕 改进4: 计算总分
            total_score = division_score + topic_score + keyword_score
            
            if total_score > 0:
                # 🆕 改进5: 计算相关度和难度
                relevance_score = self._calculate_relevance_score(division_score, topic_score, keyword_score)
                difficulty_level = self._analyze_difficulty(str(question.get('Difficulty', 'medium')), total_score)
                practice_priority = self._calculate_practice_priority(relevance_score, difficulty_level)
                difficulty_level = self._analyze_difficulty(question.get('难度', ''), total_score)
                practice_priority = self._calculate_practice_priority(relevance_score, difficulty_level)
                
                matches.append({
                    'Problem ID': question.get('Problem ID', ''),
                    'formatted_title': f"{question.get('年份', '')} {question.get('竞赛类别', '')} Problem {question.get('题号', '')}",
                    'question_text': question_text,
                    'topics': question_topic,
                    'division': question_division,
                    'difficulty': question.get('难度', ''),
                    'total_score': total_score,
                    'division_score': division_score,
                    'topic_score': topic_score,
                    'keyword_score': keyword_score,
                    'expected_match': self._judge_expected_match(question_topic, question_division),
                    # 🆕 新增字段
                    'relevance_score': relevance_score,  # 相关度评分 (0-100)
                    'difficulty_level': difficulty_level,  # 难度等级 (1-5)
                    'practice_priority': practice_priority,  # 练习优先级 (1-10)
                    'recommended_order': self._get_recommended_order(relevance_score, difficulty_level),
                    # 🆕 添加答案和解释字段
                    'answer': question.get('答案', ''),
                    'explanation': question.get('解题思路', ''),
                    'hint': question.get('提示', ''),
                    # 🆕 添加选项字段
                    'optionA': question.get('选项A', ''),
                    'optionB': question.get('选项B', ''),
                    'optionC': question.get('选项C', ''),
                    'optionD': question.get('选项D', ''),
                    'optionE': question.get('选项E', '')
                })
        
        # 🆕 改进6: 智能排序 - 相关度最高但难度最低优先
        matches.sort(key=lambda x: (x['relevance_score'], -x['difficulty_level']), reverse=True)
        return matches[:limit]
    
    def _judge_expected_match(self, topic: str, division: str) -> str:
        """根据Topic和Division判断预期匹配度 - 通用版本"""
        topic_lower = topic.lower()
        division_lower = division.lower()
        
        # 🆕 改进：通用匹配规则
        # 定义Topic和Division的对应关系
        topic_division_mapping = {
            'prob': 'c',      # 概率 -> 计数
            'geom': 'g',      # 几何 -> 几何
            'div': 's',       # 整除 -> 数论
            'mod': 's',       # 模运算 -> 数论
            'factor': 's',    # 因数 -> 数论
            'count': 'c',     # 计数 -> 计数
            'combinatorics': 'c',  # 组合 -> 计数
            'algebra': 'a',   # 代数 -> 代数
            'function': 'a',  # 函数 -> 代数
            'equation': 'a',  # 方程 -> 代数
            'triangle': 'g',  # 三角形 -> 几何
            'circle': 'g',    # 圆 -> 几何
            'area': 'g',      # 面积 -> 几何
            'perimeter': 'g', # 周长 -> 几何
            'similar': 'g',   # 相似 -> 几何
            'congruent': 'g', # 全等 -> 几何
        }
        
        # 检查是否有Topic-Division匹配
        for topic_keyword, expected_division in topic_division_mapping.items():
            if topic_keyword in topic_lower and division_lower == expected_division:
                return 'HIGH'
        
        # 检查是否有Topic匹配（不要求Division完全匹配）
        topic_keywords = ['prob', 'geom', 'div', 'mod', 'factor', 'count', 'combinatorics', 
                         'algebra', 'function', 'equation', 'triangle', 'circle', 'area', 
                         'perimeter', 'similar', 'congruent']
        
        for keyword in topic_keywords:
            if keyword in topic_lower:
                return 'MEDIUM'
        
        # 如果都没有匹配，检查是否有任何Topic内容
        if topic_lower.strip() and topic_lower != 'nan':
            return 'LOW'
        else:
            return 'VERY_LOW'
    
    def get_question_statistics(self) -> Dict:
        """获取题库统计信息"""
        questions_df = self.load_questions()
        if questions_df.empty:
            return {}
        
        stats = {
            'total_questions': len(questions_df),
            'topic_distribution': {}
        }
        
        if 'Topic' in questions_df.columns:
            topic_counts = questions_df['Topic'].value_counts()
            stats['topic_distribution'] = topic_counts.to_dict()
        
        return stats
    
    def _calculate_relevance_score(self, division_score: int, topic_score: int, keyword_score: int) -> float:
        """
        计算题目与知识点的相关度评分 (0-100)
        
        Args:
            division_score: Division匹配得分
            topic_score: Topic匹配得分
            keyword_score: 关键词匹配得分
            
        Returns:
            float: 相关度评分 (0-100)
        """
        # 权重分配
        division_weight = 0.5  # Division匹配权重最高
        topic_weight = 0.3     # Topic匹配权重中等
        keyword_weight = 0.2   # 关键词匹配权重最低
        
        # 标准化得分 (假设最大可能得分)
        max_division_score = 5  # 每个知识点最多5分
        max_topic_score = 3     # 每个知识点最多3分
        max_keyword_score = 2   # 每个知识点最多2分
        
        # 计算加权相关度
        normalized_division = min(division_score / max_division_score, 1.0)
        normalized_topic = min(topic_score / max_topic_score, 1.0)
        normalized_keyword = min(keyword_score / max_keyword_score, 1.0)
        
        relevance_score = (
            normalized_division * division_weight +
            normalized_topic * topic_weight +
            normalized_keyword * keyword_weight
        ) * 100
        
        return round(relevance_score, 1)
    
    def _analyze_difficulty(self, difficulty_code: str, total_score: int) -> int:
        """
        分析题目难度等级 (1-5)
        
        Args:
            difficulty_code: 难度代码 (E/M/H)
            total_score: 匹配总分
            
        Returns:
            int: 难度等级 (1-5)
        """
        # 基于难度代码的初始等级
        difficulty_mapping = {
            'E': 1,  # Easy
            'M': 3,  # Medium
            'H': 5   # Hard
        }
        
        base_difficulty = difficulty_mapping.get(difficulty_code.upper(), 3)
        
        # 根据匹配分数调整难度
        # 匹配分数越高，说明题目越相关，难度感知可能降低
        if total_score >= 8:
            adjusted_difficulty = max(1, base_difficulty - 1)
        elif total_score >= 5:
            adjusted_difficulty = base_difficulty
        else:
            adjusted_difficulty = min(5, base_difficulty + 1)
        
        return adjusted_difficulty
    
    def _calculate_practice_priority(self, relevance_score: float, difficulty_level: int) -> int:
        """
        计算练习优先级 (1-10)
        
        优先级策略：
        1. 相关度高 + 难度低 = 最高优先级
        2. 相关度高 + 难度中 = 高优先级
        3. 相关度中 + 难度低 = 中高优先级
        4. 相关度中 + 难度中 = 中优先级
        5. 相关度低 + 难度低 = 中低优先级
        6. 其他 = 低优先级
        
        Args:
            relevance_score: 相关度评分 (0-100)
            difficulty_level: 难度等级 (1-5)
            
        Returns:
            int: 练习优先级 (1-10)
        """
        # 相关度等级
        if relevance_score >= 80:
            relevance_level = 3  # 高相关度
        elif relevance_score >= 50:
            relevance_level = 2  # 中相关度
        else:
            relevance_level = 1  # 低相关度
        
        # 难度等级
        if difficulty_level <= 2:
            difficulty_level_score = 3  # 低难度
        elif difficulty_level <= 3:
            difficulty_level_score = 2  # 中难度
        else:
            difficulty_level_score = 1  # 高难度
        
        # 计算优先级
        priority = relevance_level * difficulty_level_score
        
        # 确保优先级在1-10范围内
        return max(1, min(10, priority))
    
    def _get_recommended_order(self, relevance_score: float, difficulty_level: int) -> str:
        """
        获取推荐练习顺序描述
        
        Args:
            relevance_score: 相关度评分
            difficulty_level: 难度等级
            
        Returns:
            str: 推荐顺序描述
        """
        if relevance_score >= 80 and difficulty_level <= 2:
            return "优先练习 - 高相关度低难度"
        elif relevance_score >= 60 and difficulty_level <= 3:
            return "推荐练习 - 中高相关度适中难度"
        elif relevance_score >= 40:
            return "可选练习 - 中等相关度"
        else:
            return "备选练习 - 相关度较低"
    
    def get_practice_recommendations(self, knowledge_point: str, limit: int = 10) -> Dict:
        """
        获取练习推荐列表（按优先级排序）
        
        Args:
            knowledge_point: 知识点名称
            limit: 推荐题目数量
            
        Returns:
            Dict: 练习推荐结果
        """
        # 🆕 使用新的基于知识点的匹配方法
        matched_questions = self.find_questions_by_knowledge_point(knowledge_point, limit * 2)
        
        # 按练习优先级排序
        matched_questions.sort(key=lambda x: x.get('practice_priority', 0), reverse=True)
        
        # 分类推荐
        recommendations = {
            'priority_1': [],  # 最高优先级
            'priority_2': [],  # 高优先级
            'priority_3': [],  # 中优先级
            'priority_4': []   # 低优先级
        }
        
        for question in matched_questions[:limit]:
            priority = question.get('practice_priority', 0)
            
            if priority >= 8:
                recommendations['priority_1'].append(question)
            elif priority >= 6:
                recommendations['priority_2'].append(question)
            elif priority >= 4:
                recommendations['priority_3'].append(question)
            else:
                recommendations['priority_4'].append(question)
        
        return {
            'knowledge_point': knowledge_point,
            'total_matched': len(matched_questions),
            'recommendations': recommendations,
            'practice_strategy': self._generate_practice_strategy(recommendations)
        }
    
    def _generate_practice_strategy(self, recommendations: Dict) -> str:
        """
        生成练习策略建议
        
        Args:
            recommendations: 推荐结果
            
        Returns:
            str: 练习策略
        """
        strategy = "📚 练习策略建议:\n"
        
        if recommendations['priority_1']:
            strategy += f"🎯 优先练习 ({len(recommendations['priority_1'])}题): 高相关度低难度，适合入门\n"
        
        if recommendations['priority_2']:
            strategy += f"📈 进阶练习 ({len(recommendations['priority_2'])}题): 中高相关度适中难度，巩固基础\n"
        
        if recommendations['priority_3']:
            strategy += f"🔍 拓展练习 ({len(recommendations['priority_3'])}题): 中等相关度，扩展知识面\n"
        
        if recommendations['priority_4']:
            strategy += f"💡 挑战练习 ({len(recommendations['priority_4'])}题): 相关度较低但可尝试\n"
        
        return strategy 