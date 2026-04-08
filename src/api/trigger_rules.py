"""
Trigger rules API router.

PHASE 5: API Routes
- CRUD endpoints for trigger rules
- Test evaluation endpoints
- Integration with trigger service
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, status, Depends, Query
from sqlmodel import Session, select

from ..models.trigger_rule import TriggerRule, TriggerRuleCreate, TriggerRuleRead, TriggerRuleUpdate
from ..models.artifact import Artifact
from ..services.trigger_service import TriggerService
from ..services.artifact_service import ArtifactService
from ..database import get_session

router = APIRouter(prefix="/api/triggers", tags=["triggers"])


def get_artifact_service(session: Session = Depends(get_session)) -> ArtifactService:
    """Dependency injection for ArtifactService."""
    return ArtifactService(session)


def get_trigger_service(
    session: Session = Depends(get_session),
    artifact_service: ArtifactService = Depends(get_artifact_service)
) -> TriggerService:
    """Dependency injection for TriggerService."""
    return TriggerService(session, artifact_service)


@router.get("/", response_model=List[TriggerRuleRead])
def get_trigger_rules(
    source_type: Optional[str] = Query(None, description="Filter by source artifact type"),
    target_type: Optional[str] = Query(None, description="Filter by target artifact type"),
    trigger_service: TriggerService = Depends(get_trigger_service)
):
    """
    Get all trigger rules with optional filtering.

    - **source_type**: Filter by source artifact type
    - **target_type**: Filter by target artifact type
    """
    try:
        query = select(TriggerRule)

        # Apply filters in database query for better performance
        if source_type:
            query = query.where(TriggerRule.source_type == source_type)
        if target_type:
            query = query.where(TriggerRule.target_type == target_type)

        rules = trigger_service.session.exec(query).all()

        # Convert to TriggerRuleRead models
        return [TriggerRuleRead.model_validate(rule) for rule in rules]

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting trigger rules: {str(e)}"
        )


@router.post("/", response_model=TriggerRuleRead, status_code=status.HTTP_201_CREATED)
def create_trigger_rule(
    rule_data: TriggerRuleCreate,
    trigger_service: TriggerService = Depends(get_trigger_service)
):
    """
    Create a new trigger rule.

    - **source_type**: Type of artifact that triggers (e.g., 'adr', 'rfc')
    - **target_type**: Type of artifact to create (e.g., 'evidence', 'governance')
    - **source_condition**: Condition expression (e.g., "level >= 4 and status == 'accepted'")
    - **description**: Human-readable description of the rule
    - **auto_create**: Whether to auto-create target artifact when condition is met
    - **required**: Whether this trigger is required (must be satisfied for certain operations)
    """
    try:
        # Create rule in database
        rule = TriggerRule(**rule_data.dict())
        trigger_service.session.add(rule)
        trigger_service.session.commit()
        trigger_service.session.refresh(rule)

        # Convert to TriggerRuleRead for response
        return TriggerRuleRead.model_validate(rule)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Internal server error: {str(e)}"
        )


@router.get("/{rule_id}", response_model=TriggerRuleRead)
def get_trigger_rule(
    rule_id: int,
    trigger_service: TriggerService = Depends(get_trigger_service)
):
    """
    Get trigger rule by ID.

    - **rule_id**: ID of the trigger rule to retrieve
    """
    try:
        rule = trigger_service.session.get(TriggerRule, rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger rule with ID {rule_id} not found"
            )

        return TriggerRuleRead.model_validate(rule)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting trigger rule: {str(e)}"
        )


@router.put("/{rule_id}", response_model=TriggerRuleRead)
def update_trigger_rule(
    rule_id: int,
    rule_update: TriggerRuleUpdate,
    trigger_service: TriggerService = Depends(get_trigger_service)
):
    """
    Update a trigger rule.

    - **rule_id**: ID of the trigger rule to update
    - **source_condition**: New condition expression (optional)
    - **description**: New description (optional)
    - **auto_create**: New auto_create setting (optional)
    - **required**: New required setting (optional)
    """
    try:
        rule = trigger_service.session.get(TriggerRule, rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger rule with ID {rule_id} not found"
            )

        # Get update data, excluding unset fields
        update_data = rule_update.dict(exclude_unset=True)

        # Validate source_condition if being updated
        if "source_condition" in update_data:
            # Use the validator from the model
            from ..models.trigger_rule import TriggerRuleUpdate as TRU
            validated_condition = TRU.validate_source_condition(update_data["source_condition"])
            update_data["source_condition"] = validated_condition

        # Update fields
        for field, value in update_data.items():
            setattr(rule, field, value)

        trigger_service.session.add(rule)
        trigger_service.session.commit()
        trigger_service.session.refresh(rule)

        return TriggerRuleRead.model_validate(rule)

    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating trigger rule: {str(e)}"
        )


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_trigger_rule(
    rule_id: int,
    trigger_service: TriggerService = Depends(get_trigger_service)
):
    """
    Delete a trigger rule.

    - **rule_id**: ID of the trigger rule to delete
    """
    try:
        rule = trigger_service.session.get(TriggerRule, rule_id)
        if not rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Trigger rule with ID {rule_id} not found"
            )

        trigger_service.session.delete(rule)
        trigger_service.session.commit()

        return None  # 204 No Content

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error deleting trigger rule: {str(e)}"
        )


@router.post("/test-evaluate")
def test_trigger_evaluation(
    artifact_id: int,
    condition: str,
    trigger_service: TriggerService = Depends(get_trigger_service),
    artifact_service: ArtifactService = Depends(get_artifact_service)
):
    """
    Test trigger condition evaluation.

    - **artifact_id**: ID of artifact to evaluate condition against
    - **condition**: Condition expression to test
    Returns evaluation result and any errors.
    """
    try:
        # Get artifact by ID
        artifact = artifact_service.get_artifact_by_id(artifact_id)
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact with ID {artifact_id} not found"
            )

        # Evaluate condition using trigger service
        result = trigger_service.evaluate_condition(
            artifact=artifact,
            condition=condition
        )

        return {
            "condition": condition,
            "result": result,
            "error": None
        }

    except HTTPException:
        raise
    except Exception as e:
        return {
            "condition": condition,
            "result": False,
            "error": str(e)
        }


@router.get("/suggestions/{artifact_id}")
def get_trigger_suggestions(
    artifact_id: int,
    trigger_service: TriggerService = Depends(get_trigger_service),
    session: Session = Depends(get_session)
):
    """
    Get trigger suggestions for an artifact.

    - **artifact_id**: ID of artifact to get suggestions for
    Returns trigger rules where condition is met.
    """
    try:
        # Get artifact directly from database (need Artifact object not ArtifactRead)
        artifact = session.get(Artifact, artifact_id)
        if not artifact:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Artifact with ID {artifact_id} not found"
            )

        # Get trigger suggestions
        suggestions = trigger_service.get_trigger_suggestions(
            artifact=artifact
        )

        return {
            "artifact_id": artifact_id,
            "suggestions": suggestions
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error getting suggestions: {str(e)}"
        )