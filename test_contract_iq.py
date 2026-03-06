#!/usr/bin/env python
"""Test ContractIQ imports."""

import sys
sys.path.insert(0, '/Users/I528664/Downloads/learning/llmMCP')

print("Testing ContractIQ imports...")

try:
    print("1. Importing models...")
    from src.contract_iq.models import ContractAnalysis, RiskLevel
    print("   ✓ Models OK")
except Exception as e:
    print(f"   ✗ Models FAILED: {e}")
    sys.exit(1)

try:
    print("2. Importing prompts...")
    from src.contract_iq.prompts import CONTRACT_PROMPTS
    print("   ✓ Prompts OK")
except Exception as e:
    print(f"   ✗ Prompts FAILED: {e}")
    sys.exit(1)

try:
    print("3. Importing templates...")
    from src.contract_iq.templates import TemplateLibrary
    print("   ✓ Templates OK")
except Exception as e:
    print(f"   ✗ Templates FAILED: {e}")
    sys.exit(1)

try:
    print("4. Importing risk_scorer...")
    from src.contract_iq.risk_scorer import RiskScorer
    print("   ✓ RiskScorer OK")
except Exception as e:
    print(f"   ✗ RiskScorer FAILED: {e}")
    sys.exit(1)

try:
    print("5. Importing analyzer...")
    from src.contract_iq.analyzer import ContractAnalyzer
    print("   ✓ Analyzer OK")
except Exception as e:
    print(f"   ✗ Analyzer FAILED: {e}")
    sys.exit(1)

try:
    print("6. Importing comparator...")
    from src.contract_iq.comparator import ContractComparator
    print("   ✓ Comparator OK")
except Exception as e:
    print(f"   ✗ Comparator FAILED: {e}")
    sys.exit(1)

try:
    print("7. Importing export...")
    from src.contract_iq.export import ContractExporter
    print("   ✓ Export OK")
except Exception as e:
    print(f"   ✗ Export FAILED: {e}")
    sys.exit(1)

try:
    print("8. Importing router...")
    from src.contract_iq.router import router
    print("   ✓ Router OK")
except Exception as e:
    print(f"   ✗ Router FAILED: {e}")
    sys.exit(1)

print("\n✓ All ContractIQ modules imported successfully!")

# Test template library
print("\nTesting TemplateLibrary...")
lib = TemplateLibrary()
clauses = lib.list_clauses()
print(f"   Found {len(clauses)} clause templates")
templates = lib.list_contract_templates()
print(f"   Found {len(templates)} contract templates")

print("\n✓ ContractIQ is ready!")

