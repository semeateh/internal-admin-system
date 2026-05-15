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
    return {"Authorization": f"Bearer {body['data']['token']}"}


def main():
    client = app.test_client()
    admin_headers = login(client, "admin")
    zak_headers = login(client, "zak")
    instance_id = None

    templates_response = client.get("/api/flow/templates", headers=admin_headers)
    templates = templates_response.get_json()["data"]["items"]
    template_id = None
    for template in templates:
        detail_response = client.get(f"/api/flow/templates/{template['id']}", headers=admin_headers)
        detail = detail_response.get_json()["data"]
        first_step = (detail.get("stepDetails") or [None])[0]
        if first_step and any(field.get("required") for field in first_step.get("fields", [])):
            template_id = template["id"]
            break
    require(template_id, "no template with required fields found")

    instance_response = client.post(
        "/api/flow/instances",
        headers=admin_headers,
        json={
            "templateId": template_id,
            "name": "Codex 字段同步验证",
            "cloudPath": "",
        },
    )
    instance_body = instance_response.get_json()
    require(instance_response.status_code == 201, f"create instance failed: {instance_body}")
    instance = instance_body["data"]
    instance_id = instance["id"]
    first_step = instance["steps"][0]
    required_fields = [field for field in first_step["fields"] if field.get("required")]
    require(required_fields, "first step should expose required fields")
    require(any(field.get("options") for field in first_step["fields"]), "select fields should include options")

    task_id = first_step["tasks"][0]["id"]
    reject_response = client.post(
        f"/api/flow/instances/{instance['id']}/tasks/{task_id}/complete",
        headers=zak_headers,
    )
    reject_body = reject_response.get_json()
    require(reject_response.status_code == 400, f"required fields should block task completion: {reject_body}")
    require(reject_body.get("code") == "VALIDATION_ERROR", f"unexpected validation code: {reject_body}")

    values = {field["id"]: f"验证值-{field['id']}" for field in required_fields}
    save_response = client.put(
        f"/api/flow/instances/{instance['id']}/steps/{first_step['id']}/fields",
        headers=admin_headers,
        json={"values": values},
    )
    save_body = save_response.get_json()
    require(save_response.status_code == 200, f"save fields failed: {save_body}")

    zak_detail_response = client.get(f"/api/flow/instances/{instance['id']}", headers=zak_headers)
    zak_detail = zak_detail_response.get_json()["data"]
    zak_first_step = zak_detail["steps"][0]
    for field in zak_first_step["fields"]:
        if field["id"] in values:
            require(field.get("value") == values[field["id"]], f"field value did not sync for {field['label']}")

    complete_response = client.post(
        f"/api/flow/instances/{instance['id']}/tasks/{task_id}/complete",
        headers=zak_headers,
    )
    complete_body = complete_response.get_json()
    require(complete_response.status_code == 200, f"complete task failed after filling fields: {complete_body}")

    app_vue = open(REPO_ROOT / "frontend" / "src" / "App.vue", encoding="utf-8").read()
    require("重置演示" not in app_vue and "resetDetail" not in app_vue, "demo reset control should be removed")

    print("Flow detail real scenario verified")

    if instance_id:
        with db_cursor(commit=True) as cursor:
            cursor.execute("DELETE FROM flow_instance_field_values WHERE instance_id = %s", (instance_id,))
            cursor.execute("DELETE FROM flow_instance_tasks WHERE instance_id = %s", (instance_id,))
            cursor.execute("DELETE FROM operation_logs WHERE instance_id = %s", (instance_id,))
            cursor.execute("DELETE FROM flow_instances WHERE id = %s", (instance_id,))


if __name__ == "__main__":
    main()
