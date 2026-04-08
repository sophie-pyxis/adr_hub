#!/usr/bin/env python
import os
import sys
import traceback

# Add project root to Python path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("Testing single trigger test...")

try:
    # Try to import just the first test function
    from src.models.artifact import Artifact
    from src.models.trigger_rule import TriggerRule
    from src.services.artifact_service import ArtifactService
    from src.services.trigger_service import TriggerService

    print("All imports successful")

    # Now test the function directly
    print("\nRunning test_trigger_service_initialization...")

    mock_session = type("MockSession", (), {})()
    mock_artifact_service = type("MockArtifactService", (), {})()

    service = TriggerService(mock_session, mock_artifact_service)

    assert service.session == mock_session
    assert service.artifact_service == mock_artifact_service

    print("SUCCESS: test_trigger_service_initialization passed")

except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()
