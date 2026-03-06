"""
Optimized Prompts for Document Analysis
Well-crafted prompts for better LLM responses.
"""

# =================================
# System Prompts
# =================================

SYSTEM_PROMPT_ANALYST = """You are an expert document analyst. Your role is to:
- Extract key information accurately
- Provide clear, structured summaries
- Identify important insights and patterns
- Present information in a reader-friendly format

Be concise but thorough. Focus on what matters most to the reader."""


# =================================
# Summary Prompts
# =================================

def get_summary_prompt(content: str, doc_type: str) -> dict:
    """Get optimized prompt for document summarization."""

    doc_type_context = {
        "pdf": "This is a PDF document. Pay attention to structure, headings, and key sections.",
        "spreadsheet": "This is spreadsheet data. Focus on numerical patterns, trends, and data relationships.",
        "webpage": "This is web content. Focus on the main article content, ignoring navigation and ads.",
        "document": "This is a general document. Extract the core message and key points."
    }

    context = doc_type_context.get(doc_type, doc_type_context["document"])

    user_prompt = f"""{context}

Please analyze the following content and provide a comprehensive summary.

CONTENT:
---
{content[:25000]}
---

Provide your summary in this format:

## Overview
[2-3 sentences describing what this document is about]

## Key Points
- [Main point 1]
- [Main point 2]
- [Main point 3]
- [Additional points as needed]

## Summary
[A detailed 3-5 sentence summary of the most important information]"""

    return {
        "system": SYSTEM_PROMPT_ANALYST,
        "user": user_prompt
    }


# =================================
# Insights Prompts
# =================================

def get_insights_prompt(content: str, doc_type: str) -> dict:
    """Get optimized prompt for extracting insights."""

    user_prompt = f"""Analyze the following {doc_type} content and extract actionable insights.

CONTENT:
---
{content[:25000]}
---

Provide exactly 5 key insights. Each insight should be:
- Specific and actionable
- Based on evidence from the document
- Useful for decision-making

Format your response as:

1. **[Insight Title]**: [Detailed explanation of the insight]

2. **[Insight Title]**: [Detailed explanation of the insight]

3. **[Insight Title]**: [Detailed explanation of the insight]

4. **[Insight Title]**: [Detailed explanation of the insight]

5. **[Insight Title]**: [Detailed explanation of the insight]"""

    return {
        "system": SYSTEM_PROMPT_ANALYST,
        "user": user_prompt
    }


# =================================
# Q&A Prompts
# =================================

def get_qa_prompt(question: str, context: str) -> dict:
    """Get optimized prompt for question answering."""

    system_prompt = """You are a helpful assistant that answers questions based on provided document context.

Guidelines:
- Only answer based on the provided context
- If the answer is not in the context, say "I cannot find this information in the provided documents"
- Cite specific parts of the document when relevant
- Be concise but complete"""

    user_prompt = f"""Based on the following document content, please answer the question.

DOCUMENT CONTEXT:
---
{context[:20000]}
---

QUESTION: {question}

Please provide a clear, accurate answer based only on the information in the document context above."""

    return {
        "system": system_prompt,
        "user": user_prompt
    }


# =================================
# Analysis Prompts
# =================================

def get_analysis_prompt(content: str, doc_type: str) -> dict:
    """Get optimized prompt for full document analysis."""

    user_prompt = f"""Perform a comprehensive analysis of this {doc_type} document.

CONTENT:
---
{content[:25000]}
---

Provide your analysis in the following structured format:

## Document Overview
[What type of document is this? What is its purpose?]

## Executive Summary
[3-4 sentences summarizing the most critical information]

## Key Findings
1. [Finding 1]
2. [Finding 2]
3. [Finding 3]
4. [Finding 4]
5. [Finding 5]

## Important Details
- [Detail 1]
- [Detail 2]
- [Detail 3]

## Actionable Insights
1. **[Insight]**: [Why this matters and what to do about it]
2. **[Insight]**: [Why this matters and what to do about it]
3. **[Insight]**: [Why this matters and what to do about it]"""

    return {
        "system": SYSTEM_PROMPT_ANALYST,
        "user": user_prompt
    }


# =================================
# Feedback-Enhanced Prompts
# =================================

def get_improved_summary_prompt(
    content: str,
    doc_type: str,
    previous_summary: str,
    feedback: str
) -> dict:
    """Get prompt for improving summary based on user feedback."""

    user_prompt = f"""A user has provided feedback on a summary. Please improve it.

ORIGINAL DOCUMENT ({doc_type}):
---
{content[:20000]}
---

PREVIOUS SUMMARY:
---
{previous_summary}
---

USER FEEDBACK:
---
{feedback}
---

Please provide an improved summary that addresses the user's feedback while maintaining accuracy to the original document."""

    return {
        "system": SYSTEM_PROMPT_ANALYST,
        "user": user_prompt
    }

