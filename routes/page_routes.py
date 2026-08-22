from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import token_required
import psycopg2                                              


page_bp = Blueprint('page_bp', __name__)

@page_bp.route('/api/pages', methods=['GET'])
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
            "id": page['id'],
            "title": page['title'],
            "content": page['content'],
            "slug": page['slug']
        })
    return jsonify(result), 200

@page_bp.route('/api/pages', methods=['POST'])
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
    try:
        cur.execute(
            "INSERT INTO pages (title, content, slug) VALUES (%s, %s, %s) RETURNING id;",
            (title, content, slug)
        )
        new_id = cur.fetchone()['id']    
        conn.commit()     
    except psycopg2.errors.UniqueViolation:                        
        conn.rollback()                                            
        cur.close()                                                
        conn.close()                                               
        return jsonify({"message": f"'{slug}' slug bilan sahifa allaqachon mavjud!"}), 400  # <<< YANGI QATOR

    cur.close()
    conn.close()

    return jsonify({"message": "Sahifa yaratildi", "id": new_id}), 201