"""
Vercel-optimized VideoProcessor with improved cache handling
针对Vercel部署优化的视频处理器，改进缓存处理逻辑
"""

import hashlib
import os
import tempfile
import json
from datetime import datetime
import re
from typing import List, Dict, Tuple, Optional
from core.summary_integrator import SummaryIntegrator
from core.prompt_manager import PromptManager


class VideoProcessor:
    def __init__(self, api_key: str, cache_only_mode=False):
        """初始化视频处理器 - Vercel优化版本"""
        self.cache_only_mode = cache_only_mode
        
        # Vercel环境检测
        self.is_vercel = os.environ.get('VERCEL') == '1'
        
        # 配置缓存目录
        if self.is_vercel:
            # Vercel环境：使用项目根目录下的静态缓存文件
            self.cache_dir = os.path.join(os.getcwd(), "data", "cache")
        else:
            # 本地开发：使用相对路径
            self.cache_dir = "./data/cache"
        
        # 确保缓存目录存在（本地开发时）
        if not self.is_vercel:
            os.makedirs(self.cache_dir, exist_ok=True)
        
        print(f"🏗️ 环境检测: {'Vercel' if self.is_vercel else 'Local'}")
        print(f"📁 缓存目录: {self.cache_dir}")
        
        # 初始化其他组件
        try:
            import google.generativeai as genai
            genai.configure(api_key=api_key)
            self.model = genai.GenerativeModel('gemini-2.5-pro')
            self.summary_integrator = SummaryIntegrator(api_key, prompts_dir="./prompts")
            self.prompt_manager = PromptManager("./prompts")
        except Exception as e:
            print(f"⚠️ 初始化API组件失败: {e}")
            # 在缓存模式下，可以继续运行
            if not cache_only_mode:
                raise e
        
        self.processing_log = {
            "token_count": 0,
            "segments_count": 0,
            "segments_details": [],
            "timestamp_matches": [],
            "processing_time": 0,
            "api_calls": 0,
            "transcription_length": 0,
            "content_type": "",
            "content_subtype": "",
            "confidence": 0.0,
            "environment": "vercel" if self.is_vercel else "local",
            "cache_mode": cache_only_mode
        }
        
        # 验证和列出可用的缓存文件
        self._validate_cache_setup()

    def _validate_cache_setup(self):
        """验证缓存设置和可用文件"""
        print(f"\n🔍 验证缓存设置...")
        print(f"📂 缓存目录: {self.cache_dir}")
        print(f"📂 目录存在: {os.path.exists(self.cache_dir)}")
        
        if os.path.exists(self.cache_dir):
            cache_files = self._get_available_cache_files()
            print(f"📄 找到 {len(cache_files)} 个缓存文件:")
            for i, cache_file in enumerate(cache_files, 1):
                file_path = os.path.join(self.cache_dir, cache_file)
                file_size = os.path.getsize(file_path) / 1024  # KB
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                print(f"  {i}. {cache_file}")
                print(f"     大小: {file_size:.1f}KB")
                print(f"     修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 验证文件内容
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        cache_data = json.load(f)
                    has_transcription = 'transcription' in cache_data
                    has_analysis = 'analysis' in cache_data
                    print(f"     内容完整性: 转录={'✅' if has_transcription else '❌'}, 分析={'✅' if has_analysis else '❌'}")
                except Exception as e:
                    print(f"     ⚠️ 文件读取错误: {e}")
        else:
            print("❌ 缓存目录不存在")

    def _get_available_cache_files(self) -> List[str]:
        """获取所有可用的缓存文件"""
        if not os.path.exists(self.cache_dir):
            return []
        
        try:
            import glob
            pattern = os.path.join(self.cache_dir, "*_analysis.json")
            cache_files = glob.glob(pattern)
            return [os.path.basename(f) for f in cache_files]
        except Exception as e:
            print(f"⚠️ 扫描缓存文件失败: {e}")
            return []

    def _find_best_cache_file(self, lecture_title: str) -> Optional[str]:
        """
        根据课程标题找到最匹配的缓存文件
        """
        cache_files = self._get_available_cache_files()
        
        if not cache_files:
            print("❌ 没有找到任何缓存文件")
            return None
        
        print(f"🔍 搜索最匹配的缓存文件，课程标题: {lecture_title}")
        
        # 策略1: 完全匹配标题
        if lecture_title and lecture_title != "Untitled Video":
            for cache_file in cache_files:
                if lecture_title.lower().replace(" ", "_") in cache_file.lower():
                    print(f"✅ 找到标题匹配的缓存文件: {cache_file}")
                    return os.path.join(self.cache_dir, cache_file)
        
        # 策略2: 使用最新的缓存文件
        if cache_files:
            latest_file = None
            latest_time = 0
            
            for cache_file in cache_files:
                file_path = os.path.join(self.cache_dir, cache_file)
                try:
                    mtime = os.path.getmtime(file_path)
                    if mtime > latest_time:
                        latest_time = mtime
                        latest_file = file_path
                except Exception as e:
                    print(f"⚠️ 无法获取文件时间: {cache_file}, {e}")
                    continue
            
            if latest_file:
                print(f"✅ 使用最新的缓存文件: {os.path.basename(latest_file)}")
                return latest_file
        
        # 策略3: 使用第一个可用文件
        first_file = os.path.join(self.cache_dir, cache_files[0])
        print(f"✅ 使用第一个可用缓存文件: {cache_files[0]}")
        return first_file

    def _load_cache_data(self, cache_file_path: str) -> Optional[Tuple[Dict, Dict]]:
        """
        安全地加载缓存数据
        """
        if not os.path.exists(cache_file_path):
            print(f"❌ 缓存文件不存在: {cache_file_path}")
            return None
        
        try:
            print(f"📖 正在读取缓存文件: {os.path.basename(cache_file_path)}")
            
            with open(cache_file_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 验证缓存数据结构
            if 'transcription' not in cache_data:
                print("❌ 缓存文件缺少transcription数据")
                return None
                
            if 'analysis' not in cache_data:
                print("❌ 缓存文件缺少analysis数据")
                return None
            
            transcription = cache_data['transcription']
            analysis = cache_data['analysis']
            
            # 验证关键字段
            if not transcription.get('text'):
                print("⚠️ 转录文本为空")
            
            if not analysis.get('content_segments'):
                print("⚠️ 没有找到内容片段")
            
            print(f"✅ 成功加载缓存数据:")
            print(f"  - 转录文本长度: {len(transcription.get('text', ''))} 字符")
            print(f"  - 内容片段数量: {len(analysis.get('content_segments', []))}")
            print(f"  - 内容类型: {analysis.get('content_type', 'unknown')}")
            
            return transcription, analysis
            
        except json.JSONDecodeError as e:
            print(f"❌ 缓存文件JSON格式错误: {e}")
            return None
        except Exception as e:
            print(f"❌ 加载缓存文件失败: {e}")
            return None

    def _process_from_cache_only(self, lecture_title: str, language: str = "中文") -> Dict:
        """
        缓存模式：直接使用预处理的缓存数据生成Summary - 改进版本
        """
        from datetime import datetime
        start_time = datetime.now()
        
        print("🔧 缓存模式：加载预处理的缓存数据...")
        
        # 查找最佳缓存文件
        cache_file_path = self._find_best_cache_file(lecture_title)
        
        if not cache_file_path:
            error_msg = "缓存模式：未找到可用的缓存文件"
            print(f"❌ {error_msg}")
            
            # 提供调试信息
            debug_info = {
                "cache_directory": self.cache_dir,
                "directory_exists": os.path.exists(self.cache_dir),
                "available_files": [],
                "search_title": lecture_title
            }
            
            if os.path.exists(self.cache_dir):
                try:
                    debug_info["available_files"] = os.listdir(self.cache_dir)
                except Exception as e:
                    debug_info["directory_read_error"] = str(e)
            
            return {
                "error": error_msg,
                "success": False,
                "debug_info": debug_info,
                "processor_version": "cache_only_failed"
            }
        
        # 加载缓存数据
        cache_result = self._load_cache_data(cache_file_path)
        
        if not cache_result:
            return {
                "error": "缓存模式：缓存文件数据损坏或无法读取",
                "success": False,
                "cache_file": os.path.basename(cache_file_path),
                "processor_version": "cache_only_failed"
            }
        
        transcription, analysis = cache_result
        
        # 更新处理日志
        self.processing_log.update({
            'segments_count': len(analysis.get('content_segments', [])),
            'content_type': analysis.get('content_type', ''),
            'content_subtype': analysis.get('content_subtype', ''),
            'confidence': analysis.get('confidence', 0.0),
            'transcription_length': len(transcription.get('text', '')),
            'cache_used': True,
            'cache_file': os.path.basename(cache_file_path)
        })
        
        # 生成Summary
        print("📄 正在生成Summary...")
        try:
            summary_result = self._generate_summary_safely(
                analysis, transcription, lecture_title, language
            )
            
            integrated_summary = summary_result.get("summary", "")
            timestamp_mapping = summary_result.get("timestamp_mapping", {})
            knowledge_points = summary_result.get("knowledge_points", [])
            
        except Exception as e:
            print(f"⚠️ Summary生成失败: {e}")
            # 生成备用Summary
            integrated_summary, timestamp_mapping, knowledge_points = self._create_fallback_summary(
                analysis, lecture_title
            )
        
        # 生成知识点（如果为空）
        if not knowledge_points:
            knowledge_points = self._extract_knowledge_points_from_analysis(analysis)
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        self.processing_log["processing_time"] = processing_time
        
        print(f"✅ 缓存模式处理完成，耗时: {processing_time:.2f}秒")
        
        return {
            "transcription": transcription,
            "analysis": analysis,
            "notes": "缓存模式：分段笔记功能暂未实现",
            "summary": "缓存模式：分段摘要功能暂未实现",
            "summary_with_timestamps": "缓存模式：带时间戳的分段摘要功能暂未实现",
            
            # 新增整合Summary相关字段
            "integrated_summary": integrated_summary,
            "timestamp_mapping": timestamp_mapping,
            "knowledge_points": knowledge_points,
            "summary_statistics": {
                "summary_length": len(integrated_summary),
                "knowledge_points_count": len(knowledge_points),
                "segments_count": len(analysis.get('content_segments', [])),
                "processing_mode": "cache_only"
            },
            
            # 缓存模式特有字段
            "cache_used": True,
            "cache_file": os.path.basename(cache_file_path),
            "processor_version": "cache_only",
            "processing_mode": "cache_only",
            
            # 前端期望的字段
            "lecture_title": lecture_title,
            "language": language,
            "processing_log": self.processing_log,
            "success": True
        }

    def _generate_summary_safely(self, analysis: Dict, transcription: Dict, 
                                lecture_title: str, language: str) -> Dict:
        """
        安全地生成Summary，带有错误处理
        """
        try:
            if hasattr(self, 'summary_integrator') and self.summary_integrator:
                return self.summary_integrator.generate_summary(
                    analysis, transcription, lecture_title, language
                )
            else:
                print("⚠️ SummaryIntegrator未初始化，使用备用方案")
                return self._create_simple_summary(analysis, lecture_title, language)
                
        except Exception as e:
            print(f"⚠️ Summary生成异常: {e}")
            return self._create_simple_summary(analysis, lecture_title, language)

    def _create_simple_summary(self, analysis: Dict, lecture_title: str, language: str) -> Dict:
        """
        创建简单的Summary（当AI生成失败时的备用方案）
        """
        segments = analysis.get('content_segments', [])
        
        if language.lower() in ["english", "en"]:
            summary = f"# Course Summary: {lecture_title}\n\n"
            summary += "## Course Overview\n"
            summary += f"This video contains {len(segments)} main content segments covering various topics.\n\n"
            summary += "## Main Knowledge Points\n"
        else:
            summary = f"# 课程总结: {lecture_title}\n\n"
            summary += "## 课程概览\n"
            summary += f"本视频包含{len(segments)}个主要内容片段，涵盖多个主题。\n\n"
            summary += "## 主要知识点\n"
        
        for i, segment in enumerate(segments, 1):
            title = segment.get('title', f'片段{i}')
            description = segment.get('description', '暂无描述')
            summary += f"{i}. **{title}**: {description}\n"
        
        return {
            "summary": summary,
            "timestamp_mapping": {},
            "knowledge_points": []
        }

    def _create_fallback_summary(self, analysis: Dict, lecture_title: str) -> Tuple[str, Dict, List]:
        """
        创建备用Summary、时间戳映射和知识点
        """
        segments = analysis.get('content_segments', [])
        
        # 创建简单的文本摘要
        summary = f"# 课程总结: {lecture_title}\n\n"
        summary += "## 课程概览\n"
        summary += f"本视频包含{len(segments)}个主要内容片段。由于技术原因，无法生成详细的AI总结。\n\n"
        summary += "## 主要内容片段\n"
        
        timestamp_mapping = {}
        knowledge_points = []
        
        for i, segment in enumerate(segments, 1):
            title = segment.get('title', f'知识点{i}')
            description = segment.get('description', '暂无描述')
            
            summary += f"{i}. **{title}**: {description}\n"
            
            # 创建时间戳映射
            if title:
                timestamp_mapping[title] = {
                    'start_time': segment.get('start_time', '00:00:00'),
                    'end_time': segment.get('end_time', '00:00:00'),
                    'start_seconds': segment.get('start_seconds', 0),
                    'end_seconds': segment.get('end_seconds', 0),
                    'duration_seconds': segment.get('duration_seconds', 0),
                    'description': description
                }
            
            # 创建知识点
            knowledge_points.append({
                'id': f'kp_{i:03d}',
                'title': title,
                'description': description,
                'start_time': segment.get('start_time', '00:00:00'),
                'end_time': segment.get('end_time', '00:00:00'),
                'category': segment.get('category', '概念'),
                'difficulty': segment.get('difficulty', '基础'),
                'importance': segment.get('importance', 'medium')
            })
        
        summary += "\n请查看下方的知识点列表获取详细信息。"
        
        return summary, timestamp_mapping, knowledge_points

    def _extract_knowledge_points_from_analysis(self, analysis: Dict) -> List[Dict]:
        """
        从analysis中提取知识点列表
        """
        segments = analysis.get('content_segments', [])
        knowledge_points = []
        
        for i, segment in enumerate(segments):
            kp = {
                'id': segment.get('id', f'kp_{i+1:03d}'),
                'title': segment.get('title', f'知识点{i+1}'),
                'description': segment.get('description', '暂无描述'),
                'start_time': segment.get('start_time', '00:00:00'),
                'end_time': segment.get('end_time', '00:00:00'),
                'key_phrase': segment.get('key_phrase', ''),
                'importance': segment.get('importance', 'medium'),
                'category': segment.get('category', '概念'),
                'difficulty': segment.get('difficulty', '基础'),
                'start_seconds': segment.get('start_seconds', 0),
                'end_seconds': segment.get('end_seconds', 0),
                'duration_seconds': segment.get('duration_seconds', 0)
            }
            knowledge_points.append(kp)
        
        return knowledge_points

    def process_video(self, video_path: str, lecture_title: str, language: str = "中文") -> Dict:
        """
        处理视频的完整流程 - Vercel优化版本
        """
        print("🚀 开始视频处理流程...")
        print(f"标题: {lecture_title}")
        print(f"缓存模式: {'启用' if self.cache_only_mode else '禁用'}")
        print(f"环境: {'Vercel' if self.is_vercel else 'Local'}")
        
        # Vercel环境或缓存模式：直接使用缓存数据
        if self.cache_only_mode or self.is_vercel:
            return self._process_from_cache_only(lecture_title, language)
        
        # 本地环境：正常处理流程
        # ... (保留原有的完整处理逻辑)
        return {"error": "本地完整处理模式暂未在此版本中实现"}

    # 从原文件保留的其他重要方法
    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> str:
        """从视频中提取音频"""
        try:
            import ffmpeg
            (
                ffmpeg
                .input(video_path)
                .output(output_audio_path, acodec='pcm_s16le', ac=1, ar='16k')
                .overwrite_output()
                .run(quiet=True)
            )
            return output_audio_path
        except Exception as e:
            print(f"❌ 音频提取失败: {e}")
            raise e

    def _format_timestamp(self, seconds: float) -> str:
        """将秒数转换为HH:MM:SS格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def transcribe_video_with_timestamps(self, video_path: str, model_size: str = "base") -> Dict:
        """使用Whisper转录视频并获取时间戳"""
        try:
            import whisper
            model = whisper.load_model(model_size)
            result = model.transcribe(video_path, word_timestamps=True)
            
            # 记录转录信息
            self._log_processing_info("transcription", {
                "text_length": len(result.get('text', '')),
                "segments_count": len(result.get('segments', [])),
                "model_size": model_size
            })
            return result
        except Exception as e:
            print(f"❌ 视频转录失败: {e}")
            raise e

    def _find_matching_timestamps(self, start_phrase: str, end_phrase: str, key_phrase: str, transcription: Dict) -> Dict:
        """基于关键句子精确匹配时间戳 - 简化版本"""
        try:
            segments = transcription.get('segments', [])
            if not segments:
                return {"start_time": "00:00:00", "end_time": "00:00:00", "duration_seconds": 0}
            
            # 简化的时间戳匹配逻辑
            start_time = segments[0]['start']
            end_time = segments[-1]['end']
            
            # 这里可以添加更复杂的匹配逻辑，但为了Vercel部署简化处理
            duration = end_time - start_time
            
            return {
                "start_time": self._format_timestamp(start_time),
                "end_time": self._format_timestamp(end_time),
                "duration_seconds": duration,
                "start_seconds": start_time,
                "end_seconds": end_time,
                "match_method": "simplified"
            }
            
        except Exception as e:
            print(f"❌ 时间戳匹配失败: {e}")
            return {"start_time": "00:00:00", "end_time": "00:00:00", "duration_seconds": 0}

    def analyze_video_content(self, transcription: Dict, lecture_title: str) -> Dict:
        """分析视频内容 - Vercel优化版本"""
        if self.cache_only_mode or self.is_vercel:
            print("⚠️ 缓存模式下跳过视频内容分析")
            return {
                "content_type": "未知",
                "content_subtype": "未知",
                "confidence": 0.0,
                "content_segments": [],
                "summary": "缓存模式下跳过分析"
            }
        
        # 如果不是缓存模式，执行正常的分析流程
        try:
            prompt = self.prompt_manager.get_prompt(
                "video_analysis",
                lecture_title=lecture_title,
                transcription_text=transcription['text']
            )
            
            response = self.model.generate_content(prompt)
            
            if not response or not hasattr(response, 'text') or not response.text:
                raise Exception("API响应为空或无效")
            
            # 解析结构化响应
            result = self._parse_structured_response(response.text)
            return result
            
        except Exception as e:
            print(f"❌ 视频内容分析失败: {e}")
            return {
                "content_type": "分析失败",
                "content_subtype": "分析失败",
                "confidence": 0.0,
                "content_segments": [],
                "summary": f"分析失败: {str(e)}"
            }

    def _parse_structured_response(self, text: str) -> Dict:
        """解析结构化文本响应"""
        # 保留原有的解析逻辑
        result = {
            "content_type": "未知",
            "content_subtype": "未知", 
            "confidence": 0.0,
            "content_segments": [],
            "summary": ""
        }
        
        lines = text.strip().split('\n')
        current_segment = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # 解析内容类型
            if line.startswith('内容类型:') or line.startswith('Content Type:'):
                result["content_type"] = line.split(':', 1)[1].strip()
            elif line.startswith('内容子类型:') or line.startswith('Content Subtype:'):
                result["content_subtype"] = line.split(':', 1)[1].strip()
            elif line.startswith('置信度:') or line.startswith('Confidence:'):
                try:
                    confidence_str = line.split(':', 1)[1].strip()
                    result["confidence"] = float(confidence_str)
                except:
                    result["confidence"] = 0.0
            elif line.startswith('总结:') or line.startswith('Summary:'):
                result["summary"] = line.split(':', 1)[1].strip()
            elif (line.startswith('片段') or line.startswith('Segment')) and ':' in line:
                # 开始新片段
                if current_segment:
                    result["content_segments"].append(current_segment)
                current_segment = {
                    "id": f"seg_{len(result['content_segments'])+1:03d}",
                    "title": "",
                    "description": "",
                    "start_phrase": "",
                    "end_phrase": "",
                    "key_phrase": "",
                    "importance": "",
                    "category": "",
                    "difficulty": ""
                }
            elif current_segment and ':' in line:
                # 解析片段属性
                key, value = line.split(':', 1)
                key = key.strip()
                value = value.strip()
                
                if key in ['标题', 'Title']:
                    current_segment["title"] = value
                elif key in ['描述', 'Description']:
                    current_segment["description"] = value
                elif key in ['开始句', 'Start Sentence']:
                    current_segment["start_phrase"] = value
                elif key in ['结束句', 'End Sentence']:
                    current_segment["end_phrase"] = value
                elif key in ['关键句', 'Key Sentence']:
                    current_segment["key_phrase"] = value
                elif key in ['重要性', 'Importance']:
                    current_segment["importance"] = value
                elif key in ['类别', 'Category']:
                    current_segment["category"] = value
                elif key in ['难度', 'Difficulty']:
                    current_segment["difficulty"] = value
        
        # 添加最后一个片段
        if current_segment:
            result["content_segments"].append(current_segment)
            
        return result

    def _log_processing_info(self, stage: str, info: Dict):
        """记录处理信息"""
        print(f"📝 [{stage}] {info}")
        if stage == "transcription":
            self.processing_log["transcription_length"] = info.get("text_length", 0)
        elif stage == "content_analysis":
            self.processing_log["token_count"] = info.get("token_count", 0)
            self.processing_log["api_calls"] += 1
            self.processing_log["content_type"] = info.get("content_type", "")
            self.processing_log["content_subtype"] = info.get("content_subtype", "")
            self.processing_log["confidence"] = info.get("confidence", 0.0)

    def clear_cache(self, lecture_title: str = None):
        """清理缓存文件"""
        if self.is_vercel:
            print("⚠️ Vercel环境下无法清理缓存文件（只读文件系统）")
            return
        
        if lecture_title:
            # 清理特定课程的缓存
            pattern = f"*{lecture_title}*_analysis.json"
            import glob
            cache_files = glob.glob(os.path.join(self.cache_dir, pattern))
            for cache_file in cache_files:
                os.remove(cache_file)
                print(f"🗑️ 已删除缓存: {cache_file}")
        else:
            # 清理所有缓存
            import glob
            cache_files = glob.glob(os.path.join(self.cache_dir, "*_analysis.json"))
            for cache_file in cache_files:
                os.remove(cache_file)
                print(f"🗑️ 已删除缓存: {cache_file}")

    def list_cache_files(self):
        """列出所有缓存文件及其详细信息"""
        cache_files = self._get_available_cache_files()
        print("📂 缓存文件列表:")
        print(f"📁 缓存目录: {self.cache_dir}")
        print(f"📊 文件数量: {len(cache_files)}")
        
        if not cache_files:
            print("❌ 没有找到任何缓存文件")
            return
        
        for i, cache_file in enumerate(cache_files, 1):
            file_path = os.path.join(self.cache_dir, cache_file)
            try:
                file_size = os.path.getsize(file_path) / 1024  # KB
                mtime = datetime.fromtimestamp(os.path.getmtime(file_path))
                
                print(f"  {i}. {cache_file}")
                print(f"     大小: {file_size:.1f}KB")
                print(f"     修改时间: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")
                
                # 验证文件完整性
                with open(file_path, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                
                has_transcription = 'transcription' in cache_data and cache_data['transcription'].get('text')
                has_analysis = 'analysis' in cache_data and cache_data['analysis'].get('content_segments')
                
                print(f"     完整性: {'✅' if has_transcription and has_analysis else '❌'}")
                
                if has_analysis:
                    segments_count = len(cache_data['analysis'].get('content_segments', []))
                    content_type = cache_data['analysis'].get('content_type', 'unknown')
                    print(f"     内容: {segments_count}个片段, 类型: {content_type}")
                
            except Exception as e:
                print(f"     ❌ 错误: {e}")
        
        print()