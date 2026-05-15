import json
from datetime import datetime

from ..common.errors import APIError
from ..models.process import INSTANCE_STATUS, TASK_STATUS, TEMPLATE_STATUS
from ..repositories.process_repository import process_cursor as db_cursor
from ..schemas.process_schema import format_datetime, map_instance, map_template


def _dt(value):
    return format_datetime(value)


def _template_status(value):
    return TEMPLATE_STATUS.get(value, "draft")


def _instance_status(value):
    return INSTANCE_STATUS.get(value, "active")


def _task_status(value):
    return TASK_STATUS.get(value, "pending")


def list_templates():
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
              t.id,
              t.template_name,
              t.status,
              t.description,
              t.version_code,
              d.department_name,
              e.employee_name AS owner_name,
              COUNT(s.id) AS step_count
            FROM flow_templates t
            JOIN departments d ON d.id = t.department_id
            LEFT JOIN employees e ON e.id = t.default_owner_id
            LEFT JOIN flow_template_steps s ON s.template_id = t.id AND s.status = 1
            WHERE t.status <> -1
            GROUP BY t.id, t.template_name, t.status, t.description, t.version_code, d.department_name, e.employee_name
            ORDER BY t.updated_at DESC, t.id DESC
            """
        )
        return [_map_template(row) for row in cursor.fetchall()]


def get_template(template_id):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
              t.id,
              t.template_name,
              t.status,
              t.description,
              t.version_code,
              t.notify_type,
              t.archive_output_type,
              d.department_name,
              e.employee_name AS owner_name,
              COUNT(s.id) AS step_count
            FROM flow_templates t
            JOIN departments d ON d.id = t.department_id
            LEFT JOIN employees e ON e.id = t.default_owner_id
            LEFT JOIN flow_template_steps s ON s.template_id = t.id AND s.status = 1
            WHERE t.id = %s
            GROUP BY t.id, t.template_name, t.status, t.description, t.version_code, t.notify_type, t.archive_output_type, d.department_name, e.employee_name
            """,
            (template_id,),
        )
        template = cursor.fetchone()
        if not template:
            return None
        result = _map_template(template)
        result["notifyType"] = template.get("notify_type") or "微信机器人通知"
        result["archiveOutputType"] = template.get("archive_output_type") or "Word 查检表"
        result["stepDetails"] = list_template_steps(cursor, template_id)
        return result


def list_template_steps(cursor, template_id, instance_id=None):
    cursor.execute(
        """
        SELECT
          s.id,
          s.step_no,
          s.step_name,
          s.complete_rule,
          GROUP_CONCAT(DISTINCT e.employee_name ORDER BY a.sort_no SEPARATOR ',') AS assignees
        FROM flow_template_steps s
        LEFT JOIN flow_template_step_assignees a ON a.template_step_id = s.id AND a.assignee_type = 'employee'
        LEFT JOIN employees e ON e.id = a.assignee_id
        WHERE s.template_id = %s AND s.status = 1
        GROUP BY s.id, s.step_no, s.step_name, s.complete_rule
        ORDER BY s.step_no ASC
        """,
        (template_id,),
    )
    steps = []
    for row in cursor.fetchall():
        fields = list_step_fields(cursor, row["id"], instance_id)
        assignees = [name for name in (row.get("assignees") or "").split(",") if name]
        owner = "、".join(assignees) if assignees else "未分配"
        steps.append(
            {
                "id": str(row["id"]),
                "name": row["step_name"],
                "owner": owner,
                "rule": row.get("complete_rule") or "owner",
                "status": "pending",
                "fields": fields,
                "assignees": assignees,
                "tasks": [
                    {
                        "title": f"{row['step_name']}处理",
                        "owner": owner,
                        "status": "pending",
                    }
                ],
                "signatures": [],
            }
        )
    if steps:
        steps[0]["status"] = "current"
    return steps


def list_step_fields(cursor, template_step_id, instance_id=None):
    value_join = ""
    value_select = "NULL AS field_value"
    params = []
    if instance_id:
        value_select = "v.field_value"
        value_join = """
        LEFT JOIN flow_instance_field_values v
          ON v.instance_id = %s
         AND v.template_step_id = sf.template_step_id
         AND v.field_id = f.id
        """
        params.append(instance_id)
    params.append(template_step_id)
    cursor.execute(
        f"""
        SELECT
          f.id,
          f.field_name,
          f.field_type,
          COALESCE(sf.required_override, f.required) AS required,
          f.options_json,
          sf.default_value,
          {value_select}
        FROM flow_template_step_fields sf
        JOIN flow_fields f ON f.id = sf.field_id
        {value_join}
        WHERE sf.template_step_id = %s AND f.status = 1
        ORDER BY sf.sort_no ASC
        """,
        tuple(params),
    )
    fields = []
    for row in cursor.fetchall():
        options = _field_options(row.get("options_json"), row["field_name"], row["field_type"])
        field = {
            "id": str(row["id"]),
            "key": str(row["id"]),
            "label": row["field_name"],
            "type": row["field_type"],
            "required": bool(row["required"]),
            "value": row.get("field_value") if row.get("field_value") is not None else (row.get("default_value") or ""),
        }
        if options:
            field["options"] = options
        fields.append(field)
    return fields


