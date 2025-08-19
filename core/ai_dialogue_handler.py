"""
AI对话处理器模块
提供统一的AI对话功能，支持不同上下文类型
"""

import google.generativeai as genai
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from dotenv import load_dotenv


class AIDialogueHandler:
    """AI对话处理器类"""
    
    def __init__(self):
        """初始化AI对话处理器"""
        # 加载环境变量
        load_dotenv('llm.env')
        genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
        
        # 设置代理（与主程序保持一致）
        os.environ['https_proxy'] = "http://127.0.0.1:8118"
        os.environ['http_proxy'] = "http://127.0.0.1:8118"
        os.environ['all_proxy'] = "socks5://127.0.0.1:8119"
        
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.prompt_templates = self._load_prompt_templates()
    
    def _load_prompt_templates(self) -> Dict[str, str]:
        """从外部文件加载提示词模板"""
        try:
            import re
            
            # 读取提示词模板文件
            template_file_path = 'prompts/ai_dialogue_templates.md'
            
            if not os.path.exists(template_file_path):
                print(f"⚠️  提示词模板文件不存在: {template_file_path}")
                return self._get_default_templates()
            
            with open(template_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 解析模板
            templates = {}
            
            # 使用正则表达式提取模板
            template_pattern = r'## ([^\n]+) Context Template \(([^)]+)\)\n\n```\n(.*?)\n```'
            matches = re.findall(template_pattern, content, re.DOTALL)
            
            for title, context_type, template in matches:
                templates[context_type] = template.strip()
            
            print(f"✅ 成功加载 {len(templates)} 个提示词模板")
            return templates
            
        except Exception as e:
            print(f"❌ 加载提示词模板失败: {e}")
            return self._get_default_templates()
    
    def _get_default_templates(self) -> Dict[str, str]:
        """Get default prompt templates (fallback)"""
        return {
            'video': """
You are a professional AI learning assistant, specialized in helping students understand video course content.

Video Information:
- Title: {title}
- Current playback time: {current_time} seconds
- Total duration: {duration} seconds

Knowledge Points:
{knowledge_points}

Video Summary:
{summary}

Student Question: {message}

Dialogue History:
{dialogue_history}

Please provide helpful answers based on the video content and the student's specific questions. Your responses should:
1. Directly address the student's question
2. Incorporate specific knowledge points from the video
3. Provide relevant explanations and examples
4. Encourage deep thinking
5. Use friendly and understandable language

Please respond in English.
            """,
            
            'summary': """
You are a professional AI summary assistant, specialized in helping students understand course summary content.

Summary Information:
- Title: {title}
- Content: {content}
- Concept Count: {concept_count}

Student Question: {message}

Dialogue History:
{dialogue_history}

Please provide professional, accurate, and helpful answers based on the summary content and the student's specific questions. Your responses should:
1. Be based on the actual content in the summary
2. Use clear and concise language
3. Provide specific explanations and examples
4. Encourage deep thinking
5. Reference specific knowledge points when possible

Please respond in English.
            """,
            
            'practice': """
You are a professional AI practice assistant, specialized in helping students solve practice problems.

Practice Information:
- Knowledge Point: {knowledge_point}
- Current Question: {current_question}

Student Question: {message}

Dialogue History:
{dialogue_history}

Please provide helpful answers based on the practice content and the student's specific questions. Your responses should:
1. Directly address the student's question
2. Provide problem-solving strategies and techniques
3. Analyze error causes (if any)
4. Give improvement suggestions
5. Use encouraging language

Please respond in English.
            """,
            
            'knowledge_graph': """
You are a professional AI knowledge assistant, specialized in helping students understand knowledge graphs.

Knowledge Graph Information:
- Title: {title}
- Concept Relationships: {concept_relationships}
- Knowledge Structure: {knowledge_structure}

Student Question: {message}

Dialogue History:
{dialogue_history}

Please provide helpful answers based on the knowledge graph content and the student's specific questions. Your responses should:
1. Explain relationships between concepts
2. Provide learning path suggestions
3. Analyze knowledge structure
4. Encourage exploration
5. Use clear language

Please respond in English.
            """
        }
    
    def generate_response(self, context_type: str, message: str, context_data: Dict[str, Any], 
                         dialogue_history: List[Dict[str, Any]] = None) -> str:
        """
        生成AI响应
        
        Args:
            context_type: 上下文类型 (video, summary, practice, knowledge_graph)
            message: 用户消息
            context_data: 上下文数据
            dialogue_history: 对话历史
            
        Returns:
            str: AI响应内容
        """
        try:
            print(f"🤖 [LLM调用开始] 上下文类型: {context_type}")
            print(f"📝 用户消息: {message}")
            
            # 获取提示词模板
            template = self.prompt_templates.get(context_type, self.prompt_templates['video'])
            print(f"📋 使用模板: {context_type}")
            
            # 格式化对话历史
            history_text = self._format_dialogue_history(dialogue_history or [])
            print(f"💬 对话历史长度: {len(history_text)} 字符")
            
            # 格式化上下文数据
            formatted_context = self._format_context_data(context_type, context_data)
            print(f"📊 上下文数据字段: {list(formatted_context.keys())}")
            
            # 构建完整提示词
            prompt = template.format(
                message=message,
                dialogue_history=history_text,
                **formatted_context
            )
            print(f"📄 提示词长度: {len(prompt)} 字符")
            
            # 调用AI模型
            print(f"🚀 开始调用Gemini API...")
            response = self.model.generate_content(prompt)
            
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
            
            print(f"✅ LLM调用成功!")
            print(f"📤 响应长度: {len(response.text)} 字符")
            
            return response.text
            
        except Exception as e:
            print(f"❌ AI对话处理错误: {e}")
            print(f"🔍 错误类型: {type(e).__name__}")
            return f"抱歉，我遇到了一些问题。错误信息: {str(e)}"
    
    def _format_dialogue_history(self, history: List[Dict[str, Any]]) -> str:
        """格式化对话历史"""
        if not history:
            return "无对话历史"
        
        formatted = []
        for msg in history[-5:]:  # 只保留最近5条消息
            role = "用户" if msg.get('type') == 'user' else "AI助手"
            content = msg.get('content', '')
            timestamp = msg.get('timestamp', '')
            
            if timestamp:
                time_str = timestamp.strftime('%H:%M') if hasattr(timestamp, 'strftime') else str(timestamp)
                formatted.append(f"[{time_str}] {role}: {content}")
            else:
                formatted.append(f"{role}: {content}")
        
        return "\n".join(formatted)
    
    def _format_context_data(self, context_type: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """格式化上下文数据"""
        if context_type == 'video':
            return {
                'title': context_data.get('title', '未知视频'),
                'current_time': context_data.get('current_time', 0),
                'duration': context_data.get('duration', 0),
                'knowledge_points': self._format_knowledge_points(context_data.get('knowledge_points', [])),
                'summary': context_data.get('summary', '暂无摘要')
            }
        elif context_type == 'summary':
            return {
                'title': context_data.get('title', '未知摘要'),
                'content': context_data.get('content', ''),
                'concept_count': context_data.get('concept_count', '0')
            }
        elif context_type == 'practice':
            return {
                'knowledge_point': context_data.get('knowledge_point', ''),
                'current_question': context_data.get('current_question', '')
            }
        elif context_type == 'knowledge_graph':
            return {
                'title': context_data.get('title', '未知知识图谱'),
                'concept_relationships': context_data.get('concept_relationships', ''),
                'knowledge_structure': context_data.get('knowledge_structure', '')
            }
        else:
            return context_data
    
    def _format_knowledge_points(self, knowledge_points: List[Dict[str, Any]]) -> str:
        """格式化知识点列表"""
        if not knowledge_points:
            return "暂无知识点信息"
        
        formatted = []
        for i, point in enumerate(knowledge_points, 1):
            title = point.get('title', '未知知识点')
            time = point.get('time', '未知时间')
            formatted.append(f"{i}. {title} (时间: {time})")
        
        return "\n".join(formatted)
    
    def validate_request(self, context_type: str, message: str, context_data: Dict[str, Any]) -> bool:
        """验证请求参数"""
        if not message or not message.strip():
            return False
        
        if context_type not in self.prompt_templates:
            return False
        
        return True
    
    def get_supported_context_types(self) -> List[str]:
        """获取支持的上下文类型"""
        return list(self.prompt_templates.keys())


# 全局AI对话处理器实例
ai_dialogue_handler = AIDialogueHandler()


def handle_ai_dialogue_request(request_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理AI对话请求的统一接口
    
    Args:
        request_data: 请求数据
        
    Returns:
        Dict[str, Any]: 响应数据
    """
    try:
        print(f"\n🎯 [AI对话请求开始]")
        print(f"📦 请求数据: {list(request_data.keys())}")
        
        # 提取请求参数
        message = request_data.get('message', '')
        context_type = request_data.get('context_type', 'video')
        context_data = request_data.get('context_data', {})
        dialogue_history = request_data.get('dialogue_history', [])
        
        print(f"📝 消息: {message[:50]}{'...' if len(message) > 50 else ''}")
        print(f"🏷️  上下文类型: {context_type}")
        print(f"📊 上下文数据字段: {list(context_data.keys())}")
        print(f"💬 对话历史条数: {len(dialogue_history)}")
        
        # 验证请求
        if not ai_dialogue_handler.validate_request(context_type, message, context_data):
            print(f"❌ 请求验证失败")
            return {
                'success': False,
                'error': '请求参数无效'
            }
        
        print(f"✅ 请求验证通过")
        
        # 生成响应
        response = ai_dialogue_handler.generate_response(
            context_type=context_type,
            message=message,
            context_data=context_data,
            dialogue_history=dialogue_history
        )
        
        print(f"🎉 [AI对话请求完成] 响应长度: {len(response)} 字符")
        
        return {
            'success': True,
            'response': response
        }
        
    except Exception as e:
        print(f"❌ 处理AI对话请求时出错: {e}")
        print(f"🔍 错误类型: {type(e).__name__}")
        return {
            'success': False,
            'error': f'处理请求时发生错误: {str(e)}'
        } 