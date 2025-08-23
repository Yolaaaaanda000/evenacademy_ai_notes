#!/usr/bin/env python3
"""
测试返回的数据结构
"""

import os
from core.video_processor import VideoProcessor
from dotenv import load_dotenv

def test_return_structure():
    """测试返回的数据结构"""
    print("🧪 测试返回的数据结构...")
    
    # 加载环境变量
    load_dotenv('llm.env')
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key:
        print("❌ 未设置GEMINI_API_KEY")
        return False
    
    # 初始化处理器（缓存模式）
    processor = VideoProcessor(api_key, cache_only_mode=True)
    
    try:
        # 处理视频（使用缓存）
        result = processor.process_video("", "Untitled Video", "中文")
        
        print("📊 返回的数据结构:")
        print("=" * 50)
        
        # 检查关键字段
        key_fields = [
            'transcription', 'analysis', 'integrated_summary', 
            'timestamp_mapping', 'knowledge_points', 'cache_used',
            'processor_version', 'lecture_title', 'language'
        ]
        
        for field in key_fields:
            if field in result:
                value = result[field]
                if isinstance(value, dict):
                    print(f"✅ {field}: dict (键数量: {len(value)})")
                elif isinstance(value, list):
                    print(f"✅ {field}: list (长度: {len(value)})")
                elif isinstance(value, str):
                    print(f"✅ {field}: str (长度: {len(value)})")
                else:
                    print(f"✅ {field}: {type(value).__name__}")
            else:
                print(f"❌ {field}: 缺失")
        
        # 检查是否有错误
        if 'error' in result:
            print(f"❌ 包含错误: {result['error']}")
            return False
        
        # 检查processor_version
        processor_version = result.get('processor_version', 'unknown')
        print(f"\n🔧 处理器版本: {processor_version}")
        
        # 检查integrated_summary
        if 'integrated_summary' in result:
            summary = result['integrated_summary']
            print(f"📝 Summary长度: {len(summary)} 字符")
            print(f"📝 Summary预览: {summary[:100]}...")
        
        # 检查knowledge_points
        if 'knowledge_points' in result:
            kp_count = len(result['knowledge_points'])
            print(f"🎯 知识点数量: {kp_count}")
            if kp_count > 0:
                first_kp = result['knowledge_points'][0]
                print(f"🎯 第一个知识点: {first_kp.get('title', '无标题')}")
        
        # 检查analysis
        if 'analysis' in result:
            analysis = result['analysis']
            if 'content_segments' in analysis:
                segments_count = len(analysis['content_segments'])
                print(f"📋 内容片段数量: {segments_count}")
        
        print("\n✅ 数据结构检查完成")
        return True
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        return False

if __name__ == "__main__":
    print("🚀 返回数据结构测试")
    print("=" * 50)
    
    success = test_return_structure()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 测试通过！")
    else:
        print("❌ 测试失败")