def _field_options(options_json, field_name, field_type):
    if options_json:
        try:
            value = json.loads(options_json) if isinstance(options_json, str) else options_json
            if isinstance(value, list):
                return value
        except (TypeError, ValueError):
            return []
    if field_type not in {"select", "radio", "checkbox", "choice"}:
        return []
    defaults = {
        "销售区域": ["全球", "仅国内", "仅海外"],
        "产品分类": ["新品", "老产品新款"],
    }
    if field_name in defaults:
        return defaults[field_name]
    if field_name.startswith("是否"):
        return ["是", "否"]
    return []


def update_template(template_id, payload, operator_id=None):
    operator = _require_operator(operator_id)
    with db_cursor(commit=True) as cursor:
        _ensure_template_exists(cursor, template_id)
        values = _template_update_values(cursor, payload)
        if values:
            set_sql = ", ".join(f"{column} = %s" for column in values)
            cursor.execute(
                f"UPDATE flow_templates SET {set_sql} WHERE id = %s",
                tuple(values.values()) + (template_id,),
            )

        deleted_step_ids = payload.get("deletedStepIds") or []
        for raw_step_id in deleted_step_ids:
            if _is_int_like(raw_step_id):
                _delete_template_step(cursor, template_id, int(raw_step_id))

        if isinstance(payload.get("steps"), list):
            _save_template_steps(cursor, template_id, payload["steps"], operator)

        _write_log(cursor, "update_template", operator, "保存模板配置", "flow_template", template_id)
    return get_template(template_id)


def create_template(payload, operator_id=None):
    operator = _require_operator(operator_id)
    with db_cursor(commit=True) as cursor:
        name = (payload.get("name") or f"新建流程模板 {datetime.now().strftime('%Y%m%d%H%M')}").strip()
        department_id = payload.get("departmentId") or _resolve_department(cursor, payload.get("department") or _first_department_name(cursor))
        owner_id = payload.get("ownerId") or operator
        version_code = datetime.now().strftime("%Y%m%d%H%M%S%f")[:20]
        cursor.execute(
            """
            INSERT INTO flow_templates
              (template_name, department_id, status, description, default_owner_id, version_code, is_latest, notify_type, archive_output_type, created_by)
            VALUES (%s, %s, 0, %s, %s, %s, 1, %s, %s, %s)
            """,
            (
                name,
                department_id,
                payload.get("description") or "",
                owner_id,
                version_code,
                payload.get("notifyType") or "微信机器人通知",
                payload.get("archiveOutputType") or "Word 查检表",
                operator,
            ),
        )
        template_id = cursor.lastrowid
        _insert_template_step(
            cursor,
            template_id,
            {
                "name": "默认步骤",
                "owner": payload.get("owner") or "",
                "rule": "any",
                "fields": [{"label": "处理说明", "type": "textarea", "required": False}],
            },
            operator,
            1,
        )
        _write_log(cursor, "create_template", operator, "新增流程模板", "flow_template", template_id)
    return get_template(template_id)


def add_template_step(template_id, payload, operator_id=None):
    operator = _require_operator(operator_id)
    with db_cursor(commit=True) as cursor:
        _ensure_template_exists(cursor, template_id)
        step_id = _insert_template_step(cursor, template_id, payload, operator, step_no=_next_step_no(cursor, template_id))
        _write_log(cursor, "add_template_step", operator, "新增模板步骤", "flow_template_step", step_id)
    return get_template(template_id)


def update_template_step(template_id, step_id, payload, operator_id=None):
    operator = _require_operator(operator_id)
    with db_cursor(commit=True) as cursor:
        _ensure_step_belongs_to_template(cursor, template_id, step_id)
        _update_template_step(cursor, template_id, step_id, payload, operator, step_no=payload.get("stepNo"))
        _write_log(cursor, "update_template_step", operator, "更新模板步骤", "flow_template_step", step_id)
    return get_template(template_id)


def delete_template_step(template_id, step_id, operator_id=None):
    operator = _require_operator(operator_id)
    with db_cursor(commit=True) as cursor:
        _delete_template_step(cursor, template_id, step_id)
        _write_log(cursor, "delete_template_step", operator, "删除模板步骤", "flow_template_step", step_id)
    return get_template(template_id)


