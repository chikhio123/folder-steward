from fastapi import APIRouter, HTTPException
from typing import List

from ..schemas.rule_schema import RuleCreateRequest, RuleUpdateRequest, RuleResponse
from ..models.rule import Rule
from ..repositories.rule_repository import RuleRepository

router = APIRouter(tags=["rules"])
rule_repo = RuleRepository()

@router.post("/rules", response_model=RuleResponse)
def create_rule(body: RuleCreateRequest):
    rule = Rule(
        name=body.name,
        rule_type=body.rule_type,
        pattern=body.pattern,
        target_dir=body.target_dir,
        action=body.action,
        priority=body.priority,
        enabled=body.enabled,
    )
    rule_id = rule_repo.create(rule)
    created_rule = rule_repo.get(rule_id)
    if not created_rule:
        raise HTTPException(status_code=500, detail="Failed to retrieve created rule")

    return RuleResponse(**created_rule.__dict__)

@router.get("/rules", response_model=List[RuleResponse])
def list_rules(only_enabled: bool = False):
    rules = rule_repo.list_all(only_enabled=only_enabled)
    return [RuleResponse(**r.__dict__) for r in rules]

@router.patch("/rules/{rule_id}", response_model=RuleResponse)
def update_rule(rule_id: int, body: RuleUpdateRequest):
    rule = rule_repo.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")

    if body.name is not None: rule.name = body.name
    if body.rule_type is not None: rule.rule_type = body.rule_type
    if body.pattern is not None: rule.pattern = body.pattern
    if body.target_dir is not None: rule.target_dir = body.target_dir
    if body.action is not None: rule.action = body.action
    if body.priority is not None: rule.priority = body.priority
    if body.enabled is not None: rule.enabled = body.enabled

    rule_repo.update(rule)
    updated_rule = rule_repo.get(rule_id)
    if not updated_rule:
        raise HTTPException(status_code=500, detail="Failed to retrieve updated rule")

    return RuleResponse(**updated_rule.__dict__)

@router.delete("/rules/{rule_id}")
def delete_rule(rule_id: int):
    rule = rule_repo.get(rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    rule_repo.delete(rule_id)
    return {"status": "deleted"}