#!/usr/bin/env python
import os
import sys

project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

from src.services.template_service import TemplateService

service = TemplateService()

# Test the template with missing closing braces
template_content = "# {{title}\n{{content"

try:
    service.validate_template_schema(template_content)
    print("ERROR: Should have raised TemplateValidationError")
except Exception as e:
    print(f"Actual error message: {e}")
    print(f"Type: {type(e).__name__}")

# Test nested placeholder
template_content2 = "# {{title {{nested}} }}"

try:
    service.validate_template_schema(template_content2)
    print("ERROR: Should have raised TemplateValidationError")
except Exception as e:
    print(f"Actual error message: {e}")
    print(f"Type: {type(e).__name__}")
