#!/usr/bin/env python
import sys
import os
import traceback

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("Testing trigger service import...")

try:
    from src.models.trigger_rule import TriggerRule

    print("SUCCESS: TriggerRule imported")
except Exception as e:
    print(f"ERROR: TriggerRule: {e}")

try:
    from src.models.artifact import Artifact

    print("SUCCESS: Artifact imported")
except Exception as e:
    print(f"ERROR: Artifact: {e}")

try:
    from src.services.trigger_service import TriggerService

    print("SUCCESS: TriggerService imported")
except Exception as e:
    print(f"ERROR: TriggerService: {e}")
    traceback.print_exc()

try:
    from src.services.artifact_service import ArtifactService

    print("SUCCESS: ArtifactService imported")
except Exception as e:
    print(f"ERROR: ArtifactService: {e}")
    traceback.print_exc()
