#!/usr/bin/env python
"""
Password operation tool for internal-admin-system.

用途：
1. 生成 bcrypt 密码哈希
2. 校验明文密码是否匹配数据库中的 password_hash
3. 重置某个员工账号的密码

安装依赖：
    python -m pip install bcrypt mysql-connector-python python-dotenv

生成密码哈希：
    python tools/password_tool.py hash --password 123456

校验密码：
    python tools/password_tool.py verify --password 123456 --hash "$2b$12$..."

重置账号密码：
    python tools/password_tool.py reset --account admin --password 123456

重置账号密码并要求下次登录修改：
    python tools/password_tool.py reset --account zhangsan --password 123456 --must-change

数据库连接配置：
新系统读取自己目录下的 .env。
可以从 ownServer/.env 复制 DB_HOST、DB_USER、DB_PASSWORD，
然后把 DB_NAME 改成新后台系统数据库名。

    DB_HOST=127.0.0.1
    DB_USER=root
    DB_PASSWORD=your-password
    DB_NAME=internal_admin_system
"""

from __future__ import annotations

import argparse
import os
import sys
from getpass import getpass

try:
    import bcrypt
except ImportError:
    print("缺少依赖 bcrypt，请先执行：python -m pip install bcrypt", file=sys.stderr)
    raise


def load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv()


def env(name: str, fallback: str | None = None) -> str | None:
    value = os.getenv(name)
    if value is None or value == "":
        return fallback
    return value


def get_password(args: argparse.Namespace) -> str:
    if args.password:
        return args.password
    first = getpass("请输入密码：")
    second = getpass("请再次输入密码：")
    if first != second:
        raise SystemExit("两次输入不一致。")
    if not first:
        raise SystemExit("密码不能为空。")
    return first


def hash_password(password: str, rounds: int) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=rounds)).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))


def connect_database():
    try:
        import mysql.connector
    except ImportError:
        print("缺少依赖 mysql-connector-python，请先执行：python -m pip install mysql-connector-python", file=sys.stderr)
        raise

    load_dotenv_if_available()

    host = env("DB_HOST")
    user = env("DB_USER")
    password = env("DB_PASSWORD")
    database = env("DB_NAME", "internal_admin_system")

    missing = [name for name, value in {
        "DB_HOST": host,
        "DB_USER": user,
        "DB_PASSWORD": password,
        "DB_NAME": database,
    }.items() if value is None]
    if missing:
        raise SystemExit(f"数据库配置缺失：{', '.join(missing)}")

    return mysql.connector.connect(
        host=host,
        user=user,
        password=password,
        database=database,
        autocommit=False,
        connection_timeout=5,
    )


def command_hash(args: argparse.Namespace) -> int:
    password = get_password(args)
    print(hash_password(password, args.rounds))
    return 0


def command_verify(args: argparse.Namespace) -> int:
    password = get_password(args)
    ok = verify_password(password, args.password_hash)
    print("匹配" if ok else "不匹配")
    return 0 if ok else 1


def command_reset(args: argparse.Namespace) -> int:
    password = get_password(args)
    password_hash = hash_password(password, args.rounds)
    must_change = 1 if args.must_change else 0

    conn = connect_database()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE employees
                SET password_hash = %s,
                    must_change_password = %s,
                    updated_at = CURRENT_TIMESTAMP
                WHERE account = %s
                """,
                (password_hash, must_change, args.account),
            )
            if cur.rowcount == 0:
                conn.rollback()
                raise SystemExit(f"未找到账号：{args.account}")
        conn.commit()
    finally:
        conn.close()

    print(f"账号 {args.account} 密码已重置。must_change_password={must_change}")
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="内部后台管理系统密码运维工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例：
  python tools/password_tool.py hash --password 123456
  python tools/password_tool.py verify --password 123456 --hash "$2b$12$..."
  python tools/password_tool.py reset --account admin --password 123456
  python tools/password_tool.py reset --account zhangsan --password 123456 --must-change
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    hash_parser = subparsers.add_parser("hash", help="生成 bcrypt 密码哈希")
    hash_parser.add_argument("--password", help="明文密码。不传则交互式输入。")
    hash_parser.add_argument("--rounds", type=int, default=int(os.getenv("BCRYPT_ROUNDS", "12")), help="bcrypt rounds，默认读取 BCRYPT_ROUNDS 或 12。")
    hash_parser.set_defaults(func=command_hash)

    verify_parser = subparsers.add_parser("verify", help="校验明文密码和 bcrypt hash 是否匹配")
    verify_parser.add_argument("--password", help="明文密码。不传则交互式输入。")
    verify_parser.add_argument("--hash", dest="password_hash", required=True, help="数据库中的 password_hash。")
    verify_parser.set_defaults(func=command_verify)

    reset_parser = subparsers.add_parser("reset", help="重置数据库中某个账号的密码")
    reset_parser.add_argument("--account", required=True, help="员工登录账号。")
    reset_parser.add_argument("--password", help="新密码。不传则交互式输入。")
    reset_parser.add_argument("--must-change", action="store_true", help="重置后要求用户下次登录必须修改密码。")
    reset_parser.add_argument("--rounds", type=int, default=int(os.getenv("BCRYPT_ROUNDS", "12")), help="bcrypt rounds，默认读取 BCRYPT_ROUNDS 或 12。")
    reset_parser.set_defaults(func=command_reset)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
