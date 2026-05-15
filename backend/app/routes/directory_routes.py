from flask import Blueprint

from ..common.auth import require_permission
from ..common.responses import api_success
from ..services import directory_service

directory_bp = Blueprint("directory", __name__, url_prefix="/api/directory")


@directory_bp.get("/people")
@require_permission("flow.instance.view")
def people():
    return api_success(directory_service.list_people_and_groups(), "人员目录已获取。", "DIRECTORY_OK")
