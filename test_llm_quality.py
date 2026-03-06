#!/usr/bin/env python3
"""
Verify LLM Setup and Test Response Quality
"""

import asyncio
import os
from src.agents.local_llm_client import LocalLLMClient


async def test_llm_quality():
    """Test current LLM setup and response quality."""

    print("=" * 60)
    print("LLM QUALITY TEST")
    print("=" * 60)

    client = LocalLLMClient()
    print(f"\n📌 Current Setup:")
    print(f"   Model: {client.model}")
    print(f"   URL: {client.base_url}")

    # Test 1: Simple Q&A
    print(f"\n📝 Test 1: Simple Q&A")
    print("-" * 60)

    context = """
    John Smith is a Senior Software Engineer with 8 years of experience
    in full-stack web development. He specializes in Python, JavaScript,
    and cloud infrastructure. John has led teams of up to 5 developers
    and successfully delivered 15+ production applications.
    """

    question = "What is John's primary skill set?"
    print(f"Context: {context.strip()[:100]}...")
    print(f"Question: {question}")

    answer = await client.answer_question(question, context)
    print(f"Answer: {answer}")

    # Check for repetition
    if "John" in answer and answer.count("John") > 3:
        print("⚠️  WARNING: Possible repetition detected")
    else:
        print("✅ Response looks good (no excessive repetition)")

    # Test 2: Summarization
    print(f"\n📝 Test 2: Summarization")
    print("-" * 60)

    doc_content = """
    Machine learning is a subset of artificial intelligence that enables
    systems to learn and improve from experience without being explicitly
    programmed. It focuses on developing algorithms and statistical models
    that can make predictions or decisions based on data patterns.
    """

    print(f"Content: {doc_content.strip()[:100]}...")
    summary = await client.summarize(doc_content)
    print(f"Summary: {summary}")

    if len(summary) < 20 or summary.startswith("Error"):
        print("⚠️  WARNING: Poor summary")
    else:
        print("✅ Summary looks good")

    # Test 3: Insights
    print(f"\n📝 Test 3: Key Insights")
    print("-" * 60)

    insights = await client.extract_insights(doc_content)
    print(f"Insights found: {len(insights)}")
    for i, insight in enumerate(insights, 1):
        print(f"  {i}. {insight}")

    if len(insights) == 0 or any("Error" in i for i in insights):
        print("⚠️  WARNING: Could not extract insights")
    else:
        print("✅ Insights extracted successfully")

    # Recommendations
    print("\n" + "=" * 60)
    print("RECOMMENDATIONS")
    print("=" * 60)

    if "smollm2" in client.model.lower():
        print("\n⚠️  Current Model: smollm2-360M (very small)")
        print("\nTo improve quality:")
        print("1. Install Ollama: brew install ollama")
        print("2. Start Ollama: ollama serve")
        print("3. Pull better model: ollama pull neural-chat:7b")
        print("4. Set environment:")
        print("   export LLM_MODEL=neural-chat:7b")
        print("   export LOCAL_LLM_URL=http://localhost:11434/v1")
        print("\nSee: QUICK_START_BETTER_MODELS.md")
    else:
        print("\n✅ Good Model Detected!")
        print(f"   Using: {client.model}")
        print("   Quality should be much better")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(test_llm_quality())

