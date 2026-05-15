from datetime import datetime

from ..models.process import INSTANCE_STATUS, TEMPLATE_STATUS


def format_datetime(value):
    if value is None:
        return ""
    if isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    return str(value)


def map_template(row):
    return {
        "id": str(row["id"]),
        "name": row["template_name"],
        "department": row["department_name"],
        "status": TEMPLATE_STATUS.get(row["status"], "draft"),
        "description": row.get("description") or "",
        "owner": row.get("owner_name") or "未分配",
        "steps": int(row.get("step_count") or 0),
        "version": row.get("version_code") or "",
    }


def map_instance(row):
    total = int(row.get("total_tasks") or 0)
    done = int(row.get("done_tasks") or 0)
    return {
        "id": str(row["id"]),
        "templateId": str(row["template_id"]),
        "name": row["instance_name"],
        "department": row["department_name"],
        "status": INSTANCE_STATUS.get(row["status"], "active"),
        "current": row.get("current_step_name") or "未开始",
        "currentStepId": str(row["current_step_id"]) if row.get("current_step_id") else "",
        "owner": row.get("owner_name") or "未分配",
        "progress": f"{done}/{total}" if total else "0/0",
        "updated": format_datetime(row.get("updated_at") or row.get("started_at")),
        "cloudPath": row.get("cloud_path") or "",
    }