def _require_operator(operator_id):
    if not operator_id:
        raise APIError("登录状态已失效，请重新登录。", 401, "UNAUTHORIZED")
    return operator_id


def _ensure_template_exists(cursor, template_id):
    cursor.execute("SELECT id FROM flow_templates WHERE id = %s AND status <> -1", (template_id,))
    if not cursor.fetchone():
        raise APIError("模板不存在或已被删除。", 404, "TEMPLATE_NOT_FOUND")


def _ensure_step_belongs_to_template(cursor, template_id, step_id):
    cursor.execute(
        "SELECT id FROM flow_template_steps WHERE id = %s AND template_id = %s AND status = 1",
        (step_id, template_id),
    )
    if not cursor.fetchone():
        raise APIError("步骤不存在或不属于当前模板。", 404, "STEP_NOT_FOUND")


def _template_update_values(cursor, payload):
    values = {}
    if payload.get("name"):
        values["template_name"] = payload["name"].strip()
    if "description" in payload or "desc" in payload:
        values["description"] = payload.get("description") or payload.get("desc") or ""
    if payload.get("status") in {"active", "draft", "disabled"}:
        values["status"] = {"active": 1, "draft": 0, "disabled": -1}[payload["status"]]
    if payload.get("departmentId"):
        values["department_id"] = int(payload["departmentId"])
    elif payload.get("department"):
        values["department_id"] = _resolve_department(cursor, payload["department"])
    if payload.get("ownerId"):
        values["default_owner_id"] = int(payload["ownerId"])
    elif payload.get("owner"):
        values["default_owner_id"] = _resolve_employee(cursor, payload["owner"])
    if "notifyType" in payload:
        values["notify_type"] = payload.get("notifyType") or None
    if "archiveOutputType" in payload:
        values["archive_output_type"] = payload.get("archiveOutputType") or None
    return values


def _resolve_department(cursor, name):
    cursor.execute("SELECT id FROM departments WHERE department_name = %s AND status = 1 LIMIT 1", (name,))
    row = cursor.fetchone()
    if not row:
        raise APIError(f"部门不存在：{name}", 400, "DEPARTMENT_NOT_FOUND")
    return row["id"]


def _first_department_name(cursor):
    cursor.execute("SELECT department_name FROM departments WHERE status = 1 ORDER BY id ASC LIMIT 1")
    row = cursor.fetchone()
    if not row:
        raise APIError("没有可用部门，无法创建模板。", 400, "DEPARTMENT_NOT_FOUND", True)
    return row["department_name"]


def _resolve_employee(cursor, name):
    cursor.execute(
        "SELECT id FROM employees WHERE (employee_name = %s OR account = %s) AND status = 1 LIMIT 1",
        (name, name),
    )
    row = cursor.fetchone()
    if not row:
        raise APIError(f"负责人不存在：{name}", 400, "EMPLOYEE_NOT_FOUND")
    return row["id"]


def _resolve_assignees(cursor, step, operator_id):
    names = step.get("assignees") or []
    if not names and step.get("owner"):
        names = [step["owner"]]
    assignees = []
    for name in names:
        cursor.execute(
            "SELECT id FROM employees WHERE (employee_name = %s OR account = %s) AND status = 1 LIMIT 1",
            (name, name),
        )
        row = cursor.fetchone()
        if row:
            assignees.append(row["id"])
    if not assignees:
        assignees.append(operator_id)
    return list(dict.fromkeys(assignees))


def _next_step_no(cursor, template_id):
    cursor.execute(
        "SELECT COALESCE(MAX(step_no), 0) + 1 AS next_no FROM flow_template_steps WHERE template_id = %s AND status = 1",
        (template_id,),
    )
    return int(cursor.fetchone()["next_no"])


def _save_template_steps(cursor, template_id, steps, operator_id):
    existing_ids = [int(step["id"]) for step in steps if _is_int_like(step.get("id"))]
    if existing_ids:
        placeholders = ", ".join(["%s"] * len(existing_ids))
        cursor.execute(
            f"UPDATE flow_template_steps SET step_no = -step_no WHERE template_id = %s AND id IN ({placeholders})",
            tuple([template_id] + existing_ids),
        )
    for index, step in enumerate(steps, start=1):
        if _is_int_like(step.get("id")):
            _update_template_step(cursor, template_id, int(step["id"]), step, operator_id, step_no=index)
        else:
            _insert_template_step(cursor, template_id, step, operator_id, step_no=index)


