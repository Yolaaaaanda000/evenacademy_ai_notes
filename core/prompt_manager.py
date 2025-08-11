"""
Prompt管理器 - 统一管理所有LLM的Prompt模板
"""

import os
import json
from typing import Dict, Optional, List
from datetime import datetime


class PromptManager:
    def __init__(self, prompts_dir: str = "./prompts"):
        """
        初始化Prompt管理器
        
        Args:
            prompts_dir: Prompt文件存放目录
        """
        self.prompts_dir = prompts_dir
        self._prompts_cache = {}  # 缓存已加载的Prompt
        
        # 确保prompts目录存在
        os.makedirs(prompts_dir, exist_ok=True)
        
        # Prompt文件映射配置
        self.prompt_files = {
            "video_analysis": "video_analysis.md",
            "summary_integration": "summary_integration.md",
            "knowledge_tagging": "knowledge_tagging.md",
            "question_matching": "question_matching.md",
            "tutor_conversation": "tutor_conversation.md"
        }
    
    def get_prompt(self, prompt_name: str, **kwargs) -> str:
        """
        获取并格式化Prompt
        
        Args:
            prompt_name: Prompt名称（如 'summary_integration'）
            **kwargs: 用于格式化Prompt的参数
            
        Returns:
            str: 格式化后的Prompt文本
        """
        try:
            # 加载Prompt内容
            prompt_content = self._load_prompt(prompt_name)
            
            # 格式化Prompt（替换占位符）
            formatted_prompt = prompt_content.format(**kwargs)
            
            print(f"✅ 成功加载Prompt: {prompt_name}")
            return formatted_prompt
            
        except FileNotFoundError:
            print(f"❌ Prompt文件不存在: {prompt_name}")
            return f"Error: Prompt '{prompt_name}' not found"
        
        except KeyError as e:
            print(f"❌ Prompt格式化失败，缺少参数: {e}")
            return f"Error: Missing parameter {e} for prompt '{prompt_name}'"
        
        except Exception as e:
            print(f"❌ 加载Prompt时出错: {e}")
            return f"Error: Failed to load prompt '{prompt_name}': {str(e)}"
    
    def _load_prompt(self, prompt_name: str) -> str:
        """
        从文件加载Prompt内容
        
        Args:
            prompt_name: Prompt名称
            
        Returns:
            str: Prompt文本内容
        """
        # 检查缓存
        if prompt_name in self._prompts_cache:
            return self._prompts_cache[prompt_name]
        
        # 获取文件路径
        if prompt_name in self.prompt_files:
            filename = self.prompt_files[prompt_name]
        else:
            filename = f"{prompt_name}.md"
        
        file_path = os.path.join(self.prompts_dir, filename)
        
        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read().strip()
        
        # 缓存内容
        self._prompts_cache[prompt_name] = content
        
        return content
    
    def list_available_prompts(self) -> List[str]:
        """
        列出所有可用的Prompt
        
        Returns:
            List[str]: Prompt名称列表
        """
        available_prompts = []
        
        # 扫描prompts目录
        if os.path.exists(self.prompts_dir):
            for filename in os.listdir(self.prompts_dir):
                if filename.endswith('.md'):
                    prompt_name = filename[:-3]  # 去掉.md后缀
                    available_prompts.append(prompt_name)
        
        return available_prompts
    
    def validate_prompt(self, prompt_name: str, required_params: List[str]) -> Dict[str, bool]:
        """
        验证Prompt是否包含所需的参数占位符
        
        Args:
            prompt_name: Prompt名称
            required_params: 必需的参数列表
            
        Returns:
            Dict: 验证结果
        """
        try:
            content = self._load_prompt(prompt_name)
            validation_result = {
                'exists': True,
                'missing_params': []
            }
            
            # 检查必需参数
            for param in required_params:
                placeholder = "{" + param + "}"
                if placeholder not in content:
                    validation_result['missing_params'].append(param)
            
            validation_result['valid'] = len(validation_result['missing_params']) == 0
            
            return validation_result
            
        except FileNotFoundError:
            return {
                'exists': False,
                'valid': False,
                'missing_params': required_params
            }
    
    def reload_prompt(self, prompt_name: str):
        """
        重新加载Prompt（清除缓存）
        
        Args:
            prompt_name: Prompt名称
        """
        if prompt_name in self._prompts_cache:
            del self._prompts_cache[prompt_name]
            print(f"🔄 已重新加载Prompt: {prompt_name}")
    
    def clear_cache(self):
        """清除所有Prompt缓存"""
        self._prompts_cache.clear()
        print("🗑️ 已清除所有Prompt缓存")
    
    def get_prompt_info(self, prompt_name: str) -> Dict:
        """
        获取Prompt的详细信息
        
        Args:
            prompt_name: Prompt名称
            
        Returns:
            Dict: Prompt信息
        """
        try:
            if prompt_name in self.prompt_files:
                filename = self.prompt_files[prompt_name]
            else:
                filename = f"{prompt_name}.md"
            
            file_path = os.path.join(self.prompts_dir, filename)
            
            if not os.path.exists(file_path):
                return {"exists": False}
            
            # 获取文件信息
            stat = os.stat(file_path)
            content = self._load_prompt(prompt_name)
            
            # 分析Prompt中的参数
            import re
            params = re.findall(r'\{(\w+)\}', content)
            unique_params = list(set(params))
            
            return {
                "exists": True,
                "file_path": file_path,
                "file_size": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "content_length": len(content),
                "word_count": len(content.split()),
                "parameters": unique_params,
                "parameter_count": len(unique_params)
            }
            
        except Exception as e:
            return {
                "exists": False,
                "error": str(e)
            }
    
    def create_prompt_template(self, prompt_name: str, template_content: str):
        """
        创建新的Prompt模板文件
        
        Args:
            prompt_name: Prompt名称
            template_content: 模板内容
        """
        if prompt_name in self.prompt_files:
            filename = self.prompt_files[prompt_name]
        else:
            filename = f"{prompt_name}.md"
        
        file_path = os.path.join(self.prompts_dir, filename)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(template_content)
        
        print(f"✅ 已创建Prompt模板: {file_path}")
        
        # 清除缓存以便重新加载
        if prompt_name in self._prompts_cache:
            del self._prompts_cache[prompt_name]


# 使用示例和测试函数
def test_prompt_manager():
    """测试Prompt管理器功能"""
    
    # 创建测试用的Prompt管理器
    pm = PromptManager("./test_prompts")
    
    # 创建测试Prompt
    test_prompt = """
你是一个{role}。

任务: {task}

要求:
1. {requirement1}
2. {requirement2}

请完成以下工作: {work_description}
"""
    
    pm.create_prompt_template("test_prompt", test_prompt)
    
    # 测试获取Prompt
    formatted = pm.get_prompt(
        "test_prompt",
        role="专业的教师",
        task="创建课程摘要",
        requirement1="保持专业性",
        requirement2="内容要准确",
        work_description="分析视频内容并生成摘要"
    )
    
    print("格式化后的Prompt:")
    print(formatted)
    
    # 测试验证功能
    validation = pm.validate_prompt("test_prompt", ["role", "task", "work_description"])
    print(f"验证结果: {validation}")
    
    # 测试信息获取
    info = pm.get_prompt_info("test_prompt")
    print(f"Prompt信息: {info}")
    
    print("✅ PromptManager测试完成")


if __name__ == "__main__":
    test_prompt_manager()