#!/usr/bin/env python3
import sys
sys.path.insert(0, "/Users/I528664/Downloads/learning/llmMCP")
print("Testing ContractIQ...")
from src.contract_iq.models import ContractAnalysis
print("Models: OK")
from src.contract_iq.templates import TemplateLibrary
print("Templates: OK")
from src.contract_iq.risk_scorer import RiskScorer
print("RiskScorer: OK")
print("All imports successful!")

# Python equivalent of your Java example
from openai import OpenAI

client = OpenAI(
    base_url="http://localhost:12000/engines/v1",
    api_key="not-needed"
)

response = client.chat.completions.create(
    model="ai/smollm2:360M-Q4_K_M",
    messages=[{"role": "user", "content": "Give me a fact about whales."}]
)
print(response.choices[0].message.content)
