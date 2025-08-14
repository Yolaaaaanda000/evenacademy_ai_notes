"""
Summary整合器 - 专门负责将视频分段内容整合为高质量的完整Summary文档
更新版本：使用PromptManager管理Prompt模板
"""

import json
import re
from typing import Dict, List, Optional
import google.generativeai as genai
from datetime import datetime
from core.prompt_manager import PromptManager  # 🆕 导入PromptManager


class SummaryIntegrator:
    def __init__(self, api_key: str, prompts_dir: str = "./prompts"):
        """
        初始化Summary整合器
        
        Args:
            api_key: Google Gemini API密钥
            prompts_dir: Prompt模板文件目录
        """
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

        # 🆕 初始化Prompt管理器
        self.prompt_manager = PromptManager(prompts_dir)
        
        # 验证必需的Prompt是否存在
        self._validate_required_prompts()

    def _validate_required_prompts(self):
        """验证必需的Prompt文件是否存在"""
        required_prompts = {
            "summary_integration": ["lecture_title", "segments_content"]
        }
        
        for prompt_name, required_params in required_prompts.items():
            validation = self.prompt_manager.validate_prompt(prompt_name, required_params)
            
            if not validation['exists']:
                print(f"⚠️ 缺少Prompt文件: {prompt_name}.md")
                print(f"请在 {self.prompt_manager.prompts_dir} 目录下创建该文件")
            elif not validation['valid']:
                print(f"⚠️ Prompt文件 {prompt_name}.md 缺少必需参数: {validation['missing_params']}")

    def generate_summary(self, analysis: Dict, transcription: Dict, lecture_title: str, language: str = "中文") -> Dict:
        """
        生成完整的Summary文档
        
        Args:
            analysis: 视频分析结果（包含content_segments）
            transcription: 转录结果
            lecture_title: 课程标题
            language: 语言
            
        Returns:
            Dict: 包含Summary文档和相关信息
        """
        print("📋 正在整合分段内容为完整Summary...")
        
        try:
            # 1. 验证输入数据
            segments = analysis.get('content_segments', [])
            if not segments:
                return self._create_empty_result("无分段内容可整合")
            
            # 2. 格式化分段内容
            segments_content = self._format_segments_for_integration(segments, language)
            
            # 🆕 3. 使用PromptManager获取Prompt模板
            try:
                # 🆕 根据语言动态生成文档结构
                language_header_structure = self._get_language_header_structure(language, lecture_title)
                
                integration_prompt = self.prompt_manager.get_prompt(
                    "summary_integration",
                    lecture_title=lecture_title,
                    segments_content=segments_content,
                    language=language,
                    language_header_structure=language_header_structure
                )
            except Exception as e:
                print(f"❌ 获取Prompt模板失败: {e}")
                return self._create_empty_result(f"Prompt加载失败: {str(e)}")
            
            # 4. 调用LLM生成Summary
            print("🤖 正在调用LLM生成Summary...")
            print(f"📝 Prompt长度: {len(integration_prompt)} 字符")
            print(f"📝 Prompt前200字符: {integration_prompt[:200]}...")
            
            try:
                generation_config = {
                    "temperature": 0.1,
                }

                response = self.model.generate_content(
                    integration_prompt,
                    generation_config=generation_config
                )

                print(f"✅ LLM调用成功，响应对象类型: {type(response)}")
                
                # 详细打印响应信息
                if hasattr(response, '__dict__'):
                    print(f"🔍 响应对象属性: {list(response.__dict__.keys())}")
                
                if hasattr(response, 'candidates') and response.candidates:
                    print(f"🔍 候选数量: {len(response.candidates)}")
                    for i, candidate in enumerate(response.candidates):
                        print(f"🔍 候选{i+1}属性: {list(candidate.__dict__.keys())}")
                        if hasattr(candidate, 'finish_reason'):
                            print(f"🔍 候选{i+1} finish_reason: {candidate.finish_reason}")
                        if hasattr(candidate, 'finish_message'):
                            print(f"🔍 候选{i+1} finish_message: {candidate.finish_message}")
                        if hasattr(candidate, 'safety_ratings'):
                            print(f"🔍 候选{i+1} safety_ratings: {candidate.safety_ratings}")
                
                if hasattr(response, 'prompt_feedback'):
                    print(f"🔍 Prompt反馈: {response.prompt_feedback}")
                
            except Exception as api_error:
                print(f"❌ LLM API调用异常: {type(api_error).__name__}: {api_error}")
                print(f"🔍 异常详情: {str(api_error)}")
                return self._create_empty_result(f"LLM API调用异常: {str(api_error)}")
            
            # 检查响应状态和内容
            if not response:
                print("❌ LLM响应为空")
                return self._create_empty_result("LLM响应为空")
            
            # 检查是否有finish_reason错误
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                if hasattr(candidate, 'finish_reason') and candidate.finish_reason not in [0, 1]: # 0 and 1 are success states
                    reason = candidate.finish_reason
                    message = f"LLM响应异常 (finish_reason={reason})"
                    
                    # Provide more specific error messages
                    if reason == 3: # SAFETY
                        message = f"内容因安全问题被阻止 (finish_reason=3)。Safety Ratings: {candidate.safety_ratings}"
                        print(f"❌ {message}")
                    else:
                        print(f"❌ {message}")
                        
                    return self._create_empty_result(message)
            

            # 检查响应文本
            integrated_summary = ""
            try:
                # This is the 'quick accessor' that can fail if no text part is returned.
                integrated_summary = response.text
                if not integrated_summary.strip():
                    # This handles cases where the model returns text, but it's just empty space.
                    print("❌ 响应的text属性为空白内容。")
                    return self._create_empty_result("LLM响应返回了空文本。")

            except ValueError:
                # This block catches the exact error you are seeing.
                print("❌ 访问 response.text 失败，因为模型没有返回文本内容。")
                
                # Now, let's inspect what the response *actually* contains to find out why.
                try:
                    part = response.candidates[0].content.parts[0]
                    if hasattr(part, 'function_call') and part.function_call:
                        fc = part.function_call
                        print(f"🔍 诊断：响应包含一个工具调用: {fc.name}")
                        return self._create_empty_result(f"模型试图调用工具 '{fc.name}'，而不是生成文本。请检查您的Prompt是否过于复杂。")
                    else:
                        print("🔍 诊断：响应不包含文本或已知的工具调用。")
                        return self._create_empty_result("响应不包含有效的文本部分。")
                except (IndexError, AttributeError):
                    print("🔍 诊断：无法检查响应的具体内容。")
                    return self._create_empty_result("响应结构异常，无法解析。")

            print(f"✅ 成功获取响应文本，长度: {len(integrated_summary)} 字符")
            
            # 5. 创建时间戳映射
            timestamp_mapping = self._create_timestamp_mapping(segments)
            
            # 6. 提取知识点结构化信息
            knowledge_points = self._extract_structured_knowledge_points(segments, language)
            
            # 🆕 7. 验证生成的Summary质量
            quality_check = self.validate_summary_quality(integrated_summary, language)
            
            print("✅ Summary整合完成")
            
            return {
                "summary": integrated_summary,
                "timestamp_mapping": timestamp_mapping,
                "knowledge_points": knowledge_points,
                "segments_count": len(segments),
                "generation_time": datetime.now().isoformat(),
                "quality_check": quality_check,  # 🆕 质量检查结果
                "success": True
            }
            
        except Exception as e:
            print(f"❌ Summary整合失败: {e}")
            return self._create_empty_result(f"整合失败: {str(e)}")
    
    def _format_segments_for_integration(self, segments: List[Dict], language: str = "中文") -> str:
        """
        将分段内容格式化为适合LLM处理的文本
        
        Args:
            segments: 视频分段列表
            language: 输出语言
            
        Returns:
            str: 格式化后的分段内容
        """
        formatted_content = []
        
        # 🆕 添加知识点标题列表，便于LLM识别
        knowledge_point_titles = []
        for segment in segments:
            title = segment.get('title', '')
            if title:
                knowledge_point_titles.append(title)
        
        # 添加知识点标题概览
        if knowledge_point_titles:
            formatted_content.append("## 📚 知识点标题列表")
            formatted_content.append("以下是在视频中识别出的主要知识点标题，请在Summary中适当引用：")
            for i, title in enumerate(knowledge_point_titles, 1):
                formatted_content.append(f"{i}. **{title}**")
            formatted_content.append("")  # 空行分隔
        
        # 详细的分段内容
        formatted_content.append("## 📖 详细分段内容")
        
        for i, segment in enumerate(segments, 1):
            # 提取关键信息
            title = segment.get('title', f'片段{i}')
            description = segment.get('description', '无描述')
            key_phrase = segment.get('key_phrase', '无关键内容')
            category = segment.get('category', '未分类')
            difficulty = segment.get('difficulty', '中等')
            importance = segment.get('importance', 'medium')
            start_time = segment.get('start_time', '00:00:00')
            end_time = segment.get('end_time', '00:00:00')
            
            # 根据语言动态生成标签
            if language.lower() in ["english", "en"]:
                time_range_label = "**Time Range**"
                category_label = "**Category**"
                difficulty_label = "**Difficulty**"
                importance_label = "**Importance**"
                description_label = "**Description**"
                key_info_label = "**Key Information**"
                segment_label = f"### Segment {i}"
            else:
                time_range_label = "**时间范围**"
                category_label = "**类别**"
                difficulty_label = "**难度**"
                importance_label = "**重要性**"
                description_label = "**内容描述**"
                key_info_label = "**关键信息**"
                segment_label = f"### 分段 {i}"
            
            # 格式化为结构化文本
            segment_text = f"""
{segment_label}: {title}
- {time_range_label}: {start_time} - {end_time}
- {category_label}: {category}
- {difficulty_label}: {difficulty}
- {importance_label}: {importance}
- {description_label}: {description}
- {key_info_label}: {key_phrase}
"""
            formatted_content.append(segment_text)
        
        return "\n".join(formatted_content)
    
    def _create_timestamp_mapping(self, segments: List[Dict]) -> Dict[str, Dict]:
        """
        创建知识点标题与时间戳的映射关系
        
        Args:
            segments: 视频分段列表
            
        Returns:
            Dict: 时间戳映射字典
        """
        timestamp_mapping = {}
        
        for segment in segments:
            title = segment.get('title', '')
            if title:
                timestamp_mapping[title] = {
                    'start_time': segment.get('start_time', '00:00:00'),
                    'end_time': segment.get('end_time', '00:00:00'),
                    'start_seconds': segment.get('start_seconds', 0),
                    'end_seconds': segment.get('end_seconds', 0),
                    'duration_seconds': segment.get('duration_seconds', 0),
                    'description': segment.get('description', ''),
                    'key_phrase': segment.get('key_phrase', ''),
                    'category': segment.get('category', ''),
                    'importance': segment.get('importance', ''),
                    'difficulty': segment.get('difficulty', '')
                }
        
        return timestamp_mapping
    
    def _extract_structured_knowledge_points(self, segments: List[Dict], language: str = "中文") -> List[Dict]:
        """
        从分段信息中提取结构化的知识点数据
        
        Args:
            segments: 视频分段列表
            language: 语言（中文/English）
            
        Returns:
            List[Dict]: 结构化知识点列表
        """
        knowledge_points = []
        
        for i, segment in enumerate(segments):
            # 根据语言设置默认标题
            if language.lower() in ["english", "en"]:
                default_title = f"Knowledge Point {i+1}"
                default_description = "No description"
                default_category = "Uncategorized"
                default_difficulty = "Intermediate"
            else:
                default_title = f"知识点{i+1}"
                default_description = "无描述"
                default_category = "未分类"
                default_difficulty = "中等"
            
            knowledge_point = {
                'id': segment.get('id', f'kp_{i+1:03d}'),
                'title': segment.get('title', default_title),
                'description': segment.get('description', default_description),
                'category': segment.get('category', default_category),
                'difficulty': segment.get('difficulty', default_difficulty),
                'importance': segment.get('importance', 'medium'),
                'start_time': segment.get('start_time', '00:00:00'),
                'end_time': segment.get('end_time', '00:00:00'),
                'duration_seconds': segment.get('duration_seconds', 0),
                'key_concepts': segment.get('key_phrase', '').split('，') if segment.get('key_phrase') else []
            }
            knowledge_points.append(knowledge_point)
        
        return knowledge_points
    
    def _get_language_header_structure(self, language: str, lecture_title: str) -> str:
        """
        根据语言生成文档结构
        
        Args:
            language: 语言（中文/English）
            lecture_title: 课程标题
            
        Returns:
            str: 文档结构字符串
        """
        if language.lower() in ["english", "en"]:
            return f"""## Course Summary: {lecture_title}
## **Course Overview**
## **Main Knowledge Points**
## **Important Formulas or Definitions**
## **Key Concept Explanations**"""
        else:
            return f"""## 课程总结: {lecture_title}
## **课程概览**
## **主要知识点**
## **重要公式或定义**
## **关键概念解释**"""
    
    def _create_empty_result(self, error_message: str) -> Dict:
        """
        创建空的结果字典（用于错误情况）
        
        Args:
            error_message: 错误信息
            
        Returns:
            Dict: 空结果字典
        """
        return {
            "summary": f"Summary生成失败: {error_message}",
            "timestamp_mapping": {},
            "knowledge_points": [],
            "segments_count": 0,
            "generation_time": datetime.now().isoformat(),
            "quality_check": {"overall_quality": False},
            "success": False,
            "error": error_message
        }
    
    def validate_summary_quality(self, summary: str, language: str = "中文") -> Dict[str, bool]:
        """
        验证生成的Summary质量 - 【修复后版本，更健壮】
        
        Args:
            summary: 生成的Summary文档
            language: 语言（中文/English）
            
        Returns:
            Dict: 质量验证结果
        """
        # 转换为小写以便进行不区分大小写的比较
        summary_lower = summary.lower()
        
        # 定义需要检查的关键词
        if language.lower() in ["english", "en"]:
            checks = {
                'has_course_overview': r'##\s*(\*\*)*course overview(\*\*)*',
                'has_main_knowledge': r'##\s*(\*\*)*main knowledge points(\*\*)*',
                'has_formulas': r'##\s*(\*\*)*important formulas', # 匹配开头即可
                'has_key_concepts': r'##\s*(\*\*)*key concept explanations(\*\*)*',
                'has_title': r'course summary:'
            }
        else:
            checks = {
                'has_course_overview': r'##\s*(\*\*)*课程概览(\*\*)*',
                'has_main_knowledge': r'##\s*(\*\*)*主要知识点(\*\*)*',
                'has_formulas': r'##\s*(\*\*)*重要公式或定义(\*\*)*',
                'has_key_concepts': r'##\s*(\*\*)*关键概念解释(\*\*)*',
                'has_title': r'课程总结:'
            }
        
        validation_result = {}
        for key, pattern in checks.items():
            # 使用正则表达式搜索，忽略大小写和可选的粗体标记
            if re.search(pattern, summary_lower):
                validation_result[key] = True
            else:
                validation_result[key] = False
                print(f"⚠️ 质量验证失败：未找到 '{key}' (模式: {pattern})")

        # 验证最小长度
        validation_result['min_length_ok'] = len(summary) > 200 # 可适当调整长度阈值

        validation_result['overall_quality'] = all(validation_result.values())
        
        return validation_result
    
    def get_summary_statistics(self, summary: str, knowledge_points: List[Dict]) -> Dict:
        """
        获取Summary的统计信息
        
        Args:
            summary: Summary文档
            knowledge_points: 知识点列表
            
        Returns:
            Dict: 统计信息
        """
        return {
            'summary_length': len(summary),
            'word_count': len(summary.split()),
            'knowledge_points_count': len(knowledge_points),
            'sections_count': summary.count('##'),
            'formulas_count': summary.count('**') // 2,  # 粗体项目数量的估计
            'has_math_symbols': any(symbol in summary for symbol in ['π', '√', '²', '³', '°', '±'])
        }
    
    # 🆕 新增方法：Prompt管理功能
    def update_prompt(self, prompt_name: str, new_content: str):
        """
        更新Prompt模板内容
        
        Args:
            prompt_name: Prompt名称
            new_content: 新的Prompt内容
        """
        self.prompt_manager.create_prompt_template(prompt_name, new_content)
        print(f"✅ 已更新Prompt: {prompt_name}")
    
    def reload_prompts(self):
        """重新加载所有Prompt模板"""
        self.prompt_manager.clear_cache()
        print("🔄 已重新加载所有Prompt模板")
    
    def get_prompt_info(self) -> Dict:
        """获取当前使用的Prompt信息"""
        return self.prompt_manager.get_prompt_info("summary_integration")


