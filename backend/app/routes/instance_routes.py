from flask import Blueprint, g, request

from ..common.auth import has_permission, require_permission
from ..common.responses import api_error, api_success
from ..services import process_service

instances_bp = Blueprint("instances", __name__, url_prefix="/api/flow/instances")


@instances_bp.get("")
@require_permission("flow.instance.view")
def list_instances():
    template_id = request.args.get("templateId")
    return api_success({"items": process_service.list_instances(template_id)}, "流程实例列表已获取。", "INSTANCE_LIST_OK")


@instances_bp.post("")
@require_permission("flow.instance.start")
def create_instance():
    payload = request.get_json(silent=True) or {}
    template_id = payload.get("templateId")
    name = payload.get("name")
    if not template_id or not name:
        return api_error("缺少模板 ID 或流程名称。", 400, "VALIDATION_ERROR")
    instance = process_service.create_instance(
        template_id=template_id,
        name=name,
        initiator_id=g.current_user["id"],
        cloud_path=payload.get("cloudPath") or "",
    )
    return api_success(instance, "流程已新建。", "INSTANCE_CREATED", 201)


@instances_bp.get("/<int:instance_id>")
@require_permission("flow.instance.view")
def get_instance(instance_id):
    instance = process_service.get_instance(instance_id)
    if not instance:
        return api_error("流程实例不存在。", 404, "INSTANCE_NOT_FOUND")
    return api_success(instance, "流程实例详情已获取。", "INSTANCE_DETAIL_OK")


@instances_bp.put("/<int:instance_id>")
@require_permission("flow.instance.handle", "flow.template.manage")
def update_instance(instance_id):
    instance = process_service.update_instance(instance_id, request.get_json(silent=True) or {}, g.current_user["id"])
    if not instance:
        return api_error("流程实例不存在。", 404, "INSTANCE_NOT_FOUND")
    return api_success(instance, "流程实例已更新。", "INSTANCE_UPDATED")


@instances_bp.delete("/<int:instance_id>")
@require_permission("flow.template.manage")
def delete_instance(instance_id):
    result = process_service.delete_instance(instance_id, g.current_user["id"])
    return api_success(result, "流程实例已删除。", "INSTANCE_DELETED")


@instances_bp.put("/<int:instance_id>/steps/<int:step_id>/fields")
@require_permission("flow.instance.handle", "flow.template.manage")
def update_instance_step_fields(instance_id, step_id):
    can_manage = has_permission(g.current_user, "flow.template.manage")
    instance = process_service.update_instance_step_fields(
        instance_id,
        step_id,
        request.get_json(silent=True) or {},
        g.current_user["id"],
        can_manage,
    )
    return api_success(instance, "步骤填写内容已保存。", "INSTANCE_FIELDS_UPDATED")


@instances_bp.put("/<int:instance_id>/steps/<int:step_id>/assignment")
@require_permission("flow.instance.handle", "flow.template.manage")
def update_instance_step_assignment(instance_id, step_id):
    can_manage = has_permission(g.current_user, "flow.template.manage")
    instance = process_service.update_instance_step_assignment(
        instance_id,
        step_id,
        request.get_json(silent=True) or {},
        g.current_user["id"],
        can_manage,
    )
    return api_success(instance, "步骤负责人已更新。", "INSTANCE_ASSIGNMENT_UPDATED")


@instances_bp.post("/<int:instance_id>/steps/<int:step_id>/revision")
@require_permission("flow.instance.handle", "flow.template.manage")
def record_step_revision(instance_id, step_id):
    can_manage = has_permission(g.current_user, "flow.template.manage")
    instance = process_service.record_step_revision(
        instance_id,
        step_id,
        request.get_json(silent=True) or {},
        g.current_user["id"],
        can_manage,
    )
    return api_success(instance, "修订已记录。", "INSTANCE_REVISION_RECORDED")


@instances_bp.post("/<int:instance_id>/checklist")
@require_permission("flow.instance.view")
def generate_checklist(instance_id):
    instance = process_service.generate_checklist(instance_id, g.current_user["id"])
    return api_success(instance, "查检表已生成。", "CHECKLIST_GENERATED")