def _insert_template_step(cursor, template_id, step, operator_id, step_no):
    step_name = (step.get("name") or "").strip()
    if not step_name:
        raise APIError("步骤名称不能为空。", 400, "VALIDATION_ERROR")
    cursor.execute(
        """
        INSERT INTO flow_template_steps (template_id, step_no, step_name, complete_rule, status)
        VALUES (%s, %s, %s, %s, 1)
        """,
        (template_id, step_no, step_name, step.get("rule") or "any"),
    )
    step_id = cursor.lastrowid
    _replace_step_assignees(cursor, step_id, _resolve_assignees(cursor, step, operator_id))
    _replace_step_fields(cursor, step_id, step.get("fields") or [])
    return step_id


def _update_template_step(cursor, template_id, step_id, step, operator_id, step_no=None):
    _ensure_step_belongs_to_template(cursor, template_id, step_id)
    values = {
        "step_name": (step.get("name") or "").strip(),
        "complete_rule": step.get("rule") or "any",
    }
    if not values["step_name"]:
        raise APIError("步骤名称不能为空。", 400, "VALIDATION_ERROR")
    if step_no:
        values["step_no"] = int(step_no)
    set_sql = ", ".join(f"{column} = %s" for column in values)
    cursor.execute(
        f"UPDATE flow_template_steps SET {set_sql} WHERE id = %s AND template_id = %s",
        tuple(values.values()) + (step_id, template_id),
    )
    _replace_step_assignees(cursor, step_id, _resolve_assignees(cursor, step, operator_id))
    _replace_step_fields(cursor, step_id, step.get("fields") or [])


def _delete_template_step(cursor, template_id, step_id):
    _ensure_step_belongs_to_template(cursor, template_id, step_id)
    cursor.execute(
        "SELECT COUNT(*) AS count FROM flow_template_steps WHERE template_id = %s AND status = 1",
        (template_id,),
    )
    if int(cursor.fetchone()["count"]) <= 1:
        raise APIError("模板至少需要保留一个步骤。", 400, "LAST_STEP_NOT_ALLOWED")
    cursor.execute(
        "UPDATE flow_template_steps SET status = 0, step_no = -id WHERE id = %s AND template_id = %s",
        (step_id, template_id),
    )
    if cursor.rowcount != 1:
        raise APIError("步骤不存在或不属于当前模板。", 404, "STEP_NOT_FOUND")
    cursor.execute(
        """
        SELECT id
        FROM flow_template_steps
        WHERE template_id = %s AND status = 1
        ORDER BY step_no ASC, id ASC
        """,
        (template_id,),
    )
    active_steps = cursor.fetchall()
    for index, row in enumerate(active_steps, start=1):
        cursor.execute("UPDATE flow_template_steps SET step_no = %s WHERE id = %s", (index, row["id"]))


def _replace_step_assignees(cursor, step_id, assignee_ids):
    cursor.execute("DELETE FROM flow_template_step_assignees WHERE template_step_id = %s", (step_id,))
    for index, assignee_id in enumerate(assignee_ids, start=1):
        cursor.execute(
            """
            INSERT INTO flow_template_step_assignees (template_step_id, assignee_type, assignee_id, sort_no)
            VALUES (%s, 'employee', %s, %s)
            """,
            (step_id, assignee_id, index),
        )


def _replace_step_fields(cursor, step_id, fields):
    cursor.execute("DELETE FROM flow_template_step_fields WHERE template_step_id = %s", (step_id,))
    for index, field in enumerate(fields, start=1):
        label = (field.get("label") or field.get("name") or "").strip()
        if not label:
            continue
        field_type = _normalize_field_type(field.get("type") or "text")
        options = field.get("options")
        cursor.execute(
            """
            INSERT INTO flow_fields (field_name, field_type, required, options_json, status)
            VALUES (%s, %s, %s, %s, 1)
            """,
            (label, field_type, 1 if field.get("required") else 0, json.dumps(options, ensure_ascii=False) if options else None),
        )
        cursor.execute(
            """
            INSERT INTO flow_template_step_fields (template_step_id, field_id, sort_no, required_override, default_value)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (step_id, cursor.lastrowid, index, 1 if field.get("required") else 0, field.get("value") or None),
        )


def _normalize_field_type(value):
    return {"choice": "select"}.get(value, value)


def _is_int_like(value):
    try:
        int(value)
        return True
    except (TypeError, ValueError):
        return False


def _write_log(cursor, action, operator_id, detail, target_type, target_id):
    cursor.execute(
        """
        INSERT INTO operation_logs (action, operator_id, detail, target_type, target_id)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (action, operator_id, detail, target_type, target_id),
    )


