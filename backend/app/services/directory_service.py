from ..db import db_cursor


def list_people_and_groups():
    with db_cursor() as cursor:
        cursor.execute(
            """
            SELECT employee_name
            FROM employees
            WHERE status = 1
            ORDER BY id ASC
            """
        )
        people = [row["employee_name"] for row in cursor.fetchall()]

        cursor.execute(
            """
            SELECT g.group_name, e.employee_name
            FROM employee_groups g
            JOIN group_members gm ON gm.group_id = g.id AND gm.status = 1
            JOIN employees e ON e.id = gm.employee_id AND e.status = 1
            WHERE g.status = 1
            ORDER BY g.id ASC, gm.id ASC
            """
        )
        groups = {}
        for row in cursor.fetchall():
            groups.setdefault(row["group_name"], []).append(row["employee_name"])

    return {"people": people, "groups": groups}
