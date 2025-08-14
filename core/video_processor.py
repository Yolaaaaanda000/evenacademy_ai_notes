import hashlib
import os
import tempfile
import whisper
import ffmpeg
import google.generativeai as genai
import json
from datetime import datetime
import re
from typing import List, Dict, Tuple, Optional
from core.summary_integrator import SummaryIntegrator  # 🆕 优化1: 导入新的Summary整合器
from core.prompt_manager import PromptManager  # 🆕 添加PromptManager导入


class VideoProcessor:
    def __init__(self, api_key: str):
        """初始化视频处理器"""
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-2.5-pro')
        self.summary_integrator = SummaryIntegrator(api_key, prompts_dir="./prompts")  # 🆕 优化2: 初始化Summary整合器

        # 🆕 初始化Prompt管理器
        self.prompt_manager = PromptManager("./prompts")

        # 🆕 优化3: 缓存目录设置
        self.cache_dir = "./data/cache"
        os.makedirs(self.cache_dir, exist_ok=True)
        
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
            "confidence": 0.0
        }
            # 🆕 验证必需的Prompt文件
        self._validate_prompts()
    
    def _validate_prompts(self):
        """验证必需的Prompt文件是否存在"""
        required_prompts = {
            "video_analysis": ["lecture_title", "transcription_text"]
        }
        
        for prompt_name, required_params in required_prompts.items():
            validation = self.prompt_manager.validate_prompt(prompt_name, required_params)
            
            if not validation['exists']:
                print(f"⚠️ 缺少Prompt文件: {prompt_name}.md")
                # 🆕 自动创建默认Prompt文件
                self._create_default_video_analysis_prompt()
            elif not validation['valid']:
                print(f"⚠️ Prompt文件 {prompt_name}.md 缺少必需参数: {validation['missing_params']}")
    
    def _create_default_video_analysis_prompt(self):
        """创建默认的视频分析Prompt"""
        default_prompt = """# 视频内容分析Prompt模板

你是一个专业的课程内容分析助手。请分析以下视频转录内容，并完成以下任务：

## 分析要求：

### 1. 内容类型判断
请判断视频内容类型：
- **概念讲解**: 新知识点的引入、定义、原理说明
- **题目复习**: 习题讲解、解题步骤、答案分析
- **混合内容**: 既有概念讲解又有题目练习

### 2. 内容切片识别
识别视频中的重要内容片段，每个片段应该：
- 有明确的开始和结束
- 包含完整的一个知识点或题目，并且列出所有的解题步骤
- 能够独立理解

### 3. 精确时间戳匹配
为每个内容片段提供：
- **开始句**: 片段的第一句话（用于精确定位）
- **结束句**: 片段的最后一句话（用于确定边界）
- **关键句**: 最能代表该片段核心内容的句子

视频标题：{lecture_title}

转录内容：
{transcription_text}

请以结构化文本格式返回分析结果，格式如下：

内容类型: [概念讲解/题目复习/混合内容]
内容子类型: [新概念引入/公式推导/例题讲解/习题解答/总结回顾]
置信度: [0.95]

片段1:
标题: [片段标题]
描述: [片段内容描述]
开始句: [片段开始的第一句话]
结束句: [片段结束的最后一句话]
关键句: [最能代表该片段核心的句子]
重要性: [high/medium/low]
类别: [概念定义/公式推导/例题讲解/解题步骤/总结回顾]
难度: [基础/中等/困难]

片段2:
标题: [片段标题]
描述: [片段内容描述]
开始句: [片段开始的第一句话]
结束句: [片段结束的最后一句话]
关键句: [最能代表该片段核心的句子]
重要性: [high/medium/low]
类别: [概念定义/公式推导/例题讲解/解题步骤/总结回顾]
难度: [基础/中等/困难]

总结: [视频内容简要总结]

## 重要说明：
1. **开始句** 和 **结束句** 必须是从转录文本中提取的实际句子，句子要完整且准确
2. **关键句** 应该是最能代表该片段核心内容的句子，包含重要的关键词
3. 不要包含时间戳，时间戳将通过后续精确匹配获得
4. 每个片段应该有明确的边界，便于后续精确定位
5. 开始句和结束句应该包含足够的词汇，便于在转录文本中精确定位
6. 请严格按照上述格式输出，不要使用JSON格式
"""
        
        self.prompt_manager.create_prompt_template("video_analysis", default_prompt)
        print("✅ 已创建默认的视频分析Prompt")

    # 🆕 优化4: 新增缓存相关方法
    def _get_file_hash(self, file_path: str) -> str:
        """获取文件hash值，用于缓存key"""
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()[:12]  # 取前12位即可
    
    def _get_cache_file_path(self, video_path: str, lecture_title: str) -> str:
        """获取缓存文件路径"""
        file_hash = self._get_file_hash(video_path)
        safe_title = ''.join(c for c in lecture_title if c.isalnum() or c in ('_', '-'))
        cache_filename = f"{safe_title}_{file_hash}_analysis.json"
        return os.path.join(self.cache_dir, cache_filename)
    
    def _save_analysis_cache(self, video_path: str, lecture_title: str, transcription: Dict, analysis: Dict) -> str:
        """保存转录和分析结果到缓存"""
        cache_file = self._get_cache_file_path(video_path, lecture_title)
        
        cache_data = {
            "cache_info": {
                "video_path": video_path,
                "lecture_title": lecture_title,
                "file_hash": self._get_file_hash(video_path),
                "created_time": datetime.now().isoformat(),
                "cache_version": "1.0"
            },
            "transcription": transcription,
            "analysis": analysis
        }
        
        with open(cache_file, 'w', encoding='utf-8') as f:
            json.dump(cache_data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 分析结果已缓存到: {cache_file}")
        return cache_file
    
    def _load_analysis_cache(self, video_path: str, lecture_title: str) -> Optional[Tuple[Dict, Dict]]:
        """从缓存加载转录和分析结果"""
        cache_file = self._get_cache_file_path(video_path, lecture_title)
        
        if not os.path.exists(cache_file):
            return None
        
        try:
            with open(cache_file, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)
            
            # 验证缓存完整性
            if 'transcription' not in cache_data or 'analysis' not in cache_data:
                print("⚠️ 缓存文件不完整，将重新处理")
                return None
            
            # 验证文件hash（可选，确保视频文件没有变化）
            current_hash = self._get_file_hash(video_path)
            cached_hash = cache_data.get('cache_info', {}).get('file_hash', '')
            
            if current_hash != cached_hash:
                print("⚠️ 视频文件已变化，将重新处理")
                return None
            
            print(f"📂 从缓存加载分析结果: {cache_file}")
            return cache_data['transcription'], cache_data['analysis']
            
        except Exception as e:
            print(f"⚠️ 缓存加载失败: {e}，将重新处理")
            return None


    def extract_audio_from_video(self, video_path: str, output_audio_path: str) -> str:
        """从视频中提取音频"""
        (
            ffmpeg
            .input(video_path)
            .output(output_audio_path, acodec='pcm_s16le', ac=1, ar='16k')
            .overwrite_output()
            .run(quiet=True)
        )
        return output_audio_path

    def _format_timestamp(self, seconds: float) -> str:
        """将秒数转换为HH:MM:SS格式"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    def transcribe_video_with_timestamps(self, video_path: str, model_size: str = "base") -> Dict:
        """使用Whisper转录视频并获取时间戳"""
        model = whisper.load_model(model_size)
        result = model.transcribe(video_path, word_timestamps=True)
        # 记录转录信息
        self._log_processing_info("transcription", {
            "text_length": len(result.get('text', '')),
            "segments_count": len(result.get('segments', [])),
            "model_size": model_size
        })
        return result

    def _find_matching_timestamps(self, start_phrase: str, end_phrase: str, key_phrase: str, transcription: Dict) -> Dict:
        """基于关键句子精确匹配时间戳 - 高精度版本"""
        try:
            segments = transcription.get('segments', [])
            if not segments:
                return {"start_time": "00:00:00", "end_time": "00:00:00", "duration_seconds": 0}
            
            print(f"🔍 开始高精度时间戳匹配:")
            print(f"  开始句: {start_phrase}")
            print(f"  结束句: {end_phrase}")
            print(f"  关键句: {key_phrase}")
            
            start_time = None
            end_time = None
            match_method = "exact"
            
            # 🆕 改进1: 更精确的句子匹配算法
            def find_exact_segment_match(target_phrase: str, segments: list, search_forward: bool = True) -> tuple:
                """找到精确匹配的片段"""
                if not target_phrase.strip():
                    return None, "empty_phrase"
                
                target_phrase_clean = target_phrase.strip().lower()
                target_words = target_phrase_clean.split()
                
                # 如果目标短语太短，增加最小长度要求
                if len(target_words) < 3:
                    return None, "phrase_too_short"
                
                best_match = None
                best_score = 0
                best_method = "no_match"
                
                # 遍历片段
                segment_list = segments if search_forward else list(reversed(segments))
                
                for segment in segment_list:
                    segment_text = segment['text'].strip().lower()
                    segment_words = segment_text.split()
                    
                    # 跳过太短的片段
                    if len(segment_words) < 2:
                        continue
                    
                    # 🆕 改进2: 多种匹配策略
                    match_scores = []
                    
                    # 策略1: 完全匹配
                    if target_phrase_clean in segment_text:
                        match_scores.append(("exact", 1.0))
                    
                    # 策略2: 连续词匹配
                    consecutive_matches = 0
                    max_consecutive = 0
                    current_consecutive = 0
                    
                    for i, word in enumerate(target_words):
                        if word in segment_words:
                            current_consecutive += 1
                            max_consecutive = max(max_consecutive, current_consecutive)
                        else:
                            current_consecutive = 0
                    
                    if max_consecutive >= 3:  # 至少3个连续词匹配
                        consecutive_ratio = max_consecutive / len(target_words)
                        match_scores.append(("consecutive", consecutive_ratio))
                    
                    # 策略3: 关键词匹配
                    common_words = set(target_words) & set(segment_words)
                    if len(common_words) >= 3:  # 至少3个词匹配
                        word_match_ratio = len(common_words) / len(target_words)
                        match_scores.append(("keyword", word_match_ratio))
                    
                    # 策略4: 模糊匹配（使用编辑距离）
                    if len(target_phrase_clean) > 10:
                        from difflib import SequenceMatcher
                        similarity = SequenceMatcher(None, target_phrase_clean, segment_text).ratio()
                        if similarity > 0.7:  # 70%相似度
                            match_scores.append(("fuzzy", similarity))
                    
                    # 选择最佳匹配策略
                    if match_scores:
                        best_strategy = max(match_scores, key=lambda x: x[1])
                        strategy_name, score = best_strategy
                        
                        if score > best_score and score > 0.5:  # 提高匹配阈值
                            best_score = score
                            best_match = segment
                            best_method = strategy_name
                
                return best_match, best_method
            
            # 🆕 改进3: 智能时间范围估计
            def estimate_reasonable_duration(segments: list, start_time: float) -> float:
                """估计合理的片段持续时间"""
                # 计算所有片段的平均持续时间
                durations = [seg['end'] - seg['start'] for seg in segments]
                avg_duration = sum(durations) / len(durations) if durations else 30
                
                # 根据内容类型调整持续时间
                if '概率' in key_phrase or '概念' in key_phrase:
                    # 概念讲解通常较短
                    return min(avg_duration * 2, 120)  # 最多2分钟
                elif '例题' in key_phrase or '解题' in key_phrase:
                    # 例题讲解可能较长
                    return min(avg_duration * 3, 180)  # 最多3分钟
                else:
                    # 默认持续时间
                    return min(avg_duration * 2, 150)  # 最多2.5分钟
            
            # 🆕 改进4: 分别匹配开始和结束
            start_segment, start_method = find_exact_segment_match(start_phrase, segments, True)
            end_segment, end_method = find_exact_segment_match(end_phrase, segments, False)
            
            if start_segment:
                start_time = start_segment['start']
                match_method = start_method
                print(f"✅ 匹配开始句: {start_segment['text'][:50]}... (方法: {start_method})")
            else:
                print(f"❌ 未找到开始句匹配")
            
            if end_segment:
                end_time = end_segment['end']
                print(f"✅ 匹配结束句: {end_segment['text'][:50]}... (方法: {end_method})")
            else:
                print(f"❌ 未找到结束句匹配")
            
            # 🆕 改进5: 智能回退策略
            if start_time is None:
                # 尝试基于关键句找到开始时间
                key_segment, key_method = find_exact_segment_match(key_phrase, segments, True)
                if key_segment:
                    start_time = key_segment['start']
                    match_method = f"key_phrase_{key_method}"
                    print(f"✅ 基于关键句匹配开始: {key_segment['text'][:50]}...")
                else:
                    # 🆕 改进6: 基于内容位置的回退
                    # 根据片段在视频中的位置估计开始时间
                    total_segments = len(segments)
                    if total_segments > 0:
                        # 假设当前片段在视频的前1/3位置
                        estimated_start_index = max(0, total_segments // 3)
                        start_time = segments[estimated_start_index]['start']
                        match_method = "position_estimate"
                        print(f"⚠️  基于位置估计开始时间: {start_time:.1f}s")
                    else:
                        start_time = segments[0]['start']
                        match_method = "default_start"
                        print(f"⚠️  使用默认开始时间: {start_time}")
            
            if end_time is None:
                # 尝试基于关键句找到结束时间
                key_segment, key_method = find_exact_segment_match(key_phrase, segments, False)
                if key_segment:
                    end_time = key_segment['end']
                    print(f"✅ 基于关键句匹配结束: {key_segment['text'][:50]}...")
                else:
                    # 🆕 改进7: 基于合理持续时间的回退
                    if start_time is not None:
                        reasonable_duration = estimate_reasonable_duration(segments, start_time)
                        end_time = min(start_time + reasonable_duration, segments[-1]['end'])
                        match_method = "duration_estimate"
                        print(f"⚠️  基于持续时间估计结束时间: {end_time:.1f}s (持续{reasonable_duration:.1f}s)")
                    else:
                        end_time = segments[-1]['end']
                        match_method = "default_end"
                        print(f"⚠️  使用默认结束时间: {end_time}")
            
            # 🆕 改进8: 更严格的时间范围验证和修正
            if start_time is not None and end_time is not None:
                duration = end_time - start_time
                
                # 检查时间范围是否合理
                if duration < 5:  # 太短
                    reasonable_duration = estimate_reasonable_duration(segments, start_time)
                    end_time = min(start_time + reasonable_duration, segments[-1]['end'])
                    print(f"⚠️  时间范围太短，调整为{reasonable_duration:.1f}秒")
                elif duration > 300:  # 太长（5分钟）
                    # 尝试找到更合理的结束时间
                    reasonable_duration = estimate_reasonable_duration(segments, start_time)
                    end_time = min(start_time + reasonable_duration, segments[-1]['end'])
                    print(f"⚠️  时间范围太长，调整为{reasonable_duration:.1f}秒")
                
                # 确保结束时间不早于开始时间
                if end_time <= start_time:
                    reasonable_duration = estimate_reasonable_duration(segments, start_time)
                    end_time = min(start_time + reasonable_duration, segments[-1]['end'])
                    print(f"⚠️  结束时间早于开始时间，调整为{reasonable_duration:.1f}秒后")
                
                duration = end_time - start_time
            else:
                duration = 0
            
            timestamp_info = {
                "start_time": self._format_timestamp(start_time) if start_time else "00:00:00",
                "end_time": self._format_timestamp(end_time) if end_time else "00:00:00",
                "duration_seconds": duration,
                "start_seconds": start_time if start_time else 0,
                "end_seconds": end_time if end_time else 0,
                "match_method": match_method
            }
            
            print(f"🎯 时间戳匹配结果:")
            print(f"  开始时间: {timestamp_info['start_time']} ({start_time:.1f}s)")
            print(f"  结束时间: {timestamp_info['end_time']} ({end_time:.1f}s)")
            print(f"  持续时间: {duration:.1f}秒")
            print(f"  匹配方法: {match_method}")
            
            self._log_processing_info("timestamp_matching", {
                "start_phrase": start_phrase,
                "end_phrase": end_phrase,
                "key_phrase": key_phrase,
                "timestamp_info": timestamp_info,
                "match_method": match_method
            })
            
            return timestamp_info
            
        except Exception as e:
            print(f"❌ 时间戳匹配失败: {e}")
            return {"start_time": "00:00:00", "end_time": "00:00:00", "duration_seconds": 0}
    
    def analyze_video_content(self, transcription: Dict, lecture_title: str) -> Dict:
        """分析视频内容，智能识别内容类型和知识点切片 - 使用PromptManager版本"""
        
        # 🆕 使用PromptManager获取Prompt
        try:
            prompt = self.prompt_manager.get_prompt(
                "video_analysis",
                lecture_title=lecture_title,
                transcription_text=transcription['text']
            )
        except Exception as e:
            print(f"❌ 获取视频分析Prompt失败: {e}")
            # 降级到硬编码Prompt（备用方案）
            prompt = self._get_fallback_analysis_prompt(transcription, lecture_title)
        
        # 调用LLM分析
        response = self.model.generate_content(prompt)
        estimated_tokens = len(prompt.split()) + len(transcription['text'].split())
        
        # 检查API响应
        # 检查响应状态和内容
        if not response:
            print(f"❌ API调用失败: 响应为空")
            return {
                "content_type": "未知",
                "content_subtype": "未知",
                "confidence": 0.0,
                "content_segments": [],
                "summary": "API调用失败"
            }
        
        # 检查是否有finish_reason错误
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'finish_reason'):
                finish_reason = candidate.finish_reason
                if finish_reason in [0, 1]:  # 0和1都表示正常完成
                    print(f"✅ API调用正常完成 (finish_reason={finish_reason})")
                elif finish_reason == 2:
                    print(f"⚠️ API调用达到最大token限制 (finish_reason=2)")
                elif finish_reason == 3:
                    print(f"❌ API调用被安全过滤阻止 (finish_reason=3)")
                    return {
                        "content_type": "未知",
                        "content_subtype": "未知",
                        "confidence": 0.0,
                        "content_segments": [],
                        "summary": "API调用被安全过滤阻止"
                    }
                elif finish_reason == 4:
                    print(f"⚠️ API调用达到递归限制 (finish_reason=4)")
                else:
                    print(f"⚠️ API调用出现未知状态 (finish_reason={finish_reason})")
        
        # 检查响应文本
        if not hasattr(response, 'text') or not response.text:
            print(f"❌ API调用失败: 响应没有文本内容")
            return {
                "content_type": "未知",
                "content_subtype": "未知",
                "confidence": 0.0,
                "content_segments": [],
                "summary": "API响应没有文本内容"
            }
        
        print(f"✅ API调用成功，响应长度: {len(response.text)}")
        
        # 清理响应（移除可能的markdown包装）
        cleaned_response = response.text
        if cleaned_response.startswith('```'):
            cleaned_response = cleaned_response.replace('```', '').strip()
        
        try:
            # 解析结构化文本响应
            result = self._parse_structured_response(cleaned_response)
            self._log_processing_info("content_analysis", {
                "token_count": estimated_tokens,
                "content_type": result.get("content_type", ""),
                "content_subtype": result.get("content_subtype", ""),
                "confidence": result.get("confidence", 0.0),
                "segments_count": len(result.get("content_segments", [])),
                "api_response_length": len(response.text),
                "prompt_used": "video_analysis (from file)"  # 🆕 记录使用的Prompt来源
            })
            return result
        except Exception as e:
            print(f"结构化文本解析失败: {e}")
            print(f"API响应内容: {response.text[:500]}...")
            print(f"清理后内容: {cleaned_response[:500]}...")
            return {
                "content_type": "未知",
                "content_subtype": "未知",
                "confidence": 0.0,
                "content_segments": [],
                "summary": "分析失败"
            }
    
    def _get_fallback_analysis_prompt(self, transcription: Dict, lecture_title: str) -> str:
        """获取备用的硬编码分析Prompt（当文件Prompt不可用时）"""
        return f"""
你是一个专业的课程内容分析助手。请分析以下视频转录内容：

视频标题：{lecture_title}
转录内容：{transcription['text']}

请返回结构化分析结果...
"""
    
    def _parse_structured_response(self, text: str) -> Dict:
        """解析结构化文本响应"""
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

    # 🆕 优化5: 重写process_video方法，添加缓存功能
    def process_video(self, video_path: str, lecture_title: str, language: str = "中文") -> Dict:
        """处理视频的完整流程 - 优化版本（支持缓存）"""
        from datetime import datetime
        start_time = datetime.now()
        
        print("🚀 开始视频处理流程...")
        print(f"视频: {video_path}")
        print(f"标题: {lecture_title}")
        
        # 🆕 优化6: 尝试从缓存加载转录和分析结果
        cached_result = self._load_analysis_cache(video_path, lecture_title)
        
        if cached_result:
            transcription, analysis = cached_result
            print("✅ 使用缓存的转录和分析结果")
            
            # 🆕 修复：从缓存加载时也要更新处理日志
            if 'content_segments' in analysis:
                self.processing_log['segments_count'] = len(analysis['content_segments'])
                self.processing_log['content_type'] = analysis.get('content_type', '')
                self.processing_log['content_subtype'] = analysis.get('content_subtype', '')
                self.processing_log['confidence'] = analysis.get('confidence', 0.0)
                self.processing_log['transcription_length'] = len(transcription.get('text', ''))
                
                # 计算估计的token数量
                estimated_tokens = len(transcription.get('text', '').split()) * 2  # 粗略估计
                self.processing_log['token_count'] = estimated_tokens
                self.processing_log['api_calls'] = 1  # 假设之前调用过API
                
                print(f"📊 从缓存恢复处理统计:")
                print(f"  - 内容片段数: {self.processing_log['segments_count']}")
                print(f"  - 内容类型: {self.processing_log['content_type']}")
                print(f"  - 转录长度: {self.processing_log['transcription_length']}字符")
        else:
            # 第一次处理：转录和分析
            print("🎬 正在转录视频...")
            transcription = self.transcribe_video_with_timestamps(video_path)
            
            print("🧠 正在分析视频内容...")
            analysis = self.analyze_video_content(transcription, lecture_title)
            
            print("⏰ 正在精确匹配时间戳...")
            if 'content_segments' in analysis:
                for i, segment in enumerate(analysis['content_segments']):
                    timestamp_info = self._find_matching_timestamps(
                        segment.get('start_phrase', ''),
                        segment.get('end_phrase', ''),
                        segment.get('key_phrase', ''),
                        transcription
                    )
                    segment.update(timestamp_info)
                    self._log_processing_info("segment_details", {
                        "segment_id": segment.get('id', f'seg_{i+1:03d}'),
                        "title": segment.get('title', ''),
                        "start_phrase": segment.get('start_phrase', ''),
                        "end_phrase": segment.get('end_phrase', ''),
                        "key_phrase": segment.get('key_phrase', ''),
                        "importance": segment.get('importance', ''),
                        "category": segment.get('category', ''),
                        "difficulty": segment.get('difficulty', ''),
                        "timestamp_info": timestamp_info
                    })
                    print(f"✅ 片段 '{segment.get('title', '')}' 匹配到时间戳: {timestamp_info['start_time']} - {timestamp_info['end_time']} (时长: {timestamp_info['duration_seconds']:.1f}秒)")
            
            # 🆕 优化7: 保存转录和分析结果到缓存
            self._save_analysis_cache(video_path, lecture_title, transcription, analysis)
        
        # 🆕 优化8: 每次都重新生成Summary（因为可能调整prompt）
        print("🔄 正在整合完整Summary...")
        summary_result = self.summary_integrator.generate_summary(
            analysis, transcription, lecture_title, language
        )

        # 保留原有功能（可选）
        print("📝 正在生成分段笔记...")
        notes = "分段笔记功能暂未实现"  # 临时占位符
        
        print("📋 正在创建分段摘要...")
        summary = "分段摘要功能暂未实现"  # 临时占位符
        summary_with_timestamps = "带时间戳的分段摘要功能暂未实现"  # 临时占位符
        
        end_time = datetime.now()
        processing_time = (end_time - start_time).total_seconds()
        self.processing_log["processing_time"] = processing_time
        self._print_processing_report()
        
        # 🆕 优化9: 返回整合后的结果
        return {
            "transcription": transcription,
            "analysis": analysis,
            "notes": notes,  # 原有分段笔记
            "summary": summary,  # 原有分段摘要
            "summary_with_timestamps": summary_with_timestamps,
            
            # 🆕 新增整合Summary相关字段
            "integrated_summary": summary_result["summary"],
            "timestamp_mapping": summary_result["timestamp_mapping"],
            "knowledge_points": summary_result["knowledge_points"],
            "summary_statistics": self.summary_integrator.get_summary_statistics(
                summary_result["summary"], 
                summary_result["knowledge_points"]
            ),
            
            "lecture_title": lecture_title,
            "language": language,
            "processing_log": self.processing_log,
            "cache_used": cached_result is not None  # 🆕 标识是否使用了缓存
        }

    def _print_processing_report(self):
        print("\n" + "="*60)
        print("📊 视频处理详细报告")
        print("="*60)
        print(f"🧮 Token数量: {self.processing_log['token_count']:,}")
        print(f"📊 内容片段数: {self.processing_log['segments_count']}")
        print(f"⏱️  处理时间: {self.processing_log['processing_time']:.2f}秒")
        print(f"📝 转录文本长度: {self.processing_log['transcription_length']}字符")
        print(f"🔁 API调用次数: {self.processing_log['api_calls']}")
        print(f"📋 内容类型: {self.processing_log['content_type']}")
        print(f"🗂️  内容子类型: {self.processing_log['content_subtype']}")
        print(f"🎯 置信度: {self.processing_log['confidence']:.2f}")
        print("\n📋 内容片段详情:")
        for i, segment in enumerate(self.processing_log['segments_details']):
            print(f"  {i+1}. {segment['title']}")
            print(f"     开始句: {segment['start_phrase'][:50]}...")
            print(f"     结束句: {segment['end_phrase'][:50]}...")
            print(f"     关键句: {segment['key_phrase'][:50]}...")
            print(f"     时间戳: {segment['timestamp_info']['start_time']} - {segment['timestamp_info']['end_time']}")
            print(f"     时长: {segment['timestamp_info']['duration_seconds']:.1f}秒")
            print(f"     重要性: {segment['importance']}, 类别: {segment['category']}, 难度: {segment['difficulty']}")
            print()
        print("="*60)

    def _log_processing_info(self, stage: str, info: Dict):
        """记录处理信息"""
        print(f"🔍 [{stage}] {info}")
        if stage == "transcription":
            self.processing_log["transcription_length"] = info.get("text_length", 0)
            self.processing_log["segments_count"] = info.get("segments_count", 0)
        elif stage == "content_analysis":
            self.processing_log["token_count"] = info.get("token_count", 0)
            self.processing_log["api_calls"] += 1
            self.processing_log["content_type"] = info.get("content_type", "")
            self.processing_log["content_subtype"] = info.get("content_subtype", "")
            self.processing_log["confidence"] = info.get("confidence", 0.0)
        elif stage == "timestamp_matching":
            self.processing_log["timestamp_matches"].append(info)
        elif stage == "segment_details":
            self.processing_log["segments_details"].append(info)
    
    # 🆕 优化10: 新增缓存管理方法
    def clear_cache(self, lecture_title: str = None):
        """清理缓存文件"""
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
        """列出所有缓存文件"""
        import glob
        cache_files = glob.glob(os.path.join(self.cache_dir, "*_analysis.json"))
        print("📂 缓存文件列表:")
        for cache_file in cache_files:
            file_size = os.path.getsize(cache_file) / 1024  # KB
            mtime = datetime.fromtimestamp(os.path.getmtime(cache_file))
            print(f"  - {os.path.basename(cache_file)} ({file_size:.1f}KB, {mtime.strftime('%Y-%m-%d %H:%M:%S')})")
    
    # 🆕 新增Prompt管理相关方法
    def update_analysis_prompt(self, new_prompt_content: str):
        """
        更新视频分析Prompt
        
        Args:
            new_prompt_content: 新的Prompt内容
        """
        self.prompt_manager.create_prompt_template("video_analysis", new_prompt_content)
        print("✅ 已更新视频分析Prompt")
    
    def reload_prompts(self):
        """重新加载所有Prompt模板"""
        self.prompt_manager.clear_cache()
        print("🔄 已重新加载所有Prompt模板")
    
    def list_available_prompts(self):
        """列出所有可用的Prompt"""
        prompts = self.prompt_manager.list_available_prompts()
        print("📋 可用的Prompt模板:")
        for prompt in prompts:
            info = self.prompt_manager.get_prompt_info(prompt)
            if info.get('exists'):
                print(f"  - {prompt}.md ({info.get('word_count', 0)} 词)")
            else:
                print(f"  - {prompt}.md (文件不存在)")
    
    def get_prompt_statistics(self):
        """获取Prompt使用统计"""
        return {
            "available_prompts": self.prompt_manager.list_available_prompts(),
            "video_analysis_info": self.prompt_manager.get_prompt_info("video_analysis"),
            "prompts_directory": self.prompt_manager.prompts_dir
        }