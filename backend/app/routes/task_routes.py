from flask import Blueprint, g, request

from ..common.auth import has_permission, require_permission
from ..common.responses import api_error, api_success
from ..services import process_service

tasks_bp = Blueprint("tasks", __name__, url_prefix="/api/flow/instances")


@tasks_bp.post("/<int:instance_id>/tasks/<int:task_id>/complete")
@require_permission("flow.instance.handle")
def complete_task(instance_id, task_id):
    can_manage = has_permission(g.current_user, "flow.template.manage")
    return api_success(process_service.complete_task(instance_id, task_id, g.current_user["id"], can_manage), "任务已完成。", "TASK_COMPLETED")


@tasks_bp.post("/<int:instance_id>/steps/<int:step_id>/complete")
@require_permission("flow.instance.handle")
def complete_step(instance_id, step_id):
    can_manage = has_permission(g.current_user, "flow.template.manage")
    return api_success(process_service.complete_step(instance_id, step_id, g.current_user["id"], can_manage), "步骤已完成。", "STEP_COMPLETED")


@tasks_bp.post("/<int:instance_id>/remind")
@require_permission("flow.instance.handle")
def remind(instance_id):
    payload = request.get_json(silent=True) or {}
    return api_success(process_service.remind_instance(instance_id, payload.get("message"), g.current_user["id"]), "催办已记录。", "REMIND_RECORDED")


@tasks_bp.get("/<int:instance_id>/logs")
@require_permission("flow.instance.view")
def logs(instance_id):
    instance = process_service.get_instance(instance_id)
    if not instance:
        return api_error("流程实例不存在。", 404, "INSTANCE_NOT_FOUND")
    return api_success({"items": instance.get("logs", [])}, "流程日志已获取。", "INSTANCE_LOGS_OK")
