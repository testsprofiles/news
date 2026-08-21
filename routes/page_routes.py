from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import token_required

page_bp = Blueprint('page_bp', __name__)

@page_bp.route('/pages', methods=['GET'])
def get_pages():
    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, slug FROM pages;")
    pages = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for page in pages:
        result.append({
            "id": page[0],
            "title": page[1],
            "content": page[2],
            "slug": page[3]
        })
#----------------------------------------------------------------------qwertyuioitqwertyuiuytrewqwert
    return jsonify(result), 200

@page_bp.route('/pages', methods=['POST'])
@token_required
def create_page(current_user):
    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')
    slug = data.get('slug')

    if not title or not content or not slug:
        return jsonify({"message": "title, content va slug kiritilishi shart!"}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pages (title, content, slug) VALUES (%s, %s, %s) RETURNING id;",
        (title, content, slug)
    )
    new_id = cur.fetchone()[0]
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({"message": "Sahifa yaratildi", "id": new_id}), 201