def list_instances(template_id=None):
    params = []
    conditions = ["i.status <> 0"]
    if template_id:
        conditions.append("i.template_id = %s")
        params.append(template_id)
    where = f"WHERE {' AND '.join(conditions)}"
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT
              i.id,
              i.template_id,
              i.instance_name,
              i.cloud_path,
              i.status,
              i.current_step_id,
              i.started_at,
              i.updated_at,
              t.template_name,
              d.department_name,
              e.employee_name AS owner_name,
              s.step_name AS current_step_name,
              COUNT(tasks.id) AS total_tasks,
              SUM(CASE WHEN tasks.status = 1 THEN 1 ELSE 0 END) AS done_tasks
            FROM flow_instances i
            JOIN flow_templates t ON t.id = i.template_id
            JOIN departments d ON d.id = t.department_id
            JOIN employees e ON e.id = i.initiator_id
            LEFT JOIN flow_template_steps s ON s.id = i.current_step_id
            LEFT JOIN flow_instance_tasks tasks ON tasks.instance_id = i.id
            {where}
            GROUP BY i.id, i.template_id, i.instance_name, i.cloud_path, i.status, i.current_step_id, i.started_at, i.updated_at,
                     t.template_name, d.department_name, e.employee_name, s.step_name
            ORDER BY i.updated_at DESC, i.id DESC
            """,
            tuple(params),
        )
        return [_map_instance(row) for row in cursor.fetchall()]


def get_instance(instance_id):
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT
              i.id,
              i.template_id,
              i.instance_name,
              i.cloud_path,
              i.status,
              i.current_step_id,
              i.started_at,
              i.updated_at,
              t.template_name,
              d.department_name,
              e.employee_name AS owner_name,
              s.step_name AS current_step_name,
              COUNT(tasks.id) AS total_tasks,
              SUM(CASE WHEN tasks.status = 1 THEN 1 ELSE 0 END) AS done_tasks
            FROM flow_instances i
            JOIN flow_templates t ON t.id = i.template_id
            JOIN departments d ON d.id = t.department_id
            JOIN employees e ON e.id = i.initiator_id
            LEFT JOIN flow_template_steps s ON s.id = i.current_step_id
            LEFT JOIN flow_instance_tasks tasks ON tasks.instance_id = i.id
            WHERE i.id = %s
            GROUP BY i.id, i.template_id, i.instance_name, i.cloud_path, i.status, i.current_step_id, i.started_at, i.updated_at,
                     t.template_name, d.department_name, e.employee_name, s.step_name
            """,
            (instance_id,),
        )
        row = cursor.fetchone()
        if not row:
            return None
        instance = _map_instance(row)
        instance["steps"] = list_instance_steps(cursor, instance_id, instance["templateId"], instance.get("currentStepId"))
        instance["logs"] = list_logs(cursor, instance_id)
        return instance


def list_instance_steps(cursor, instance_id, template_id, current_step_id=None):
    steps = list_template_steps(cursor, template_id, instance_id)
    for step in steps:
        step["status"] = "current" if step["id"] == str(current_step_id) else "pending"
    cursor.execute(
        """
        SELECT tasks.id, tasks.template_step_id, tasks.assignee_id, tasks.status, tasks.completed_at, e.employee_name
        FROM flow_instance_tasks tasks
        LEFT JOIN employees e ON e.id = tasks.assignee_id
        WHERE instance_id = %s
        """,
        (instance_id,),
    )
    task_rows = cursor.fetchall()
    by_step = {}
    for row in task_rows:
        by_step.setdefault(str(row["template_step_id"]), []).append(row)
    for step in steps:
        rows = by_step.get(step["id"], [])
        if rows:
            step["tasks"] = [
                {
                    "id": str(row["id"]),
                    "title": f"{step['name']}处理",
                    "owner": row.get("employee_name") or str(row["assignee_id"]),
                    "status": _task_status(row["status"]),
                }
                for row in rows
            ]
            if all(row["status"] == 1 for row in rows):
                step["status"] = "done"
            elif step["id"] == str(current_step_id):
                step["status"] = "current"
            else:
                step["status"] = "pending"
    return steps


