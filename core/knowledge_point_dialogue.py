"""
Knowledge Point Dialogue Handler
专门处理单个知识点的深度对话功能
"""

import google.generativeai as genai
import os
import re
from datetime import datetime
from typing import Dict, List, Any
from dotenv import load_dotenv


class KnowledgePointDialogueHandler:
    """知识点专用对话处理器类"""
    
    def __init__(self):
        """初始化知识点对话处理器"""
        # 主程序已经设置了环境变量，这里直接使用
        self.model = genai.GenerativeModel('gemini-2.5-flash')
        self.prompt_template = self._load_knowledge_point_prompt()
    
    def _load_knowledge_point_prompt(self) -> str:
        """加载知识点专用Prompt模板"""
        prompt_file_path = 'prompts/knowledge_point_focused.md'
        
        if not os.path.exists(prompt_file_path):
            print(f"⚠️  知识点Prompt文件不存在: {prompt_file_path}，使用默认Prompt")
            return self._get_default_prompt()
        
        try:
            with open(prompt_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 提取主Prompt模板（在```之间的内容）
            prompt_pattern = r'```\n(.*?)\n```'
            matches = re.findall(prompt_pattern, content, re.DOTALL)
            
            if not matches:
                print("⚠️  在Prompt文件中未找到模板内容，使用默认Prompt")
                return self._get_default_prompt()
            
            template = matches[0].strip()
            
            # 验证模板中是否包含必要的占位符
            required_placeholders = [
                '{knowledge_point_title}',
                '{knowledge_point_content}',
                '{knowledge_point_timestamp}',
                '{video_title}',
                '{related_concepts}',
                '{user_message}',
                '{dialogue_history}',
                '{dialogue_round}',
                '{focus_deviation_count}',
                '{language}'
            ]
            
            missing_placeholders = []
            for placeholder in required_placeholders:
                if placeholder not in template:
                    missing_placeholders.append(placeholder)
            
            if missing_placeholders:
                print(f"⚠️  Prompt模板缺少必要占位符: {missing_placeholders}，使用默认Prompt")
                return self._get_default_prompt()
            
            print("✅ 成功加载知识点专用Prompt模板")
            return template
            
        except Exception as e:
            print(f"⚠️  加载Prompt文件时出错: {e}，使用默认Prompt")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """获取默认的知识点Prompt模板"""
        return """
You are a professional knowledge point deep analysis assistant, specialized in helping students deeply understand individual knowledge points.

## Knowledge Point Information
- Knowledge Point Title: {knowledge_point_title}
- Knowledge Point Content: {knowledge_point_content}
- Knowledge Point Timestamp: {knowledge_point_timestamp}
- Source Video: {video_title}
- Related Concepts: {related_concepts}

## Dialogue Rules
1. **Strict Focus**: Only answer questions directly related to "{knowledge_point_title}"
2. **Deep Analysis**: Provide detailed explanations, principles, applications, and examples of the knowledge point
3. **Relevance Judgment**: If user questions exceed the knowledge point scope, politely refuse and guide back to focus
4. **Active Guidance**: Provide targeted deep question suggestions
5. **Knowledge Expansion**: Provide related concepts and practical applications within the knowledge point scope

## Current Dialogue State
- User Question: {user_message}
- Dialogue History: {dialogue_history}
- Dialogue Round: {dialogue_round}
- Focus Deviation Count: {focus_deviation_count}

## Response Requirements
1. First judge question relevance (high/medium/low)
2. Provide corresponding responses based on relevance:
   - High relevance: Deep analysis + Extended content + Guiding questions
   - Medium relevance: Brief answer + Guide back to focus
   - Low relevance: Polite refusal + Provide knowledge point related suggested questions
3. Respond in {language}
4. Maintain friendly and encouraging tone

Please start responding:
"""
    

    
    def generate_response(
        self, 
        knowledge_point_data: Dict[str, Any],
        user_message: str,
        dialogue_history: List[Dict[str, Any]] = None,
        dialogue_state: Dict[str, Any] = None,
        language: str = 'English'
    ) -> str:
        """
        生成知识点专用对话回复
        
        Args:
            knowledge_point_data: 知识点数据
            user_message: 用户消息
            dialogue_history: 对话历史
            dialogue_state: 对话状态
            
        Returns:
            str: AI回复内容
        """
        try:
            # 初始化或更新对话状态
            if dialogue_state is None:
                dialogue_state = {
                    'round': 0,
                    'focus_deviation_count': 0
                }
            
            # 更新对话轮次
            dialogue_state['round'] += 1
            
            # 格式化对话历史
            formatted_history = self._format_dialogue_history(dialogue_history or [])
            
            # 准备Prompt参数
            prompt_params = {
                'knowledge_point_title': knowledge_point_data.get('title', ''),
                'knowledge_point_content': knowledge_point_data.get('content', ''),
                'knowledge_point_timestamp': knowledge_point_data.get('timestamp', ''),
                'video_title': knowledge_point_data.get('video_title', ''),
                'related_concepts': knowledge_point_data.get('related_concepts', ''),
                'user_message': user_message,
                'dialogue_history': formatted_history,
                'dialogue_round': dialogue_state['round'],
                'focus_deviation_count': dialogue_state['focus_deviation_count'],
                'language': language
            }
            
            # 格式化Prompt
            try:
                formatted_prompt = self.prompt_template.format(**prompt_params)
                print(f"📝 Prompt格式化成功，长度: {len(formatted_prompt)} 字符")
            except KeyError as e:
                print(f"❌ Prompt格式化失败，缺少参数: {e}")
                return f"抱歉，系统配置错误，缺少必要参数: {str(e)}"
            except Exception as e:
                print(f"❌ Prompt格式化失败: {e}")
                return f"抱歉，系统配置错误: {str(e)}"
            
            # 生成回复
            try:
                response = self.model.generate_content(formatted_prompt)
                
                # 检查响应状态和内容
                if not response:
                    print(f"❌ LLM调用失败: 响应为空")
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
                
                # 检查响应文本
                if not hasattr(response, 'text') or not response.text:
                    print(f"❌ LLM调用失败: 响应没有文本内容")
                    return "抱歉，AI服务暂时不可用，请稍后重试。"
                
                ai_response = response.text
                print(f"✅ 知识点对话回复生成成功 (轮次: {dialogue_state['round']})")
                return ai_response
            except Exception as e:
                print(f"❌ LLM调用失败: {e}")
                return f"抱歉，AI服务暂时不可用，请稍后再试。错误信息: {str(e)}"
            
        except Exception as e:
            print(f"❌ 生成知识点对话回复失败: {e}")
            return f"抱歉，处理您的请求时出现错误: {str(e)}"
    
    def _format_dialogue_history(self, history: List[Dict[str, Any]]) -> str:
        """格式化对话历史"""
        if not history:
            return "无对话历史"
        
        formatted_lines = []
        for entry in history[-10:]:  # 只保留最近10轮对话
            timestamp = entry.get('timestamp', '')
            role = entry.get('role', '')
            content = entry.get('content', '')
            
            if timestamp and role and content:
                formatted_lines.append(f"[{timestamp}] {role}: {content}")
        
        return '\n'.join(formatted_lines) if formatted_lines else "无对话历史"


def handle_knowledge_point_dialogue_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理知识点对话请求的便捷函数
    
    Args:
        request_data: 包含知识点数据和用户消息的请求数据
        
    Returns:
        Dict: 处理结果
    """
    try:
        # 验证请求数据
        required_fields = ['knowledge_point_data', 'user_message']
        for field in required_fields:
            if field not in request_data:
                return {
                    'success': False,
                    'error': f'Missing required field: {field}',
                    'response': None
                }
        
        # 创建处理器实例
        handler = KnowledgePointDialogueHandler()
        
        # 提取参数
        knowledge_point_data = request_data['knowledge_point_data']
        user_message = request_data['user_message']
        dialogue_history = request_data.get('dialogue_history', [])
        dialogue_state = request_data.get('dialogue_state')
        
        # 生成回复
        language = request_data.get('language', 'English')
        response = handler.generate_response(
            knowledge_point_data=knowledge_point_data,
            user_message=user_message,
            dialogue_history=dialogue_history,
            dialogue_state=dialogue_state,
            language=language
        )
        
        return {
            'success': True,
            'response': response,
            'error': None
        }
        
    except Exception as e:
        return {
            'success': False,
            'error': str(e),
            'response': None
        }


 