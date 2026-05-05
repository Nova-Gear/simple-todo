"""
Todo Service
Business logic layer for todo CRUD operations.
Keeps route handlers thin by centralizing all DB interactions here.
"""

from app.database import get_cursor


def get_all_todos(filter_status=None):
    """
    Retrieve all todos, optionally filtered by completion status.

    Args:
        filter_status: None for all, 'completed', or 'active'

    Returns:
        List of todo dictionaries.
    """
    base_query = "SELECT * FROM todos"
    params = []

    if filter_status == "completed":
        base_query += " WHERE is_completed = 1"
    elif filter_status == "active":
        base_query += " WHERE is_completed = 0"

    base_query += " ORDER BY created_at DESC"

    with get_cursor() as cursor:
        cursor.execute(base_query, params)
        todos = cursor.fetchall()

    return _serialize_todos(todos)


def get_todo_by_id(todo_id):
    """
    Retrieve a single todo by its ID.

    Returns:
        Todo dict or None if not found.
    """
    with get_cursor() as cursor:
        cursor.execute("SELECT * FROM todos WHERE id = %s", (todo_id,))
        todo = cursor.fetchone()

    if not todo:
        return None

    return _serialize_todo(todo)


def create_todo(title, description=None, priority="medium"):
    """
    Create a new todo item.

    Returns:
        The newly created todo dict.
    """
    with get_cursor() as cursor:
        cursor.execute(
            "INSERT INTO todos (title, description, priority) VALUES (%s, %s, %s)",
            (title, description, priority),
        )
        new_id = cursor.lastrowid

    return get_todo_by_id(new_id)


def update_todo(todo_id, **fields):
    """
    Update a todo's fields dynamically.
    Only provided fields are updated — unprovided fields remain unchanged.

    Returns:
        Updated todo dict or None if not found.
    """
    if not fields:
        return get_todo_by_id(todo_id)

    allowed_fields = {"title", "description", "is_completed", "priority"}
    filtered = {key: value for key, value in fields.items() if key in allowed_fields}

    if not filtered:
        return get_todo_by_id(todo_id)

    set_clause = ", ".join(f"{key} = %s" for key in filtered)
    values = list(filtered.values()) + [todo_id]

    with get_cursor() as cursor:
        cursor.execute(
            f"UPDATE todos SET {set_clause} WHERE id = %s",
            values,
        )

    return get_todo_by_id(todo_id)


def toggle_todo(todo_id):
    """
    Toggle the completion status of a todo.

    Returns:
        Updated todo dict or None if not found.
    """
    with get_cursor() as cursor:
        cursor.execute(
            "UPDATE todos SET is_completed = NOT is_completed WHERE id = %s",
            (todo_id,),
        )
        affected = cursor.rowcount

    if affected == 0:
        return None

    return get_todo_by_id(todo_id)


def delete_todo(todo_id):
    """
    Permanently delete a todo.

    Returns:
        True if deleted, False if not found.
    """
    with get_cursor() as cursor:
        cursor.execute("DELETE FROM todos WHERE id = %s", (todo_id,))
        return cursor.rowcount > 0


def get_stats():
    """
    Return aggregate statistics about todos.

    Returns:
        Dict with total, completed, and active counts.
    """
    with get_cursor() as cursor:
        cursor.execute(
            """
            SELECT
                COUNT(*) as total,
                SUM(is_completed = 1) as completed,
                SUM(is_completed = 0) as active
            FROM todos
            """
        )
        row = cursor.fetchone()

    return {
        "total": row["total"] or 0,
        "completed": int(row["completed"] or 0),
        "active": int(row["active"] or 0),
    }


def _serialize_todo(todo):
    """Convert a raw DB row into a clean API-friendly dict."""
    return {
        "id": todo["id"],
        "title": todo["title"],
        "description": todo["description"],
        "isCompleted": bool(todo["is_completed"]),
        "priority": todo["priority"],
        "createdAt": todo["created_at"].isoformat() if todo["created_at"] else None,
        "updatedAt": todo["updated_at"].isoformat() if todo["updated_at"] else None,
    }


def _serialize_todos(todos):
    """Serialize a list of todo rows."""
    return [_serialize_todo(todo) for todo in todos]
