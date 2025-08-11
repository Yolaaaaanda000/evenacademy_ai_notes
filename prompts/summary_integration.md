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

Please generate the complete Summary document: