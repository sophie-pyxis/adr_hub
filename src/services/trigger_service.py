"""
Trigger service for unified artifact model.

PHASE 4: Trigger Service
- Business logic for evaluating trigger conditions
- Auto-creation of artifacts based on trigger rules
- Integration with artifact service
- Safe evaluation of condition expressions
"""

import ast
import operator
import re
from typing import List, Dict, Any, Optional
from sqlmodel import Session, select

from ..models.trigger_rule import TriggerRule
from ..models.artifact import Artifact, ArtifactCreate
from ..services.artifact_service import ArtifactService


class TriggerEvaluationError(Exception):
    """Exception raised for trigger evaluation errors."""

    pass


class TriggerService:
    """Service for managing and evaluating trigger rules."""

    def __init__(self, session: Session, artifact_service: ArtifactService):
        """
        Initialize TriggerService.

        Args:
            session: Database session
            artifact_service: Artifact service for creating target artifacts
        """
        self.session = session
        self.artifact_service = artifact_service

        # Whitelist of safe operators
        self.safe_operators = {
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: lambda a, b: a and b,
            ast.Or: lambda a, b: a or b,
            ast.Not: operator.not_,
        }

        # Whitelist of allowed attributes
        self.allowed_attributes = {
            "level",
            "status",
            "artifact_type",
            "title",
            "content",
        }

    def get_rules_for_source_type(self, source_type: str) -> List[TriggerRule]:
        """
        Get all trigger rules for a source artifact type.

        Args:
            source_type: Type of artifact that triggers (e.g., 'adr', 'rfc')

        Returns:
            List of trigger rules
        """
        statement = select(TriggerRule).where(TriggerRule.source_type == source_type)
        result = self.session.exec(statement)
        return result.all()

    def evaluate_condition(self, artifact: Artifact, condition: str) -> bool:
        """
        Safely evaluate a condition against an artifact.

        Args:
            artifact: Artifact to evaluate condition against
            condition: Condition expression (e.g., "level >= 4 and status == 'accepted'")

        Returns:
            True if condition is met, False otherwise

        Raises:
            TriggerEvaluationError: If condition cannot be safely evaluated
        """
        if not condition.strip():
            return False

        try:
            # Parse the condition into AST
            tree = ast.parse(condition, mode="eval")

            # Validate the AST for safety
            self._validate_ast(tree.body)

            # Create a safe evaluation context
            context = self._create_evaluation_context(artifact)

            # Evaluate the expression
            result = self._evaluate_ast_node(tree.body, context)

            # Ensure result is boolean
            if not isinstance(result, bool):
                return False

            return result

        except (SyntaxError, ValueError, AttributeError, TypeError) as e:
            # Log the error but don't fail - return False for safety
            # In production, you might want to log this
            return False
        except Exception as e:
            # Catch-all for any other errors
            return False

    def _validate_ast(self, node: ast.AST) -> None:
        """
        Validate AST node for safety.

        Args:
            node: AST node to validate

        Raises:
            TriggerEvaluationError: If AST contains unsafe constructs
        """
        if isinstance(node, ast.Compare):
            # Validate left side
            self._validate_ast(node.left)

            # Validate comparators and ops
            for op in node.ops:
                if not any(
                    isinstance(op, op_type) for op_type in self.safe_operators.keys()
                ):
                    raise TriggerEvaluationError(f"Unsafe operator: {op}")

            for comparator in node.comparators:
                self._validate_ast(comparator)

        elif isinstance(node, ast.BoolOp):
            # Validate boolean operators
            if not isinstance(node.op, (ast.And, ast.Or)):
                raise TriggerEvaluationError(f"Unsafe boolean operator: {node.op}")

            for value in node.values:
                self._validate_ast(value)

        elif isinstance(node, ast.UnaryOp):
            # Validate unary operators
            if not isinstance(node.op, ast.Not):
                raise TriggerEvaluationError(f"Unsafe unary operator: {node.op}")

            self._validate_ast(node.operand)

        elif isinstance(node, ast.Name):
            # Check if attribute is allowed
            if node.id not in self.allowed_attributes:
                raise TriggerEvaluationError(f"Disallowed attribute: {node.id}")

        elif isinstance(node, ast.Constant):
            # Allow constants (strings, numbers, booleans, None)
            if not isinstance(node.value, (str, int, float, bool, type(None))):
                raise TriggerEvaluationError(
                    f"Unsafe constant type: {type(node.value)}"
                )

        elif isinstance(node, ast.Attribute):
            # Only allow attributes on 'artifact' object
            if not isinstance(node.value, ast.Name) or node.value.id != "artifact":
                raise TriggerEvaluationError(
                    "Only attributes on 'artifact' object are allowed"
                )

            if node.attr not in self.allowed_attributes:
                raise TriggerEvaluationError(f"Disallowed attribute: {node.attr}")

        elif isinstance(node, ast.Call):
            # No function calls allowed
            raise TriggerEvaluationError("Function calls are not allowed")

        else:
            # Any other node type is unsafe
            raise TriggerEvaluationError(f"Unsafe AST node type: {type(node)}")

    def _create_evaluation_context(self, artifact: Artifact) -> Dict[str, Any]:
        """
        Create a safe evaluation context for the artifact.

        Args:
            artifact: Artifact to create context from

        Returns:
            Dictionary with safe artifact attributes
        """
        return {
            "level": artifact.level,
            "status": artifact.status,
            "artifact_type": artifact.artifact_type,
            "title": artifact.title,
            "content": artifact.content,
            "artifact": {
                "level": artifact.level,
                "status": artifact.status,
                "artifact_type": artifact.artifact_type,
                "title": artifact.title,
                "content": artifact.content,
            },
            "True": True,
            "False": False,
            "None": None,
        }

    def _evaluate_ast_node(self, node: ast.AST, context: Dict[str, Any]) -> Any:
        """
        Evaluate an AST node with the given context.

        Args:
            node: AST node to evaluate
            context: Evaluation context

        Returns:
            Evaluation result
        """
        if isinstance(node, ast.Compare):
            # Evaluate comparison
            left = self._evaluate_ast_node(node.left, context)

            results = []
            for op, comparator in zip(node.ops, node.comparators):
                right = self._evaluate_ast_node(comparator, context)
                op_func = self.safe_operators[type(op)]
                result = op_func(left, right)
                results.append(result)
                left = right  # For chained comparisons

            return all(results)

        elif isinstance(node, ast.BoolOp):
            # Evaluate boolean operation
            values = [self._evaluate_ast_node(value, context) for value in node.values]

            if isinstance(node.op, ast.And):
                return all(values)
            elif isinstance(node.op, ast.Or):
                return any(values)

        elif isinstance(node, ast.UnaryOp):
            # Evaluate unary operation
            operand = self._evaluate_ast_node(node.operand, context)

            if isinstance(node.op, ast.Not):
                return not operand

        elif isinstance(node, ast.Name):
            # Look up name in context
            return context.get(node.id)

        elif isinstance(node, ast.Attribute):
            # Get attribute from artifact object
            obj = self._evaluate_ast_node(node.value, context)
            if isinstance(obj, dict):
                return obj.get(node.attr)
            else:
                return getattr(obj, node.attr, None)

        elif isinstance(node, ast.Constant):
            # Return constant value
            return node.value

        else:
            # Should not reach here due to validation
            raise TriggerEvaluationError(f"Cannot evaluate node type: {type(node)}")

    def check_triggers_for_artifact(self, artifact: Artifact) -> List[Dict[str, Any]]:
        """
        Check all triggers for an artifact and return matching ones.

        Args:
            artifact: Artifact to check triggers for

        Returns:
            List of dictionaries with trigger information:
            - rule: TriggerRule object
            - condition_met: Whether condition is met
            - auto_create: Whether to auto-create target
            - required: Whether this trigger is required
        """
        triggers = []
        rules = self.get_rules_for_source_type(artifact.artifact_type)

        for rule in rules:
            condition_met = self.evaluate_condition(artifact, rule.source_condition)

            triggers.append(
                {
                    "rule": rule,
                    "condition_met": condition_met,
                    "auto_create": rule.auto_create,
                    "required": rule.required,
                }
            )

        return triggers

    def create_target_artifact(
        self, source_artifact: Artifact, trigger_rule: TriggerRule
    ) -> Optional[Artifact]:
        """
        Create target artifact based on trigger rule.

        Args:
            source_artifact: Source artifact that triggered the rule
            trigger_rule: Trigger rule to execute

        Returns:
            Created artifact or None if auto_create is False
        """
        if not trigger_rule.auto_create:
            return None

        # Create target artifact data
        target_data = ArtifactCreate(
            artifact_type=trigger_rule.target_type,
            artifact_number="auto",  # Will be auto-generated
            title=f"{trigger_rule.target_type.title()} for {source_artifact.title}",
            status="proposed",
            content=f"Auto-generated {trigger_rule.target_type} artifact triggered by {source_artifact.artifact_type} '{source_artifact.title}'",
            squad_id=source_artifact.squad_id,
            triggered_by_id=source_artifact.id,
            trigger_reason=f"Auto-created by trigger rule: {trigger_rule.description}",
        )

        # Use artifact service to create the artifact
        # This will handle template validation, content generation, etc.
        return self.artifact_service.create_artifact(target_data)

    def process_artifact_triggers(self, artifact: Artifact) -> List[Artifact]:
        """
        Process all triggers for an artifact and auto-create targets.

        Args:
            artifact: Artifact to process triggers for

        Returns:
            List of created artifacts (empty list if none created)
        """
        created_artifacts = []
        triggers = self.check_triggers_for_artifact(artifact)

        for trigger in triggers:
            if trigger["condition_met"] and trigger["auto_create"]:
                created = self.create_target_artifact(artifact, trigger["rule"])
                if created:
                    created_artifacts.append(created)

        return created_artifacts

    def validate_required_triggers(self, artifact: Artifact) -> None:
        """
        Validate that all required triggers for an artifact are satisfied.

        Args:
            artifact: Artifact to validate

        Raises:
            ValueError: If a required trigger is not satisfied
        """
        triggers = self.check_triggers_for_artifact(artifact)

        for trigger in triggers:
            if trigger["required"] and not trigger["condition_met"]:
                rule = trigger["rule"]
                raise ValueError(
                    f"Required trigger not satisfied: {rule.description} "
                    f"(condition: {rule.source_condition})"
                )

    def get_trigger_suggestions(self, artifact: Artifact) -> List[Dict[str, Any]]:
        """
        Get trigger suggestions for an artifact.

        Args:
            artifact: Artifact to get suggestions for

        Returns:
            List of dictionaries with suggestion information:
            - rule: TriggerRule object
            - condition_met: Whether condition is met
            - auto_create: Whether to auto-create target
            - required: Whether this trigger is required
        """
        triggers = self.check_triggers_for_artifact(artifact)

        # Filter for suggestions (conditions that are met)
        suggestions = [t for t in triggers if t["condition_met"]]

        return suggestions
