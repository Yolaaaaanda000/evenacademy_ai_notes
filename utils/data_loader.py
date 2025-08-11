"""
数据加载器 - 用于加载题库和其他数据文件
"""

import pandas as pd
import os
import json
from typing import Dict, List, Optional


class QuestionLoader:
    """题目数据加载器"""
    
    def __init__(self):
        self.data_dir = "data"
        self.questions_dir = os.path.join(self.data_dir, "questions")
        self.cache = {}
        
    def load_csv_questions(self, filename: str) -> pd.DataFrame:
        """
        加载CSV格式的题目数据
        
        Args:
            filename: CSV文件名
            
        Returns:
            pd.DataFrame: 题目数据
        """
        filepath = os.path.join(self.questions_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ 文件不存在: {filepath}")
            return pd.DataFrame()
        
        try:
            # 尝试不同的编码格式
            encodings = ['utf-8', 'gbk', 'gb2312', 'latin1']
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(filepath, encoding=encoding)
                    print(f"✅ 成功加载题目文件: {filename} (编码: {encoding})")
                    return df
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    print(f"❌ 加载文件失败: {e}")
                    continue
            
            print(f"❌ 无法加载文件: {filename}")
            return pd.DataFrame()
            
        except Exception as e:
            print(f"❌ 加载题目文件失败: {e}")
            return pd.DataFrame()
    
    def load_all_question_files(self) -> Dict[str, pd.DataFrame]:
        """
        加载所有题目文件
        
        Returns:
            Dict[str, pd.DataFrame]: 文件名到数据框的映射
        """
        if not os.path.exists(self.questions_dir):
            print(f"❌ 题目目录不存在: {self.questions_dir}")
            return {}
        
        question_files = {}
        
        for filename in os.listdir(self.questions_dir):
            if filename.endswith('.csv'):
                df = self.load_csv_questions(filename)
                if not df.empty:
                    question_files[filename] = df
        
        print(f"📊 总共加载了 {len(question_files)} 个题目文件")
        return question_files
    
    def get_question_statistics(self, df: pd.DataFrame) -> Dict:
        """
        获取题目数据统计信息
        
        Args:
            df: 题目数据框
            
        Returns:
            Dict: 统计信息
        """
        if df.empty:
            return {}
        
        stats = {
            'total_questions': len(df),
            'columns': list(df.columns),
            'missing_values': df.isnull().sum().to_dict()
        }
        
        # 如果有Topic列，统计主题分布
        if 'Topic' in df.columns:
            topic_counts = df['Topic'].value_counts()
            stats['topic_distribution'] = topic_counts.head(10).to_dict()
        
        # 如果有年份列，统计年份分布
        if '年份' in df.columns:
            year_counts = df['年份'].value_counts()
            stats['year_distribution'] = year_counts.head(10).to_dict()
        
        return stats
    
    def search_questions(self, df: pd.DataFrame, keywords: List[str], 
                        search_columns: List[str] = None) -> pd.DataFrame:
        """
        在题目中搜索关键词
        
        Args:
            df: 题目数据框
            keywords: 搜索关键词列表
            search_columns: 搜索的列名列表
            
        Returns:
            pd.DataFrame: 匹配的题目
        """
        if df.empty:
            return pd.DataFrame()
        
        if search_columns is None:
            search_columns = ['题目', 'Topic', 'formatted_title']
        
        # 过滤存在的列
        available_columns = [col for col in search_columns if col in df.columns]
        
        if not available_columns:
            print("❌ 没有可搜索的列")
            return pd.DataFrame()
        
        # 创建搜索条件
        search_conditions = []
        for keyword in keywords:
            keyword_conditions = []
            for col in available_columns:
                keyword_conditions.append(df[col].str.contains(keyword, case=False, na=False))
            search_conditions.append(pd.concat(keyword_conditions, axis=1).any(axis=1))
        
        # 合并所有条件（OR关系）
        if search_conditions:
            final_condition = pd.concat(search_conditions, axis=1).any(axis=1)
            matched_df = df[final_condition]
        else:
            matched_df = pd.DataFrame()
        
        print(f"🔍 搜索关键词 {keywords} 找到 {len(matched_df)} 道题目")
        return matched_df
    
    def filter_questions_by_topic(self, df: pd.DataFrame, topics: List[str]) -> pd.DataFrame:
        """
        根据主题过滤题目
        
        Args:
            df: 题目数据框
            topics: 主题列表
            
        Returns:
            pd.DataFrame: 过滤后的题目
        """
        if df.empty or 'Topic' not in df.columns:
            return pd.DataFrame()
        
        # 创建主题过滤条件
        topic_conditions = []
        for topic in topics:
            topic_conditions.append(df['Topic'].str.contains(topic, case=False, na=False))
        
        if topic_conditions:
            final_condition = pd.concat(topic_conditions, axis=1).any(axis=1)
            filtered_df = df[final_condition]
        else:
            filtered_df = pd.DataFrame()
        
        print(f"📋 根据主题 {topics} 过滤得到 {len(filtered_df)} 道题目")
        return filtered_df
    
    def get_random_questions(self, df: pd.DataFrame, n: int = 5) -> pd.DataFrame:
        """
        随机获取题目
        
        Args:
            df: 题目数据框
            n: 题目数量
            
        Returns:
            pd.DataFrame: 随机题目
        """
        if df.empty:
            return pd.DataFrame()
        
        n = min(n, len(df))
        random_df = df.sample(n=n, random_state=42)
        
        print(f"🎲 随机获取了 {len(random_df)} 道题目")
        return random_df


class DataLoader:
    """通用数据加载器"""
    
    def __init__(self):
        self.data_dir = "data"
        self.cache = {}
    
    def load_json(self, filename: str) -> Dict:
        """
        加载JSON文件
        
        Args:
            filename: JSON文件名
            
        Returns:
            Dict: JSON数据
        """
        filepath = os.path.join(self.data_dir, filename)
        
        if not os.path.exists(filepath):
            print(f"❌ 文件不存在: {filepath}")
            return {}
        
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
            print(f"✅ 成功加载JSON文件: {filename}")
            return data
        except Exception as e:
            print(f"❌ 加载JSON文件失败: {e}")
            return {}
    
    def save_json(self, data: Dict, filename: str) -> bool:
        """
        保存JSON文件
        
        Args:
            data: 要保存的数据
            filename: 文件名
            
        Returns:
            bool: 是否保存成功
        """
        filepath = os.path.join(self.data_dir, filename)
        
        try:
            # 确保目录存在
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 成功保存JSON文件: {filename}")
            return True
        except Exception as e:
            print(f"❌ 保存JSON文件失败: {e}")
            return False
    
    def list_data_files(self, extension: str = None) -> List[str]:
        """
        列出数据文件
        
        Args:
            extension: 文件扩展名过滤
            
        Returns:
            List[str]: 文件名列表
        """
        if not os.path.exists(self.data_dir):
            return []
        
        files = []
        for filename in os.listdir(self.data_dir):
            if extension is None or filename.endswith(extension):
                files.append(filename)
        
        return files


# 使用示例
if __name__ == "__main__":
    # 测试题目加载器
    loader = QuestionLoader()
    
    # 加载所有题目文件
    question_files = loader.load_all_question_files()
    
    # 显示统计信息
    for filename, df in question_files.items():
        print(f"\n📊 {filename} 统计信息:")
        stats = loader.get_question_statistics(df)
        for key, value in stats.items():
            print(f"  {key}: {value}")
    
    # 测试搜索功能
    if question_files:
        first_df = list(question_files.values())[0]
        print(f"\n🔍 搜索测试:")
        search_results = loader.search_questions(first_df, ['probability', '概率'])
        print(f"找到 {len(search_results)} 道相关题目") 