def update_instance_step_fields(instance_id, step_id, payload, operator_id=None, can_manage=False):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401, "UNAUTHORIZED")
    values = payload.get("values") or {}
    if not isinstance(values, dict):
        raise APIError("字段值格式不正确。", 400, "VALIDATION_ERROR")
    with db_cursor(commit=True) as cursor:
        _ensure_step_access(cursor, instance_id, step_id, operator, can_manage, require_current=True)
        cursor.execute(
            """
            SELECT f.id
            FROM flow_template_step_fields sf
            JOIN flow_fields f ON f.id = sf.field_id AND f.status = 1
            WHERE sf.template_step_id = %s
            """,
            (step_id,),
        )
        allowed_field_ids = {str(row["id"]) for row in cursor.fetchall()}
        for field_id, field_value in values.items():
            if str(field_id) not in allowed_field_ids:
                raise APIError("字段不属于当前步骤。", 400, "VALIDATION_ERROR")
            cursor.execute(
                """
                INSERT INTO flow_instance_field_values
                  (instance_id, template_step_id, field_id, field_value, updated_by)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE
                  field_value = VALUES(field_value),
                  updated_by = VALUES(updated_by)
                """,
                (instance_id, step_id, int(field_id), "" if field_value is None else str(field_value), operator),
            )
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('update_instance_fields', %s, %s, %s, 'flow_template_step', %s)
            """,
            (operator, "保存步骤填写内容", instance_id, step_id),
        )
    return get_instance(instance_id)


def delete_instance(instance_id, operator_id=None):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401, "UNAUTHORIZED")
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            "UPDATE flow_instances SET status = 0, current_step_id = NULL WHERE id = %s AND status <> 0",
            (instance_id,),
        )
        if cursor.rowcount != 1:
            raise APIError("流程实例不存在或已删除。", 404, "INSTANCE_NOT_FOUND")
        cursor.execute(
            "UPDATE flow_instance_tasks SET status = 2 WHERE instance_id = %s AND status = 0",
            (instance_id,),
        )
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('delete_instance', %s, %s, %s, 'flow_instance', %s)
            """,
            (operator, "删除流程实例", instance_id, instance_id),
        )
    return {"id": str(instance_id), "deleted": True}


def update_instance_step_assignment(instance_id, step_id, payload, operator_id=None, can_manage=False):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401, "UNAUTHORIZED")
    rule = payload.get("rule") or "any"
    assignee_names = payload.get("assignees") or []
    if not isinstance(assignee_names, list) or not assignee_names:
        raise APIError("请至少选择一个负责人。", 400, "VALIDATION_ERROR")
    with db_cursor(commit=True) as cursor:
        _ensure_step_access(cursor, instance_id, step_id, operator, can_manage, require_current=True)
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM flow_instance_tasks
            WHERE instance_id = %s AND template_step_id = %s AND status = 1
            """,
            (instance_id, step_id),
        )
        if cursor.fetchone()["count"] > 0:
            raise APIError("已完成的步骤不能重新分配。", 400, "VALIDATION_ERROR")

        assignee_ids = []
        for name in assignee_names:
            employee_id = _resolve_employee(cursor, name)
            assignee_ids.append(employee_id)
        assignee_ids = list(dict.fromkeys(assignee_ids))

        cursor.execute(
            "UPDATE flow_template_steps SET complete_rule = %s WHERE id = %s",
            (rule, step_id),
        )
        cursor.execute(
            "DELETE FROM flow_instance_tasks WHERE instance_id = %s AND template_step_id = %s AND status = 0",
            (instance_id, step_id),
        )
        for assignee_id in assignee_ids:
            cursor.execute(
                """
                INSERT INTO flow_instance_tasks (instance_id, template_step_id, assignee_id, status)
                VALUES (%s, %s, %s, 0)
                ON DUPLICATE KEY UPDATE status = VALUES(status)
                """,
                (instance_id, step_id, assignee_id),
            )
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('update_assignment', %s, %s, %s, 'flow_template_step', %s)
            """,
            (operator, f"调整步骤负责人：{', '.join(assignee_names)}；完成规则：{rule}", instance_id, step_id),
        )
    return get_instance(instance_id)


def record_step_revision(instance_id, step_id, payload, operator_id=None, can_manage=False):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401, "UNAUTHORIZED")
    message = (payload.get("message") or "保存已完成内容修订").strip()
    with db_cursor(commit=True) as cursor:
        _ensure_step_access(cursor, instance_id, step_id, operator, can_manage)
        missing = _missing_required_fields(cursor, instance_id, step_id)
        if missing:
            raise APIError(f"请先填写必填项：{'、'.join(missing)}", 400, "VALIDATION_ERROR")
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('revise_step', %s, %s, %s, 'flow_template_step', %s)
            """,
            (operator, message, instance_id, step_id),
        )
    return get_instance(instance_id)


def generate_checklist(instance_id, operator_id=None):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401, "UNAUTHORIZED")
    instance = get_instance(instance_id)
    if not instance:
        raise APIError("instance not found", 404, "INSTANCE_NOT_FOUND")
    with db_cursor(commit=True) as cursor:
        stored_name = f"checklist-{instance_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}.docx"
        file_path = f"generated://checklists/{stored_name}"
        cursor.execute(
            """
            INSERT INTO attachments
              (instance_id, attachment_type, original_file_name, stored_file_name, file_path, uploaded_by)
            VALUES (%s, 2, %s, %s, %s, %s)
            """,
            (instance_id, f"{instance['name']}-查检表.docx", stored_name, file_path, operator),
        )
        attachment_id = cursor.lastrowid
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('generate_checklist', %s, %s, %s, 'attachment', %s)
            """,
            (operator, "生成流程查检表", instance_id, attachment_id),
        )
    refreshed = get_instance(instance_id)
    refreshed["attachment"] = {
        "id": str(attachment_id),
        "filePath": file_path,
        "fileName": f"{instance['name']}-查检表.docx",
    }
    return refreshed


