#!/usr/bin/env python
import sys
import os

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.template_service import TemplateService
import re

service = TemplateService()

# Test different malformed patterns
test_cases = [
    ("# {{title}\n{{content", "Missing closing braces"),
    ("# {{title}}}", "Extra closing brace"),
    ("# {{{title}}", "Extra opening brace"),
    ("# {{title {{nested}} }}", "Nested placeholder"),
    ("# {{}}", "Empty placeholder"),
    ("# {{title|}}", "Empty default"),
    ("# {{|default}}", "Empty placeholder name"),
    ("# {{title||extra}}", "Multiple pipes"),
]

for template, description in test_cases:
    print(f"\n{description}: {repr(template)}")
    placeholder_pattern = r"\{\{.*?\}\}"
    matches = list(re.finditer(placeholder_pattern, template))
    print(f"  Regex matches: {len(matches)}")
    for match in matches:
        placeholder = match.group(0)
        print(f"    Match: {repr(placeholder)}")

    try:
        service.validate_template_schema(template)
        print("  Result: No error")
    except Exception as e:
        print(f"  Result: {type(e).__name__}: {e}")