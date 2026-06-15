import os
from enum import IntEnum

class RoleLevel(IntEnum):
    STUDENT = 10
    RESEARCHER = 20
    COORDINATOR = 30
    ADMINISTRATOR = 40

ROLE_HIERARCHY = {
    RoleLevel.STUDENT: ["view_project", "edit_own_kanban"],
    RoleLevel.RESEARCHER: ["create_project", "manage_students", "view_gantt"],
    RoleLevel.COORDINATOR: ["allocate_funds", "approve_milestones", "modify_gantt"],
    RoleLevel.ADMINISTRATOR: ["purge_system", "modify_system_rbac"]
}

def has_minimum_role(user_role: int, required_minimum: RoleLevel) -> bool:
    """
    Evaluates role level capability based on numerical structural evaluation.
    Prevents access if the user's role weight is beneath the constraint threshold.
    """
    return user_role >= required_minimum.value

def get_all_permissions_for_role(user_role: int) -> set:
    """
    Cascades down the hierarchy tree to aggregate all inherited permission nodes.
    """
    permissions = set()
    for level, perms in ROLE_HIERARCHY.items():
        if user_role >= level.value:
            permissions.update(perms)
    return permissions