def _ensure_step_access(cursor, instance_id, step_id, operator_id, can_manage=False, require_current=False):
    cursor.execute(
        """
        SELECT i.id, i.current_step_id
        FROM flow_instances i
        JOIN flow_template_steps s ON s.id = %s AND s.template_id = i.template_id
        WHERE i.id = %s
        """,
        (step_id, instance_id),
    )
    instance = cursor.fetchone()
    if not instance:
        raise APIError("步骤不属于当前流程实例。", 400, "VALIDATION_ERROR")
    if require_current and instance["current_step_id"] != step_id:
        raise APIError("流程还未走到该步骤，不能填写或处理。", 400, "VALIDATION_ERROR")
    if can_manage:
        return
    cursor.execute(
        """
        SELECT COUNT(*) AS count
        FROM flow_instance_tasks
        WHERE instance_id = %s AND template_step_id = %s AND assignee_id = %s
        """,
        (instance_id, step_id, operator_id),
    )
    if cursor.fetchone()["count"] == 0:
        raise APIError("当前账号不能处理该步骤。", 403, "FORBIDDEN")


def _missing_required_fields(cursor, instance_id, step_id):
    cursor.execute(
        """
        SELECT f.field_name
        FROM flow_template_step_fields sf
        JOIN flow_fields f ON f.id = sf.field_id AND f.status = 1
        LEFT JOIN flow_instance_field_values v
          ON v.instance_id = %s
         AND v.template_step_id = sf.template_step_id
         AND v.field_id = f.id
        WHERE sf.template_step_id = %s
          AND COALESCE(sf.required_override, f.required) = 1
          AND (v.field_value IS NULL OR TRIM(v.field_value) = '')
        ORDER BY sf.sort_no ASC
        """,
        (instance_id, step_id),
    )
    return [row["field_name"] for row in cursor.fetchall()]


def create_instance(template_id, name, initiator_id=None, cloud_path=""):
    operator_id = initiator_id
    if not operator_id:
        raise APIError("operator is required", 401)
    with db_cursor(commit=True) as cursor:
        steps = list_template_steps(cursor, template_id)
        if not steps:
            raise ValueError("模板没有可用步骤")
        current_step_id = int(steps[0]["id"])
        cursor.execute(
            """
            INSERT INTO flow_instances (template_id, instance_name, cloud_path, initiator_id, current_step_id, status)
            VALUES (%s, %s, %s, %s, %s, 1)
            """,
            (template_id, name, cloud_path, operator_id, current_step_id),
        )
        instance_id = cursor.lastrowid
        cursor.execute(
            """
            SELECT s.id AS step_id, COALESCE(a.assignee_id, %s) AS assignee_id
            FROM flow_template_steps s
            LEFT JOIN flow_template_step_assignees a ON a.template_step_id = s.id AND a.assignee_type = 'employee'
            WHERE s.template_id = %s AND s.status = 1
            ORDER BY s.step_no ASC, a.sort_no ASC
            """,
            (operator_id, template_id),
        )
        for row in cursor.fetchall():
            cursor.execute(
                """
                INSERT IGNORE INTO flow_instance_tasks (instance_id, template_step_id, assignee_id, status)
                VALUES (%s, %s, %s, 0)
                """,
                (instance_id, row["step_id"], row["assignee_id"]),
            )
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('create_instance', %s, %s, %s, 'flow_instance', %s)
            """,
            (operator_id, f"发起流程：{name}；共享盘：{cloud_path}", instance_id, instance_id),
        )
    return get_instance(instance_id)


def update_instance(instance_id, payload, operator_id=None):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401)
    allowed = {}
    if payload.get("name"):
        allowed["instance_name"] = payload["name"]
    if "cloudPath" in payload:
        allowed["cloud_path"] = payload.get("cloudPath") or ""
    if not allowed:
        return get_instance(instance_id)
    set_sql = ", ".join(f"{key} = %s" for key in allowed)
    values = list(allowed.values()) + [instance_id]
    with db_cursor(commit=True) as cursor:
        cursor.execute(f"UPDATE flow_instances SET {set_sql} WHERE id = %s", tuple(values))
        if cursor.rowcount != 1:
            raise APIError("instance not found", 404)
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('update_instance', %s, %s, %s, 'flow_instance', %s)
            """,
            (operator, "更新流程实例信息", instance_id, instance_id),
        )
    return get_instance(instance_id)


