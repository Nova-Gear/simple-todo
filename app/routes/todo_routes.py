"""
Todo API Routes
RESTful endpoints for todo CRUD operations.
All business logic is delegated to the service layer.
"""

from flask import Blueprint, request, jsonify
from app.services import todo_service

todo_bp = Blueprint("todos", __name__, url_prefix="/api/todos")


@todo_bp.route("", methods=["GET"])
def list_todos():
    """GET /api/todos?status=all|active|completed"""
    filter_status = request.args.get("status", None)
    todos = todo_service.get_all_todos(filter_status)
    return jsonify({"success": True, "data": todos})


@todo_bp.route("", methods=["POST"])
def create_todo():
    """POST /api/todos — Create a new todo."""
    body = request.get_json(silent=True)

    if not body or not body.get("title", "").strip():
        return jsonify({"success": False, "error": "Title is required"}), 400

    title = body["title"].strip()
    description = body.get("description", "").strip() or None
    priority = body.get("priority", "medium")

    if priority not in ("low", "medium", "high"):
        return jsonify({"success": False, "error": "Priority must be low, medium, or high"}), 400

    todo = todo_service.create_todo(title, description, priority)
    return jsonify({"success": True, "data": todo}), 201


@todo_bp.route("/<int:todo_id>", methods=["GET"])
def get_todo(todo_id):
    """GET /api/todos/:id — Get a single todo."""
    todo = todo_service.get_todo_by_id(todo_id)

    if not todo:
        return jsonify({"success": False, "error": "Todo not found"}), 404

    return jsonify({"success": True, "data": todo})


@todo_bp.route("/<int:todo_id>", methods=["PUT"])
def update_todo(todo_id):
    """PUT /api/todos/:id — Update a todo's fields."""
    existing = todo_service.get_todo_by_id(todo_id)
    if not existing:
        return jsonify({"success": False, "error": "Todo not found"}), 404

    body = request.get_json(silent=True) or {}

    update_fields = {}

    if "title" in body:
        title = body["title"].strip()
        if not title:
            return jsonify({"success": False, "error": "Title cannot be empty"}), 400
        update_fields["title"] = title

    if "description" in body:
        update_fields["description"] = body["description"].strip() or None

    if "isCompleted" in body:
        update_fields["is_completed"] = 1 if body["isCompleted"] else 0

    if "priority" in body:
        if body["priority"] not in ("low", "medium", "high"):
            return jsonify({"success": False, "error": "Priority must be low, medium, or high"}), 400
        update_fields["priority"] = body["priority"]

    todo = todo_service.update_todo(todo_id, **update_fields)
    return jsonify({"success": True, "data": todo})


@todo_bp.route("/<int:todo_id>/toggle", methods=["PATCH"])
def toggle_todo(todo_id):
    """PATCH /api/todos/:id/toggle — Toggle completion status."""
    todo = todo_service.toggle_todo(todo_id)

    if not todo:
        return jsonify({"success": False, "error": "Todo not found"}), 404

    return jsonify({"success": True, "data": todo})


@todo_bp.route("/<int:todo_id>", methods=["DELETE"])
def delete_todo(todo_id):
    """DELETE /api/todos/:id — Delete a todo."""
    deleted = todo_service.delete_todo(todo_id)

    if not deleted:
        return jsonify({"success": False, "error": "Todo not found"}), 404

    return jsonify({"success": True, "message": "Todo deleted successfully"})


@todo_bp.route("/stats", methods=["GET"])
def get_stats():
    """GET /api/todos/stats — Get aggregate statistics."""
    stats = todo_service.get_stats()
    return jsonify({"success": True, "data": stats})
