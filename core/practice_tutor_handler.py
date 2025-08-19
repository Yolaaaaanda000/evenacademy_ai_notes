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
        self.model = genai.GenerativeModel('gemini-2.5-flash')

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

    def generate_response(self, knowledge_point: str, question: Dict, user_message: str, language: str = 'English') -> str:
        """
        根据题目信息和用户消息，生成LLM的回复。
        
        Args:
            knowledge_point: 知识点名称
            question: 题目信息字典
            user_message: 用户消息
            language: 回复语言，默认为英文
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
            
            # 检查响应状态和内容
            if not response:
                return "抱歉，AI服务暂时不可用，请稍后重试。"
            
            # 检查是否有finish_reason错误
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason'):
                    finish_reason = candidate.finish_reason
                    if finish_reason in [0, 1]:  # 0和1都表示正常完成
                        print(f"✅ LLM调用正常完成 (finish_reason={finish_reason})")
                    elif finish_reason == 2:
                        print(f"⚠️ LLM调用达到最大token限制 (finish_reason=2)")
                    elif finish_reason == 3:
                        print(f"❌ LLM调用被安全过滤阻止 (finish_reason=3)")
                        return "抱歉，内容因安全问题被阻止，请重新提问。"
                    elif finish_reason == 4:
                        print(f"⚠️ LLM调用达到递归限制 (finish_reason=4)")
                    else:
                        print(f"⚠️ LLM调用出现未知状态 (finish_reason={finish_reason})")
            
            # 🆕 修复Gemini API响应格式问题
            if hasattr(response, 'text') and response.text:
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