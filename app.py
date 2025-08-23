import os
import tempfile
import json
from flask import Flask, request, render_template, send_file, jsonify
from dotenv import load_dotenv
import google.generativeai as genai
from datetime import datetime
from core.video_processor import VideoProcessor
from core.knowledge_tagger import KnowledgeTagger
from core.practice_tutor_handler import PracticeLLMHandler
from core.ai_dialogue_handler import handle_ai_dialogue_request
from core.knowledge_point_dialogue import handle_knowledge_point_dialogue_request

# 新处理器标志
NEW_PROCESSOR = True

# Vercel部署模式配置
CACHE_ONLY_MODE = True  # 设置为True时仅使用缓存，跳过视频处理
VERCEL_DEPLOYMENT = True  # Vercel部署标志

# 加载环境变量
load_dotenv('llm.env')
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 移除本地代理设置，适配Vercel部署
# os.environ['https_proxy'] = "http://127.0.0.1:8118"
# os.environ['http_proxy'] = "http://127.0.0.1:8118"
# os.environ['all_proxy'] = "socks5://127.0.0.1:8119"

app = Flask(__name__)

# 初始化LLM练习处理器
practice_handler = PracticeLLMHandler(prompt_template_path='prompts/practice_tutor_prompt.md')

# Vercel部署配置
MAX_FILE_SIZE = 4 * 1024 * 1024  # 4MB限制

@app.route('/', methods=['GET'])
def index():
    """视频播放器主页"""
    return render_template('video_player.html')

@app.route('/download', methods=['POST'])
def download():
    """文件下载功能"""
    content = request.form.get('content', '')
    filename = request.form.get('filename', 'generated_content')
    file_extension = request.form.get('file_extension', '.txt')
    with tempfile.NamedTemporaryFile(mode='w', suffix=file_extension, delete=False, encoding='utf-8') as f:
        f.write(content)
        temp_path = f.name
    return send_file(
        temp_path,
        as_attachment=True,
        download_name=f"{filename}{file_extension}",
        mimetype='application/octet-stream'
    )

