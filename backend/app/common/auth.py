from datetime import datetime, timedelta, timezone
from functools import wraps

import bcrypt
import jwt
from flask import g, request

from ..config import config
from ..db import db_cursor
from .responses import api_error


def _load_user_by_clause(where_sql, params):
    with db_cursor() as cursor:
        cursor.execute(
            f"""
            SELECT id, account, password_hash, employee_name, status
            FROM employees
            WHERE {where_sql}
            LIMIT 1
            """,
            params,
        )
        user = cursor.fetchone()
        if not user or user["status"] != 1:
            return None

        cursor.execute(
            """
            SELECT r.role_name, p.permission_code
            FROM employee_roles er
            JOIN roles r ON r.id = er.role_id AND r.status = 1
            LEFT JOIN role_permissions rp ON rp.role_id = r.id
            LEFT JOIN permissions p ON p.id = rp.permission_id AND p.status = 1
            WHERE er.employee_id = %s
            """,
            (user["id"],),
        )
        rows = cursor.fetchall()

    roles = sorted({row["role_name"] for row in rows if row.get("role_name")})
    permissions = sorted({row["permission_code"] for row in rows if row.get("permission_code")})
    return {
        "id": user["id"],
        "account": user["account"],
        "name": user["employee_name"],
        "password_hash": user["password_hash"],
        "roles": roles,
        "permissions": permissions,
    }


def load_user_by_account(account):
    return _load_user_by_clause("account = %s", (account,))


def load_user_by_id(user_id):
    return _load_user_by_clause("id = %s", (user_id,))


def public_user(user):
    return {
        "id": user["id"],
        "account": user["account"],
        "name": user["name"],
        "roles": user.get("roles", []),
        "permissions": user.get("permissions", []),
    }


def verify_password(password, password_hash):
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def create_token(user):
    now = datetime.now(timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "account": user["account"],
        "iat": now,
        "exp": now + timedelta(minutes=config.JWT_EXPIRE_MINUTES),
    }
    return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)


def _unauthorized(message="Unauthorized"):
    return api_error(message, 401, "UNAUTHORIZED")


def require_auth(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        header = request.headers.get("Authorization", "")
        if not header.startswith("Bearer "):
            return _unauthorized()
        token = header.removeprefix("Bearer ").strip()
        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        except jwt.PyJWTError:
            return _unauthorized("Invalid or expired token")
        user = load_user_by_id(payload.get("sub"))
        if not user:
            return _unauthorized("User not found")
        g.current_user = public_user(user)
        return func(*args, **kwargs)

    return wrapper


def has_permission(user, code):
    return code in set(user.get("permissions", []))


def require_permission(*codes):
    def decorator(func):
        @require_auth
        @wraps(func)
        def wrapper(*args, **kwargs):
            if any(has_permission(g.current_user, code) for code in codes):
                return func(*args, **kwargs)
            return api_error("当前账号没有操作权限。", 403, "FORBIDDEN")

        return wrapper

    return decorator
