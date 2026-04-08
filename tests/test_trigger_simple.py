#!/usr/bin/env python
import sys
import os
import traceback

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print(f"Project root: {project_root}")
print(f"Python path: {sys.path}")
print(f"Current dir: {os.getcwd()}")

# Check if src exists
src_path = os.path.join(project_root, "src")
print(f"src directory exists: {os.path.exists(src_path)}")

# Check if src/models exists
models_path = os.path.join(project_root, "src", "models")
print(f"src/models directory exists: {os.path.exists(models_path)}")

# Check if src/models/trigger_rule.py exists
trigger_rule_path = os.path.join(project_root, "src", "models", "trigger_rule.py")
print(f"src/models/trigger_rule.py exists: {os.path.exists(trigger_rule_path)}")

# Try to read the file directly
try:
    with open(trigger_rule_path, 'r') as f:
        first_line = f.readline()
        print(f"First line of trigger_rule.py: {first_line}")
except Exception as e:
    print(f"Error reading file: {e}")

# Try to import directly using file path
print("\nTrying direct import via file path...")
try:
    import importlib.util
    spec = importlib.util.spec_from_file_location("trigger_rule", trigger_rule_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    print(f"[OK] Direct file import successful")
    print(f"  Module: {module}")
    print(f"  Has TriggerRule: {hasattr(module, 'TriggerRule')}")
except Exception as e:
    print(f"[FAIL] Direct file import failed: {e}")
    traceback.print_exc()