from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import token_required

posts_bp = Blueprint('posts', __name__)


@posts_bp.route('/api/posts', methods=['GET'])
def get_posts():
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.title, p.content, p.created_at, c.name as category_name 
        FROM posts p
        LEFT JOIN categories c ON p.category_id = c.id
        ORDER BY p.created_at DESC;
    """)
    posts = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(posts), 200


@posts_bp.route('/api/posts/<int:post_id>', methods=['GET'])
def get_single_post(post_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.title, p.content, p.created_at, c.name as category_name 
        FROM posts p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = %s;
    """, (post_id,))
    post = cur.fetchone()
    cur.close()
    conn.close()

    if not post:
        return jsonify({'message': 'Yangilik topilmadi!'}), 404

    return jsonify(post), 200



@posts_bp.route('/api/posts', methods=['POST'])
@token_required
def create_post(current_user_id):
    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')

    if not title or not content:
        return jsonify({'message': 'Title va content kiritilishi shart!'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO posts (title, content, category_id) VALUES (%s, %s, %s) RETURNING id, created_at;",
        (title, content, category_id)
    )
    new_post = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        'message': 'Yangilik muvaffaqiyatli qo`shildi!',
        'post': new_post
    }), 201


@posts_bp.route('/api/posts/<int:post_id>', methods=['PUT'])
@token_required
def update_post(current_user_id, post_id):
    data = request.get_json() or {}
    title = data.get('title')
    content = data.get('content')
    category_id = data.get('category_id')

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute(
        "UPDATE posts SET title = %s, content = %s, category_id = %s WHERE id = %s RETURNING id;",
        (title, content, category_id, post_id)
    )
    updated_post = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not updated_post:
        return jsonify({'message': 'Yangilik topilmadi!'}), 404

    return jsonify({'message': 'Yangilik muvaffaqiyatli yangilandi!'}), 200


@posts_bp.route('/api/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user_id, post_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute("DELETE FROM posts WHERE id = %s RETURNING id;", (post_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not deleted:
        return jsonify({'message': 'Yangilik topilmadi!'}), 404

    return jsonify({'message': 'Yangilik o`chirib tashlandi!'}), 200