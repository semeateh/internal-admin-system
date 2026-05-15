from flask import jsonify


DEVELOPER_HINT = "请联系开发人员/管理员。"


def api_success(data=None, message="操作成功。", code="OK", status=200):
    payload = {
        "ok": True,
        "code": code,
        "message": message,
    }
    if data is not None:
        payload["data"] = data
    return jsonify(payload), status


def api_error(message, status=400, code="BAD_REQUEST", developer_hint=False):
    payload = {
        "ok": False,
        "code": code,
        "message": message,
    }
    if developer_hint:
        payload["developerHint"] = DEVELOPER_HINT
    return jsonify(payload), status
