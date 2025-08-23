#!/usr/bin/env python3
"""
测试缓存模式功能
"""

import os
import sys
import json
from core.video_processor import VideoProcessor

def test_cache_mode():
    """测试缓存模式"""
    print("🧪 开始测试缓存模式...")
    
    # 检查环境变量
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ 错误：未设置GEMINI_API_KEY环境变量")
        return False
    
    # 检查缓存文件
    cache_dir = "./data/cache"
    if not os.path.exists(cache_dir):
        print("❌ 错误：缓存目录不存在")
        return False
    
    cache_files = [f for f in os.listdir(cache_dir) if f.endswith('_analysis.json')]
    if not cache_files:
        print("❌ 错误：未找到缓存文件")
        return False
    
    print(f"✅ 找到 {len(cache_files)} 个缓存文件")
    
    # 初始化处理器（缓存模式）
    try:
        processor = VideoProcessor(api_key, cache_only_mode=True)
        print("✅ 视频处理器初始化成功")
    except Exception as e:
        print(f"❌ 处理器初始化失败: {e}")
        return False
    
    # 测试处理
    try:
        result = processor.process_video("", "Untitled Video", "中文")
        
        if "error" in result:
            print(f"❌ 处理失败: {result['error']}")
            return False
        
        print("✅ 缓存模式处理成功")
        print(f"📊 处理结果:")
        print(f"  - 转录长度: {len(result.get('transcription', {}).get('text', ''))} 字符")
        print(f"  - 内容片段数: {len(result.get('analysis', {}).get('content_segments', []))}")
        print(f"  - Summary长度: {len(result.get('integrated_summary', ''))} 字符")
        print(f"  - 知识点数: {len(result.get('knowledge_points', []))}")
        print(f"  - 缓存使用: {result.get('cache_used', False)}")
        print(f"  - 处理模式: {result.get('processing_mode', 'unknown')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理过程中出错: {e}")
        return False

def test_cache_files():
    """测试缓存文件完整性"""
    print("\n📂 检查缓存文件完整性...")
    
    cache_dir = "./data/cache"
    cache_files = [f for f in os.listdir(cache_dir) if f.endswith('_analysis.json')]
    
    for cache_file in cache_files:
        file_path = os.path.join(cache_dir, cache_file)
        file_size = os.path.getsize(file_path) / 1024  # KB
        
        print(f"📄 {cache_file} ({file_size:.1f}KB)")
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # 检查必需字段
            required_fields = ['cache_info', 'transcription', 'analysis']
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"  ❌ 缺少字段: {missing_fields}")
            else:
                print(f"  ✅ 文件结构完整")
                print(f"  📝 转录文本长度: {len(data['transcription'].get('text', ''))} 字符")
                print(f"  🧠 分析片段数: {len(data['analysis'].get('content_segments', []))}")
                
        except Exception as e:
            print(f"  ❌ 文件读取失败: {e}")

if __name__ == "__main__":
    print("🚀 缓存模式测试工具")
    print("=" * 50)
    
    # 测试缓存文件
    test_cache_files()
    
    # 测试缓存模式
    success = test_cache_mode()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 所有测试通过！缓存模式工作正常")
    else:
        print("❌ 测试失败，请检查配置")
    
    sys.exit(0 if success else 1)