@app.route('/process_video', methods=['POST'])
def process_video():
    """处理视频文件，生成带时间戳的笔记"""
    if 'video_file' not in request.files:
        return jsonify({"error": "缺少视频文件"}), 400
    
    video_file = request.files['video_file']
    if video_file.filename == '':
        return jsonify({"error": "未选择视频文件"}), 400
    
    # Vercel文件大小检查
    video_file.seek(0, 2)  # 移动到文件末尾
    file_size = video_file.tell()
    video_file.seek(0)  # 重置到文件开头
    
    if file_size > MAX_FILE_SIZE:
        return jsonify({
            "error": f"文件大小超过限制。最大允许: {MAX_FILE_SIZE // (1024*1024)}MB，当前文件: {file_size // (1024*1024)}MB"
        }), 400
    
    lecture_title = request.form.get('title', 'Untitled Video')
    language = request.form.get('language', 'English')
    output_type = request.form.get('output_type', 'notes')
    
    # 检查文件格式
    video_ext = os.path.splitext(video_file.filename)[1].lower()
    if video_ext not in ['.mp4', '.mov', '.avi', '.mkv']:
        return jsonify({"error": "不支持的视频格式"}), 400
    
    try:
        # 检查是否为缓存模式
        if CACHE_ONLY_MODE:
            print("🔧 缓存模式：跳过视频处理，直接使用缓存数据")
            
            # 初始化视频处理器（缓存模式）
            processor = VideoProcessor(os.getenv("GEMINI_API_KEY"), cache_only_mode=True)
            
            # 使用预定义的缓存文件路径
            cache_video_path = f"./data/cache/{lecture_title}_cache.mp4"
            
            # 处理视频（仅使用缓存）
            result = processor.process_video(cache_video_path, lecture_title, language)
        else:
            # 完整处理模式
            with tempfile.TemporaryDirectory() as tmpdir:
                # 保存视频文件
                video_path = os.path.join(tmpdir, video_file.filename)
                video_file.save(video_path)
                
                # 初始化视频处理器
                processor = VideoProcessor(os.getenv("GEMINI_API_KEY"))
                
                # 处理视频
                result = processor.process_video(video_path, lecture_title, language)
            
            # 根据是否使用新处理器返回不同格式
            if NEW_PROCESSOR and 'integrated_summary' in result:
                # 新架构：有整合Summary
                if output_type == 'integrated_summary':
                    content = result['integrated_summary']
                    filename = f"{lecture_title}_完整Summary"
                    file_extension = '.md'
                    analysis_data = result.get('analysis', {})
                elif output_type == 'notes':
                    content = result.get('notes', result.get('integrated_summary', ''))
                    filename = f"{lecture_title}_带时间戳笔记"
                    file_extension = '.md'
                    analysis_data = result.get('analysis', {})
                elif output_type == 'summary':
                    content = result.get('summary', result.get('integrated_summary', ''))
                    filename = f"{lecture_title}_视频摘要"
                    file_extension = '.md'
                    analysis_data = result.get('analysis', {})
                elif output_type == 'analysis':
                    content = json.dumps(result.get('analysis', {}), ensure_ascii=False, indent=2)
                    filename = f"{lecture_title}_视频分析"
                    file_extension = '.json'
                    analysis_data = result.get('analysis', {})
                else:
                    # 默认返回整合Summary
                    content = result.get('integrated_summary', '')
                    filename = f"{lecture_title}_完整Summary"
                    file_extension = '.md'
                    analysis_data = result.get('analysis', {})
                
                return jsonify({
                    "success": True,
                    "content": content,
                    "filename": filename,
                    "file_extension": file_extension,
                    "analysis": analysis_data,
                    "transcription": result.get('transcription', {}),
                    "lecture_title": lecture_title,
                    "language": language,
                    "integrated_summary": result.get('integrated_summary', ''),
                    "timestamp_mapping": result.get('timestamp_mapping', {}),
                    "knowledge_points": result.get('knowledge_points', []),
                    "cache_used": result.get('cache_used', False),
                    "processor_version": "new",
                    "summary_statistics": result.get('summary_statistics', {})
                })
            
            else:
                # 旧架构：保持原有逻辑
                if output_type == 'notes':
                    content = result['notes']
                    filename = f"{lecture_title}_带时间戳笔记"
                    file_extension = '.md'
                elif output_type == 'summary':
                    content = result['summary']
                    filename = f"{lecture_title}_视频摘要"
                    file_extension = '.md'
                    analysis_data = result.get('summary_with_timestamps', {})
                elif output_type == 'analysis':
                    content = json.dumps(result['analysis'], ensure_ascii=False, indent=2)
                    filename = f"{lecture_title}_视频分析"
                    file_extension = '.json'
                    analysis_data = result['analysis']
                else:
                    content = result['notes']
                    filename = f"{lecture_title}_带时间戳笔记"
                    file_extension = '.md'
                
                return jsonify({
                    "success": True,
                    "content": content,
                    "filename": filename,
                    "file_extension": file_extension,
                    "analysis": analysis_data if 'analysis_data' in locals() else result['analysis'],
                    "transcription": result['transcription'],
                    "processor_version": "legacy"
                })
            
    except Exception as e:
        error_msg = f"处理视频时出错: {str(e)}"
        if CACHE_ONLY_MODE:
            error_msg += " (缓存模式)"
        return jsonify({"error": error_msg}), 500

@app.route('/practice_dialog', methods=['GET'])
def practice_dialog():
    """练习对话框页面"""
    return render_template('practice_dialog.html')

@app.route('/knowledge_point_chat', methods=['GET'])
def knowledge_point_chat():
    """知识点专用对话页面"""
    knowledge_point_data = request.args.get('knowledge_point')
    
    if knowledge_point_data:
        try:
            knowledge_point = json.loads(knowledge_point_data)
            return render_template('knowledge_point_chat.html', knowledge_point=knowledge_point)
        except Exception as e:
            print(f"解析知识点数据失败: {e}")
            return render_template('knowledge_point_chat.html')
    else:
        return render_template('knowledge_point_chat.html')