# 🆕 新增：创建默认Prompt文件的工具函数
def create_default_prompts(prompts_dir: str = "./prompts"):
    """
    创建默认的Prompt模板文件
    
    Args:
        prompts_dir: Prompt文件目录
    """
    import os
    os.makedirs(prompts_dir, exist_ok=True)
    
    # Summary整合Prompt（已经有了，这里展示如何程序化创建）
    summary_prompt = """# Summary整合Prompt模板

你是一个专业的教育内容编辑。请基于以下视频分段内容，生成一个完整的、高可读性的课程Summary文档。

## 要求格式（严格按照以下结构）：

## Course Summary: {lecture_title}

## **Course Overview**
[2-3句话概括整个课程的主要内容和目标]

## **Main Knowledge Points**
[按逻辑顺序组织知识点...]

## 分段内容数据：
{segments_content}

请生成完整的Summary文档："""
    
    # 如果文件不存在，则创建
    summary_file = os.path.join(prompts_dir, "summary_integration.md")
    if not os.path.exists(summary_file):
        with open(summary_file, 'w', encoding='utf-8') as f:
            f.write(summary_prompt)
        print(f"✅ 已创建默认Prompt: {summary_file}")
    else:
        print(f"📁 Prompt文件已存在: {summary_file}")


# 使用示例和测试函数
def test_updated_summary_integrator():
    """测试更新后的Summary整合器"""
    
    # 确保有默认Prompt文件
    create_default_prompts()
    
    # 注意：实际使用时需要提供真实的API key
    # integrator = SummaryIntegrator("your_api_key_here")
    
    print("✅ 更新后的SummaryIntegrator类定义完成")
    print("📁 Prompt模板已分离到独立文件")
    print("🔧 现在可以通过修改.md文件来调优Prompt")


if __name__ == "__main__":
    test_updated_summary_integrator()