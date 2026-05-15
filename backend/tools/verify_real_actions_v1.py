import pathlib
import sys

BACKEND_ROOT = pathlib.Path(__file__).resolve().parents[1]
REPO_ROOT = BACKEND_ROOT.parent
sys.path.insert(0, str(BACKEND_ROOT))

from app import create_app
from app.db import db_cursor


app = create_app()


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def login(client, account):
    response = client.post("/api/auth/login", json={"account": account, "password": "123456"})
    body = response.get_json()
    require(response.status_code == 200, f"{account} login failed: {body}")
    return body["data"]["user"], {"Authorization": f"Bearer {body['data']['token']}"}


def cleanup(instance_id):
    if not instance_id:
        return
    with db_cursor(commit=True) as cursor:
        cursor.execute("DELETE FROM attachments WHERE instance_id = %s", (instance_id,))
        cursor.execute("DELETE FROM flow_instance_field_values WHERE instance_id = %s", (instance_id,))
        cursor.execute("DELETE FROM flow_instance_tasks WHERE instance_id = %s", (instance_id,))
        cursor.execute("DELETE FROM operation_logs WHERE instance_id = %s", (instance_id,))
        cursor.execute("DELETE FROM flow_instances WHERE id = %s", (instance_id,))


def main():
    client = app.test_client()
    admin_user, admin_headers = login(client, "admin")
    zak_user, zak_headers = login(client, "zak")
    instance_id = None
    try:
        require("flow.template.manage" in admin_user["permissions"], "admin should manage templates")
        require("flow.template.manage" not in zak_user["permissions"], "zak should not manage templates")

        templates = client.get("/api/flow/templates", headers=admin_headers).get_json()["data"]["items"]
        template_id = next(item["id"] for item in templates if item["status"] == "active")
        created = client.post(
            "/api/flow/instances",
            headers=admin_headers,
            json={"templateId": template_id, "name": "Codex 真实按钮验证", "cloudPath": r"\\share\\codex"},
        )
        instance = created.get_json()["data"]
        instance_id = instance["id"]
        first_step = instance["steps"][0]

        assign = client.put(
            f"/api/flow/instances/{instance_id}/steps/{first_step['id']}/assignment",
            headers=admin_headers,
            json={"assignees": ["zak"], "rule": "any"},
        )
        assign_body = assign.get_json()
        require(assign.status_code == 200, f"assignment must persist: {assign_body}")
        assigned_step = assign_body["data"]["steps"][0]
        require(assigned_step["tasks"][0]["owner"] == "Zak", f"assignment did not create Zak task: {assigned_step}")

        second_step = assign_body["data"]["steps"][1]
        blocked_fields = client.put(
            f"/api/flow/instances/{instance_id}/steps/{second_step['id']}/fields",
            headers=zak_headers,
            json={"values": {second_step["fields"][0]["id"]: "zak should not write this"}},
        )
        blocked_fields_body = blocked_fields.get_json()
        require(blocked_fields.status_code in {400, 403}, f"unavailable step fields must not be editable: {blocked_fields_body}")
        require(blocked_fields_body["code"] in {"FORBIDDEN", "VALIDATION_ERROR"}, f"step field write should be blocked clearly: {blocked_fields_body}")

        future_zak_step = next(
            step for step in assign_body["data"]["steps"]
            if step["status"] == "pending" and any(task["owner"] == "Zak" for task in step["tasks"])
        )
        blocked_future_fields = client.put(
            f"/api/flow/instances/{instance_id}/steps/{future_zak_step['id']}/fields",
            headers=zak_headers,
            json={"values": {future_zak_step["fields"][0]["id"]: "zak should not write future step"}},
        )
        blocked_future_fields_body = blocked_future_fields.get_json()
        require(blocked_future_fields.status_code == 400, f"pending step fields must not be editable: {blocked_future_fields_body}")
        require(blocked_future_fields_body["code"] == "VALIDATION_ERROR", f"pending step should return validation error: {blocked_future_fields_body}")

        empty_revision = client.post(
            f"/api/flow/instances/{instance_id}/steps/{first_step['id']}/revision",
            headers=zak_headers,
            json={"message": "required field missing revision"},
        )
        empty_revision_body = empty_revision.get_json()
        require(empty_revision.status_code == 400, f"revision must reject missing required fields: {empty_revision_body}")
        require(empty_revision_body["code"] == "VALIDATION_ERROR", f"revision should return validation error: {empty_revision_body}")

        required_values = {
            field["id"]: f"revision-value-{field['id']}"
            for field in first_step["fields"]
            if field.get("required")
        }
        saved_fields = client.put(
            f"/api/flow/instances/{instance_id}/steps/{first_step['id']}/fields",
            headers=zak_headers,
            json={"values": required_values},
        )
        saved_fields_body = saved_fields.get_json()
        require(saved_fields.status_code == 200, f"required fields must save before revision: {saved_fields_body}")

        revision = client.post(
            f"/api/flow/instances/{instance_id}/steps/{first_step['id']}/revision",
            headers=zak_headers,
            json={"message": "补充修订说明"},
        )
        revision_body = revision.get_json()
        require(revision.status_code == 200, f"revision must be recorded: {revision_body}")
        require(any("补充修订说明" in log["text"] for log in revision_body["data"]["logs"]), "revision log missing")

        checklist = client.post(f"/api/flow/instances/{instance_id}/checklist", headers=admin_headers)
        checklist_body = checklist.get_json()
        require(checklist.status_code == 200, f"checklist generation must be real: {checklist_body}")
        require(checklist_body["data"]["attachment"]["filePath"].startswith("generated://checklists/"), "checklist attachment path missing")

        forbidden_delete = client.delete(f"/api/flow/instances/{instance_id}", headers=zak_headers)
        forbidden_delete_body = forbidden_delete.get_json()
        require(forbidden_delete.status_code == 403, f"employee must not delete instance: {forbidden_delete_body}")

        deleted = client.delete(f"/api/flow/instances/{instance_id}", headers=admin_headers)
        deleted_body = deleted.get_json()
        require(deleted.status_code == 200, f"admin must delete instance: {deleted_body}")
        require(deleted_body["code"] == "INSTANCE_DELETED", f"delete should return clear code: {deleted_body}")
        listed_after_delete = client.get("/api/flow/instances", headers=admin_headers).get_json()["data"]["items"]
        require(not any(item["id"] == str(instance_id) for item in listed_after_delete), "deleted instance must be hidden from lists")

        directory = client.get("/api/directory/people", headers=admin_headers)
        directory_body = directory.get_json()
        require(directory.status_code == 200, f"directory must be available: {directory_body}")
        require("Zak" in directory_body["data"]["people"], "directory people should come from database")
        require(isinstance(directory_body["data"]["groups"], dict), "directory groups should be a mapping")

        app_vue = (REPO_ROOT / "frontend" / "src" / "App.vue").read_text(encoding="utf-8")
        flow_detail = (REPO_ROOT / "frontend" / "src" / "views" / "process" / "ProcessDetail.vue").read_text(encoding="utf-8")
        require("已切回本地演示" not in app_vue, "API failure must not fall back to local demo")
        require("mockTemplates" not in app_vue and "mockInstances" not in app_vue and "mockSteps" not in app_vue, "App must not initialize with mock business data")
        require("PlaceholderModule" not in app_vue, "placeholder module must not be routed")
        require("已模拟催办" not in flow_detail and "模拟微信机器人通知" not in flow_detail, "remind UI must not say simulated")
        require("$message.success('已生成产品 Release 查检表。')" not in app_vue, "generate checklist button must call API")
    finally:
        cleanup(instance_id)

    print("Real actions v1 verified")


if __name__ == "__main__":
    main()