def complete_task(instance_id, task_id, operator_id=None, can_manage=False):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401)
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT id, assignee_id, template_step_id
            FROM flow_instance_tasks
            WHERE instance_id = %s AND id = %s
            """,
            (instance_id, task_id),
        )
        task = cursor.fetchone()
        if not task:
            raise APIError("task not found", 404)
        if not can_manage and task["assignee_id"] != operator:
            raise APIError("task does not belong to current user", 403)
        missing = _missing_required_fields(cursor, instance_id, task["template_step_id"])
        if missing:
            raise APIError(f"请先填写必填项：{'、'.join(missing)}", 400, "VALIDATION_ERROR")
        cursor.execute(
            "UPDATE flow_instance_tasks SET status = 1, completed_at = NOW() WHERE instance_id = %s AND id = %s AND assignee_id = %s",
            (instance_id, task_id, task["assignee_id"]),
        )
        if cursor.rowcount != 1:
            raise APIError("task not found", 404)
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('complete_task', %s, %s, %s, 'flow_instance_task', %s)
            """,
            (operator, f"完成任务 {task_id}", instance_id, task_id),
        )
    return get_instance(instance_id)


def complete_step(instance_id, step_id, operator_id=None, can_manage=False):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401)
    with db_cursor(commit=True) as cursor:
        cursor.execute(
            """
            SELECT i.id, i.template_id, i.current_step_id
            FROM flow_instances i
            JOIN flow_template_steps s ON s.id = %s AND s.template_id = i.template_id
            WHERE i.id = %s
            """,
            (step_id, instance_id),
        )
        instance = cursor.fetchone()
        if not instance:
            raise APIError("step does not belong to this instance", 400)
        if instance["current_step_id"] != step_id:
            raise APIError("step is not the current step", 400)
        cursor.execute(
            """
            SELECT COUNT(*) AS count
            FROM flow_instance_tasks
            WHERE instance_id = %s AND template_step_id = %s AND assignee_id = %s
            """,
            (instance_id, step_id, operator),
        )
        if not can_manage and cursor.fetchone()["count"] == 0:
            raise APIError("current user cannot complete this step", 403)
        missing = _missing_required_fields(cursor, instance_id, step_id)
        if missing:
            raise APIError(f"请先填写必填项：{'、'.join(missing)}", 400, "VALIDATION_ERROR")
        cursor.execute(
            "UPDATE flow_instance_tasks SET status = 1, completed_at = NOW() WHERE instance_id = %s AND template_step_id = %s",
            (instance_id, step_id),
        )
        if cursor.rowcount < 1:
            raise APIError("step has no tasks", 404)
        cursor.execute(
            """
            SELECT next_step.id
            FROM flow_instances i
            JOIN flow_template_steps current_step ON current_step.id = %s
            JOIN flow_template_steps next_step
              ON next_step.template_id = i.template_id
             AND next_step.step_no > current_step.step_no
             AND next_step.status = 1
            WHERE i.id = %s
            ORDER BY next_step.step_no ASC
            LIMIT 1
            """,
            (step_id, instance_id),
        )
        next_step = cursor.fetchone()
        if next_step:
            cursor.execute("UPDATE flow_instances SET current_step_id = %s WHERE id = %s", (next_step["id"], instance_id))
        else:
            cursor.execute("UPDATE flow_instances SET current_step_id = NULL, status = 2, completed_at = NOW() WHERE id = %s", (instance_id,))
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('complete_step', %s, %s, %s, 'flow_template_step', %s)
            """,
            (operator, f"完成步骤 {step_id}", instance_id, step_id),
        )
    return get_instance(instance_id)


def remind_instance(instance_id, message, operator_id=None):
    operator = operator_id
    if not operator:
        raise APIError("operator is required", 401)
    with db_cursor(commit=True) as cursor:
        cursor.execute("SELECT id FROM flow_instances WHERE id = %s", (instance_id,))
        if not cursor.fetchone():
            raise APIError("instance not found", 404)
        cursor.execute(
            """
            INSERT INTO operation_logs (action, operator_id, detail, instance_id, target_type, target_id)
            VALUES ('remind', %s, %s, %s, 'flow_instance', %s)
            """,
            (operator, message or "发送催办提醒", instance_id, instance_id),
        )
    return {"ok": True}


def list_logs(cursor, instance_id):
    cursor.execute(
        """
        SELECT action, detail, operated_at
        FROM operation_logs
        WHERE instance_id = %s
        ORDER BY operated_at DESC, id DESC
        LIMIT 50
        """,
        (instance_id,),
    )
    return [{"title": row["action"], "text": row.get("detail") or "", "time": _dt(row["operated_at"])} for row in cursor.fetchall()]


def _map_template(row):
    return map_template(row)


def _map_instance(row):
    return map_instance(row)
