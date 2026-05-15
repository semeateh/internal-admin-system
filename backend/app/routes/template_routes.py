from flask import Blueprint, g, request

from ..common.auth import require_permission
from ..common.responses import api_error, api_success
from ..services import process_service

templates_bp = Blueprint("templates", __name__, url_prefix="/api/flow/templates")


@templates_bp.get("")
@require_permission("flow.instance.view")
def list_templates():
    return api_success({"items": process_service.list_templates()}, "模板列表已获取。", "TEMPLATE_LIST_OK")


@templates_bp.post("")
@require_permission("flow.template.manage")
def create_template():
    template = process_service.create_template(request.get_json(silent=True) or {}, g.current_user["id"])
    return api_success(template, "模板已创建。", "TEMPLATE_CREATED", 201)


@templates_bp.get("/<int:template_id>")
@require_permission("flow.instance.view")
def get_template(template_id):
    template = process_service.get_template(template_id)
    if not template:
        return api_error("模板不存在或已被删除。", 404, "TEMPLATE_NOT_FOUND")
    return api_success(template, "模板详情已获取。", "TEMPLATE_DETAIL_OK")


@templates_bp.put("/<int:template_id>")
@require_permission("flow.template.manage")
def update_template(template_id):
    template = process_service.update_template(template_id, request.get_json(silent=True) or {}, g.current_user["id"])
    return api_success(template, "模板已保存。", "TEMPLATE_UPDATED")


@templates_bp.post("/<int:template_id>/steps")
@require_permission("flow.template.manage")
def add_step(template_id):
    template = process_service.add_template_step(template_id, request.get_json(silent=True) or {}, g.current_user["id"])
    return api_success(template, "步骤已新增。", "TEMPLATE_STEP_CREATED", 201)


@templates_bp.put("/<int:template_id>/steps/<int:step_id>")
@require_permission("flow.template.manage")
def update_step(template_id, step_id):
    payload = request.get_json(silent=True) or {}
    template = process_service.update_template_step(template_id, step_id, payload, g.current_user["id"])
    return api_success(template, "步骤已更新。", "TEMPLATE_STEP_UPDATED")


@templates_bp.delete("/<int:template_id>/steps/<int:step_id>")
@require_permission("flow.template.manage")
def delete_step(template_id, step_id):
    template = process_service.delete_template_step(template_id, step_id, g.current_user["id"])
    return api_success(template, "步骤已删除。", "TEMPLATE_STEP_DELETED")
