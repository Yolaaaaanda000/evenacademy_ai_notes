# 这是一个用于诊断Gemini API响应被阻止问题的独立脚本

import google.generativeai as genai
import os

print("--- 开始诊断Gemini API调用 ---")

# --- 1. 配置您的API密钥 ---
# 请将 "YOUR_API_KEY" 替换成您自己的Google API密钥
# 如果您习惯用环境变量，请确保该环境变量已设置
try:
    # 推荐方式：从环境变量读取，更安全
    # GOOGLE_API_KEY = os.environ.get('GOOGLE_API_KEY')
    # genai.configure(api_key=GOOGLE_API_KEY)
    
    # 或者，为了测试方便，直接在这里填写（注意不要泄露）
    genai.configure(api_key="AIzaSyBJd5Qm_kUFsf0J4nI7bdSW7ZodDPOTJVQ") 
    print("✅ API Key 配置成功")
except Exception as e:
    print(f"❌ API Key 配置失败: {e}")
    exit() # 配置失败则退出程序

# --- 2. 配置代理（如果需要） ---
# 如果您的网络环境需要代理才能访问Google，请取消下面的注释并确保端口正确
# 这里的设置应该和您主程序中的保持一致
os.environ['https_proxy'] = "http://127.0.0.1:8118"
print("✅ 代理已设置")


# --- 3. 初始化模型 ---
try:
    model = genai.GenerativeModel('gemini-2.5-pro')
    print(f"✅ 模型 'gemini-2.5-pro' 初始化成功")
except Exception as e:
    print(f"❌ 模型初始化失败: {e}")
    exit()


# --- 4. 填写导致问题的提示词 ---
# 这是最关键的一步，请务必将【】中的内容替换成您那条被阻止的提示词
prompt_that_causes_blocking = '''
# Summary Integration Prompt Template

You are a professional educational content editor. Based on the following video segment content, please generate a complete and highly readable course summary document in {language}.

## Language Requirements:
- Output language: {language}
- If {language} is "中文", write the summary in Chinese
- If {language} is "English", write the summary in English
- Maintain consistent language throughout the document

## Required Format (Strictly follow the structure below):

## Course Summary: {lecture_title}

## **Course Overview**
[Provide a 2-3 sentence summary of the main content and objectives of the entire course.]

## **Main Knowledge Points**
[Organize the knowledge points in a logical order. Each knowledge point should include:
- The knowledge point title in bold.
- A detailed but concise explanation.
- If there are specific steps or methods, list them clearly.
- Ensure the content is coherent, not just a simple stitching of segments.]

## **Important Formulas or Definitions**
[List all important formulas and definitions in the format:
- **Concept Name/Formula Name**: The formula's content or definition's description.
- Ensure formulas are accurate and complete.]

## **Key Concept Explanations**
[Provide in-depth explanations of important concepts to aid understanding:
- Explain the essence and importance of the concept.
- Describe the relationships between concepts.
- Offer tips or key points for understanding.]

## Segment Content Data:
{segments_content}

## 🎯 CRITICAL REQUIREMENTS FOR INTERACTIVE FEATURES:

### **Knowledge Point Marking Requirements:**
1. **MUST use [KP:Title] format**: When mentioning any knowledge point from the "Knowledge Points List" or "知识点标题列表" above, you MUST wrap it in the format `[KP:Title]`.

2. **Reference ALL available titles**: Review the "Knowledge Points List" or "知识点标题列表" carefully and incorporate ALL of these knowledge point titles into your Summary where appropriate.

3. **Natural integration**: Integrate the knowledge point titles naturally into your Summary content, don't just list them.

4. **Multiple references**: You can reference the same knowledge point multiple times in different contexts.

### **Examples of correct usage:**
- ✅ "The [KP:Statistical Definition of Probability] demonstrates how probability relates to long-term frequency."
- ✅ "In the section on [KP:Experiment and Outcome], we learned the fundamental concepts."
- ✅ "The [KP:Great Law of Large Numbers] is essential for understanding probability theory."

### **Examples of incorrect usage:**
- ❌ "The statistical definition demonstrates..." (missing [KP:Title])
- ❌ "In the experiment and outcome section..." (missing [KP:Title])
- ❌ "The law of large numbers..." (missing [KP:Title])

## Generation Requirements:
1. Maintain an academic and professional tone, but keep the language clear and easy to understand.
2. The content should be coherent and flow smoothly, organized by the logical relationship of knowledge points, not chronologically.
3. **CRITICAL**: When mentioning any content in the Summary that corresponds to a title from "Knowledge Points List" or "知识点标题列表" , you MUST wrap it in the format `[KP:Title]`. This is essential for interactive features.
4. Important formulas must be complete and accurate, using standard mathematical symbols.
5. Concept explanations should be insightful yet accessible for learners.
6. Avoid repetitive content and ensure the information is complete and consistent.
7. Adhere to the provided sample format.
8. **Ensure you reference ALL knowledge point titles** from the provided list in your Summary.

Please generate the complete Summary document
'''

print(f"📝 准备发送的提示词: {prompt_that_causes_blocking[:100]}...") # 打印前100个字符


# --- 5. 发送请求并捕获响应 ---
print("\n--- 正在发送请求... ---")
try:
    # 注意：这里没有加任何 safety_settings，使用Google的默认设置
    response = model.generate_content(prompt_that_causes_blocking)
    
    print("\n--- 收到响应 ---")
    print("✅ LLM调用成功，未抛出异常")
    
    # 打印最关键的诊断信息
    print(f"🔍 Finish Reason: {response.candidates[0].finish_reason}")
    print(f"🔍 Safety Ratings: \n{response.candidates[0].safety_ratings}")
    
    # 尝试打印文本内容
    try:
        print(f"📝 Response Text: {response.text}")
    except ValueError as e:
        print(f"📝 Response Text: 无法获取，因为 - {e}")

except Exception as e:
    print("\n--- 收到响应 ---")
    print(f"❌ 调用时发生异常: {e}")
    # 有些被阻止的响应会直接抛出异常，我们需要检查异常对象中是否包含response信息
    # 这一部分逻辑在新版库中可能不常见，但作为兼容性检查保留
    if hasattr(e, '__dict__') and 'response' in e.__dict__:
         response = e.response
         print(f"🔍 (从异常中获取) Finish Reason: {response.candidates[0].finish_reason}")
         print(f"🔍 (从异常中获取) Safety Ratings: \n{response.candidates[0].safety_ratings}")

print("\n--- 诊断结束 ---")