@app.route('/get_practice_session/<knowledge_point>', methods=['GET'])
def get_practice_session(knowledge_point):
    """获取指定知识点的练习会话"""
    try:
        limit = request.args.get('limit', 5, type=int)
        
        tagger = KnowledgeTagger()
        
        # 🆕 使用新的基于知识点的匹配方法
        matched_questions = tagger.question_matcher.find_questions_by_knowledge_point(
            knowledge_point=knowledge_point, 
            limit=limit
        )
        
        session = tagger.create_practice_session(knowledge_point, matched_questions)
        
        return jsonify({
            "success": True,
            "session": session
        })
        
    except Exception as e:
        return jsonify({"error": f"获取练习会话失败: {str(e)}"}), 500

@app.route('/chat_for_practice', methods=['POST'])
def chat_for_practice():
    """处理练习对话框中的用户消息"""
    try:
        data = request.get_json()
        question = data.get('question')
        user_message_raw = data.get('user_message', '')

        if not all([question, user_message_raw]):
            return jsonify({"error": "从前端接收的数据不完整"}), 400

        user_message_command = user_message_raw.strip().lower()

        # 检查本地命令
        if user_message_command in ['提示', '给我提示', 'hint']:
            hint = question.get('hint') or '抱歉，这道题没有预设的提示。'
            return jsonify({"success": True, "llm_response": f"💡 提示：{hint}"})

        if user_message_command in ['答案', '看答案', '告诉我答案']:
            answer = question.get('answer', '未知')
            explanation = question.get('explanation', '暂无官方解析。')
            return jsonify({"success": True, "llm_response": f"好的，正确答案是 {answer}。\n📝 解析：{explanation}"})

        # LLM处理
        knowledge_point = question.get('knowledge_point', '未知知识点') 
        language = question.get('language', 'English') 
                
        llm_reply = practice_handler.generate_response(
            knowledge_point, question, user_message_raw, language
        )

        return jsonify({
            "success": True,
            "llm_response": llm_reply
        })
            
    except Exception as e:
        return jsonify({"error": f"处理请求时发生内部错误: {str(e)}"}), 500

@app.route('/chat_for_video', methods=['POST'])
def chat_for_video():
    """处理视频播放页面的AI对话"""
    try:
        data = request.get_json()
        message = data.get('message', '')
        video_data = data.get('video_data', {})
        dialogue_history = data.get('dialogue_history', [])
        
        request_data = {
            'message': message,
            'context_type': 'video',
            'context_data': video_data,
            'dialogue_history': dialogue_history
        }
        
        result = handle_ai_dialogue_request(request_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/chat_for_knowledge_point', methods=['POST'])
def chat_for_knowledge_point():
    """处理知识点专用对话"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        knowledge_point_data = data.get('knowledge_point_data', {})
        dialogue_history = data.get('dialogue_history', [])
        dialogue_state = data.get('dialogue_state')
        language = data.get('language', 'English')
        
        request_data = {
            'knowledge_point_data': knowledge_point_data,
            'user_message': user_message,
            'dialogue_history': dialogue_history,
            'dialogue_state': dialogue_state,
            'language': language
        }
        
        result = handle_knowledge_point_dialogue_request(request_data)
        
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'处理知识点对话时发生错误: {str(e)}'
        }), 500

if __name__ == '__main__':
    print(f"🚀 启动独立视频播放器应用")
    print(f"📊 视频处理器版本: {'新版本(支持缓存+整合Summary)' if NEW_PROCESSOR else '旧版本(兼容模式)'}")
    print(f"🤖 AI对话处理器: 已集成统一对话处理模块")
    
    # 适配Vercel部署
    port = int(os.environ.get('PORT', 5012))
    app.run(host='0.0.0.0', port=port) 