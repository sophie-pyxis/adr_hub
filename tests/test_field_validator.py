#!/usr/bin/env python
import sys
import os

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("Testing field_validator import...")

# Try importing field_validator directly
try:
    from pydantic import field_validator

    print("[OK] from pydantic import field_validator - SUCCESS")
except ImportError as e:
    print(f"[FAIL] from pydantic import field_validator - FAILED: {e}")

try:
    from pydantic.functional_validators import field_validator

    print("[OK] from pydantic.functional_validators import field_validator - SUCCESS")
except ImportError as e:
    print(
        f"[FAIL] from pydantic.functional_validators import field_validator - FAILED: {e}"
    )

try:
    import pydantic

    print(f"Pydantic version: {pydantic.__version__}")
    print(f"Pydantic __file__: {pydantic.__file__}")

    # Check what's available
    if hasattr(pydantic, "field_validator"):
        print("pydantic has field_validator attribute")
    else:
        print("pydantic does NOT have field_validator attribute")

    # Check pydantic.functional_validators
    if hasattr(pydantic, "functional_validators"):
        print("pydantic has functional_validators module")
        print(f"functional_validators contents: {dir(pydantic.functional_validators)}")
except Exception as e:
    print(f"Error: {e}")
