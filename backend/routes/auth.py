from flask import Blueprint, g, request

from ..auth import create_token, load_user_by_account, public_user, require_auth, verify_password
from ..responses import api_error, api_success

auth_bp = Blueprint("auth", __name__, url_prefix="/api/auth")


@auth_bp.post("/login")
def login():
    payload = request.get_json(silent=True) or {}
    account = (payload.get("account") or "").strip()
    password = payload.get("password") or ""
    if not account or not password:
        return api_error("请输入账号和密码。", 400, "LOGIN_FIELDS_REQUIRED")

    user = load_user_by_account(account)
    if not user or not verify_password(password, user["password_hash"]):
        return api_error("账号或密码错误。", 401, "INVALID_CREDENTIALS")

    return api_success({"token": create_token(user), "user": public_user(user)}, "登录成功。", "LOGIN_OK")


@auth_bp.get("/me")
@require_auth
def me():
    return api_success(g.current_user, "当前用户信息已获取。", "AUTH_ME_OK")
