import os
import google.generativeai as genai

print("--- 开始最终核心诊断 ---")

# --- 1. 配置您的API密钥 ---
# 请将 "YOUR_API_KEY" 替换成您自己的Google API密钥
API_KEY = "AIzaSyB4AsX9OL7PCBpBHiFIHOdzvJ3E72g4DOQ" 
if API_KEY == "YOUR_API_KEY" or not API_KEY:
    print("❌ 错误：请在代码中填入您的API密钥！")
    exit()
genai.configure(api_key=API_KEY)
print("✅ API Key 已配置")

# --- 2. 配置代理（确保和您主程序一致）---
# 如果您的网络需要代理，请取消下面几行的注释
os.environ['https_proxy'] = "http://127.0.0.1:8118"
os.environ['http_proxy'] = "http://127.0.0.1:8118"
os.environ['all_proxy'] = "socks5://127.0.0.1:8119"
print("✅ 代理已配置")

# --- 3. 定义一个绝对简单的Prompt和模型 ---
# 我们不再从文件读取，直接在代码中定义
simple_prompt = "天空为什么是蓝色的？请用中文简单回答。"
model_name = 'gemini-2.5-pro' # 使用官方确认的有效模型名称
print(f"✅ 使用模型: {model_name}")
print(f"✅ 使用Prompt: '{simple_prompt}'")


# --- 4. 执行API调用并进行最详细的打印 ---
try:
    print("\n--- 正在调用API... ---")
    model = genai.GenerativeModel(model_name)
    response = model.generate_content(simple_prompt)
    
    print("\n--- API调用完成，开始深入分析响应对象 ---")
    
    # 打印所有我们能获取到的信息
    print(f"响应对象类型: {type(response)}")
    
    if hasattr(response, '__dict__'):
        print(f"响应对象原始属性: {response.__dict__}")
    else:
        print("响应对象没有 __dict__ 属性")

    if hasattr(response, 'candidates') and response.candidates:
        print(f"候选内容数量: {len(response.candidates)}")
        candidate = response.candidates[0]
        print(f"候选[0] finish_reason: {getattr(candidate, 'finish_reason', 'N/A')}")
        print(f"候选[0] safety_ratings: {getattr(candidate, 'safety_ratings', 'N/A')}")
        
        if hasattr(candidate, 'content') and hasattr(candidate.content, 'parts'):
            print(f"候选[0] content.parts 数量: {len(candidate.content.parts)}")
            if len(candidate.content.parts) > 0:
                 print(f"候选[0] content.parts[0] 的内容: {candidate.content.parts[0]}")
            else:
                 print("!!! 关键发现：content.parts列表为空 !!!")
        else:
            print("!!! 关键发现：响应中找不到 content.parts 结构 !!!")
            
    else:
        print("!!! 关键发现：响应中不包含任何 'candidates' !!!")

    # 最后尝试访问 .text
    print("\n--- 尝试访问 .text ---")
    try:
        print(f"成功获取 .text 内容: \n---\n{response.text}\n---")
    except ValueError as e:
        print(f"访问 .text 失败，错误信息: {e}")

except Exception as e:
    print(f"\n--- API调用过程中发生严重异常 ---")
    print(f"异常类型: {type(e).__name__}")
    print(f"异常详情: {e}")

print("\n--- 诊断结束 ---")