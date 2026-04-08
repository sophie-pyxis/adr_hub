"""
FastAPI routers for AI Architecture Governance System.
"""

from .squads import router as squads_router
from .artifacts import router as artifacts_router
from .trigger_rules import router as triggers_router
from .health import router as health_router

__all__ = ["squads_router", "artifacts_router", "triggers_router", "health_router"]