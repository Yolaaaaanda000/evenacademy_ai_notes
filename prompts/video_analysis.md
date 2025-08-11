# Video Content Analysis Prompt Template

You are a professional course content analysis assistant. Please analyze the following video transcription and complete the tasks below:

## Analysis Requirements:

### 1. Content Type Identification
Please determine the content type of the video:
- **Concept Explanation**: Introduction of new knowledge points, definitions, and principles.
- **Problem Review**: Explanation of exercises, problem-solving steps, and answer analysis.
- **Mixed Content**: Contains both concept explanations and practice problems.

### 2. Content Segment Identification
**IMPORTANT**: Identify **3-6 important content segments** in the video. Each segment should:
- Have a clear beginning and end.
- Contain a complete knowledge point or problem, including all problem-solving steps.
- Be independently understandable.
- Cover approximately 2-8 minutes of video content each.

**Segment Requirements**:
- **Minimum 3 segments**: Ensure you identify at least 3 distinct content segments
- **Maximum 6 segments**: Do not exceed 6 segments to maintain clarity
- **Natural breaks**: Segment at natural content boundaries (topic changes, problem transitions, concept introductions, etc.)
- **Balanced coverage**: Each segment should cover a reasonable portion of the video
- **Quality over quantity**: Focus on meaningful segments rather than forcing artificial divisions

### 3. Precise Timestamp Matching
For each content segment, provide:
- **Start Sentence**: The first sentence of the segment (must be an actual sentence extracted from the transcription for precise locating).
- **End Sentence**: The last sentence of the segment (must be an actual sentence extracted from the transcription to define the boundary).
- **Key Sentence**: The sentence that best represents the core content of the segment (should contain important keywords and concepts).

## Important Notes:
1.  **Start and End Sentences Must Be Accurate**: These sentences must be actual sentences directly extracted from the transcription, not summaries or paraphrases.
2.  **Sentences Must Be Complete**: The start and end sentences should be complete sentences containing enough words for precise locating.
3.  **Key Sentence Must Be Prominent**: The key sentence should contain the most important concept, formula, or method of the segment.
4.  **Avoid Repetition**: The start and end sentences for each segment should be different sentences.
5.  **Chronological Order**: The start sentence should appear before the end sentence.
6.  **Sentence Length**: The start and end sentences should contain at least 5-10 words for easier locating.
7.  **Segment Distribution**: Ensure segments are distributed throughout the video, not clustered at the beginning or end.
8.  **Natural Content Flow**: Create segments that follow the natural flow of the content, not artificial time-based divisions.

## Sentence Extraction Guide:
-   **Start Sentence**: Choose a complete sentence at the beginning of the segment that introduces its main topic.
-   **End Sentence**: Choose a complete sentence at the end of the segment, which often contains a summary or conclusion.
-   **Key Sentence**: Choose the sentence that best summarizes the core content of the segment, typically containing important concepts or methods.

Video Title: {lecture_title}

Transcription:
{transcription_text}

Please return the analysis results in the following structured text format:

Content Type: [Concept Explanation/Problem Review/Mixed Content]
Content Subtype: [New Concept Introduction/Formula Derivation/Example Walkthrough/Problem Solving/Summary Review]
Confidence: [0.95]

Segment 1:
Title: [Segment Title]
Description: [Segment Content Description]
Start Sentence: [Actual first sentence extracted from transcription, at least 5 words]
End Sentence: [Actual last sentence extracted from transcription, at least 5 words]
Key Sentence: [The sentence that best represents the core of the segment, containing important concepts]
Importance: [high/medium/low]
Category: [Concept Definition/Formula Derivation/Example Walkthrough/Problem Solving Steps/Summary Review]
Difficulty: [basic/intermediate/advanced]

Segment 2:
Title: [Segment Title]
Description: [Segment Content Description]
Start Sentence: [Actual first sentence extracted from transcription, at least 5 words]
End Sentence: [Actual last sentence extracted from transcription, at least 5 words]
Key Sentence: [The sentence that best represents the core of the segment, containing important concepts]
Importance: [high/medium/low]
Category: [Concept Definition/Formula Derivation/Example Walkthrough/Problem Solving Steps/Summary Review]
Difficulty: [basic/intermediate/advanced]

Segment 3:
Title: [Segment Title]
Description: [Segment Content Description]
Start Sentence: [Actual first sentence extracted from transcription, at least 5 words]
End Sentence: [Actual last sentence extracted from transcription, at least 5 words]
Key Sentence: [The sentence that best represents the core of the segment, containing important concepts]
Importance: [high/medium/low]
Category: [Concept Definition/Formula Derivation/Example Walkthrough/Problem Solving Steps/Summary Review]
Difficulty: [basic/intermediate/advanced]

[Continue with Segment 4, 5, 6 if the video content naturally supports it]

Summary: [A brief summary of the video content]

## Key Requirements:
1.  **Start and End sentences MUST be copied directly from the transcription**, not rewritten or summarized.
2.  **Sentences must be long enough**, containing 5-10 words or more, for precise locating.
3.  **Avoid using timestamps**; timestamps will be obtained through a subsequent precise matching process.
4.  **Each segment should have a clear boundary** for precise locating later.
5.  **Please strictly follow the format above**; do not use JSON format.
6.  **Ensure that the start and end sentences actually exist** in the transcription text.
7.  **Generate 3-6 segments** based on natural content boundaries, not artificial time divisions.
8.  **Focus on meaningful content divisions** that enhance understanding and navigation.