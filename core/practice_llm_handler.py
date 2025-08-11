import google.generativeai as genai
from typing import Dict

class PracticeLLMHandler:
    """
    负责处理练习对话框中的LLM交互。
    包括加载prompt模板、与Gemini API通信等。
    """
    def __init__(self, prompt_template_path: str):
        """
        初始化处理器，加载prompt模板。
        """
        self.prompt_template = self._load_prompt_template(prompt_template_path)
        self.model = genai.GenerativeModel('models/gemini-2.5-pro')

    def _load_prompt_template(self, filepath: str) -> str:
        """
        从文件加载prompt模板。
        """
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"❌ 错误: Prompt模板文件未找到 at {filepath}")
            return "错误：无法加载Prompt模板。"
        except Exception as e:
            print(f"❌ 错误: 读取Prompt模板文件时出错: {e}")
            return "错误：无法加载Prompt模板。"

    def generate_response(self, knowledge_point: str, question: Dict, user_message: str, language: str = '中文') -> str:
        """
        根据题目信息和用户消息，生成LLM的回复。
        
        Args:
            knowledge_point: 知识点名称
            question: 题目信息字典
            user_message: 用户消息
            language: 回复语言，默认为中文
        """
        if "错误" in self.prompt_template:
            return self.prompt_template

        try:
            # 准备填充模板所需的数据
            prompt_data = {
                'knowledge_point': knowledge_point,
                'title': question.get('title', ''),
                'question_text': question.get('question_text', ''),
                'optionA': question.get('optionA', ''),
                'optionB': question.get('optionB', ''),
                'optionC': question.get('optionC', ''),
                'optionD': question.get('optionD', ''),
                'optionE': question.get('optionE', ''),
                'answer': question.get('answer', 'N/A'),
                'explanation': question.get('explanation', 'N/A'),
                'user_message': user_message,
                'language': language
            }
            
            # 使用.format()方法填充模板
            final_prompt = self.prompt_template.format(**prompt_data)
            
            # 调用Gemini模型
            response = self.model.generate_content(final_prompt)
            
            # 🆕 修复Gemini API响应格式问题
            if hasattr(response, 'text'):
                return response.text
            elif hasattr(response, 'parts') and response.parts:
                return response.parts[0].text
            elif hasattr(response, 'candidates') and response.candidates:
                return response.candidates[0].content.parts[0].text
            else:
                return "抱歉，我暂时无法回复，请稍后再试。"

        except Exception as e:
            print(f"❌ 调用LLM生成回复时出错: {e}")
            return f"抱歉，处理您的请求时发生内部错误。"