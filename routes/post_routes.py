from flask import Blueprint, request, jsonify
import os
import uuid
from flask import current_app
from database import get_db_connection
from utils.auth import token_required
import re
from pydantic import ValidationError
from schemas.post import PostCreate, PostUpdate

posts_bp = Blueprint('posts', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@posts_bp.route('/api/posts', methods=['GET'])
def get_posts():
    title_filter = request.args.get('title')
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    offset = (page - 1) * limit

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    try:
        if title_filter:
            if any(ch.isdigit() for ch in title_filter):
                return jsonify({"error": "title parametrida raqam bo'lishi mumkin emas"}), 400
            if len(title_filter) > 3:
                return jsonify({"error": "title parametri 3 ta harfdan oshmasligi kerak"}), 400
            cur.execute(
                "SELECT p.id, p.title, p.content, p.category_id, c.name AS category_name, "
                "p.image_url, p.created_at FROM posts p "
                "LEFT JOIN categories c ON p.category_id = c.id "
                "WHERE p.title ~* %s ORDER BY p.created_at DESC LIMIT %s OFFSET %s;",
                (title_filter, limit, offset)
            )
        else:
            cur.execute(
                "SELECT p.id, p.title, p.content, p.category_id, c.name AS category_name, "
                "p.image_url, p.created_at FROM posts p "
                "LEFT JOIN categories c ON p.category_id = c.id "
                "ORDER BY p.created_at DESC LIMIT %s OFFSET %s;",
                (limit, offset)
            )
        posts = cur.fetchall()
        return jsonify(posts), 200

    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500

    finally:
        cur.close()
        conn.close()


@posts_bp.route('/api/posts/<int:post_id>', methods=['GET'])
def get_single_post(post_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute("""
        SELECT p.id, p.title, p.content, p.image_url, p.created_at, c.name as category_name
        FROM posts p
        LEFT JOIN categories c ON p.category_id = c.id
        WHERE p.id = %s;
    """, (post_id,))
    post = cur.fetchone()

    if not post:
        cur.close()
        conn.close()
        return jsonify({'message': 'Yangilik topilmadi!'}), 404

    cur.execute("SELECT id, post_id, text FROM comments WHERE post_id = %s;", (post_id,))
    comments = cur.fetchall()
    cur.close()
    conn.close()

    post_data = dict(post)
    post_data['comments'] = comments
    post_data['comment_count'] = len(comments)

    return jsonify(post_data), 200


@posts_bp.route('/api/posts', methods=['POST'])
@token_required
def create_post(current_user_id):
    try:
        data = PostCreate(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    title = data.title
    content = data.content
    category_id = data.category_id

    if category_id is not None and not isinstance(category_id, int):
        return jsonify({'message': 'category_id butun son bolishi kerak!'}), 400

    if category_id is not None:
        conn_check = get_db_connection()
        if not conn_check:
            return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
        cur_check = conn_check.cursor()
        cur_check.execute("SELECT id FROM categories WHERE id = %s;", (category_id,))
        exists = cur_check.fetchone()
        cur_check.close()
        conn_check.close()
        if not exists:
            return jsonify({'message': 'Bunday category_id mavjud emas!'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO posts (title, content, category_id) VALUES (%s, %s, %s) RETURNING id, created_at;",
            (title, content, category_id)
        )
        new_post = cur.fetchone()
        conn.commit()
        return jsonify({
            'message': 'Yangilik muvaffaqiyatli qo`shildi!',
            'post': new_post
        }), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()


@posts_bp.route('/api/posts/<int:post_id>', methods=['PUT'])
@token_required
def update_post(current_user_id, post_id):
    try:
        data = PostUpdate(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    title = data.title
    content = data.content
    category_id = data.category_id

    if title is None and content is None and category_id is None:
        return jsonify({'message': 'Kamida bitta maydon yuborilishi kerak!'}), 400

    if category_id is not None:
        conn_check = get_db_connection()
        if not conn_check:
            return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
        cur_check = conn_check.cursor()
        cur_check.execute("SELECT id FROM categories WHERE id = %s;", (category_id,))
        exists = cur_check.fetchone()
        cur_check.close()
        conn_check.close()
        if not exists:
            return jsonify({'message': 'Bunday category_id mavjud emas!'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
    cur = conn.cursor()

    try:
        fields = []
        values = []
        if title is not None:
            fields.append("title = %s")
            values.append(title)
        if content is not None:
            fields.append("content = %s")
            values.append(content)
        if category_id is not None:
            fields.append("category_id = %s")
            values.append(category_id)

        values.append(post_id)
        query = f"UPDATE posts SET {', '.join(fields)} WHERE id = %s RETURNING id;"
        cur.execute(query, values)
        updated_post = cur.fetchone()
        conn.commit()

        if not updated_post:
            return jsonify({'message': 'Yangilik topilmadi!'}), 404

        return jsonify({'message': 'Yangilik muvaffaqiyatli yangilandi!'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()


@posts_bp.route('/api/posts/<int:post_id>', methods=['DELETE'])
@token_required
def delete_post(current_user_id, post_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM posts WHERE id = %s RETURNING id;", (post_id,))
        deleted = cur.fetchone()
        conn.commit()

        if not deleted:
            return jsonify({'message': 'Yangilik topilmadi!'}), 404

        return jsonify({'message': 'Yangilik o`chirib tashlandi!'}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()


@posts_bp.route('/api/posts/<int:post_id>/image', methods=['POST'])
@token_required
def upload_post_image(current_user_id, post_id):
    if 'image' not in request.files:
        return jsonify({'message': 'Rasm fayli topilmadi!'}), 400

    file = request.files['image']
    if file.filename == '':
        return jsonify({'message': 'Fayl tanlanmagan!'}), 400

    if not allowed_file(file.filename):
        return jsonify({'message': 'Faqat rasm fayllari ruxsat etilgan (png, jpg, jpeg, gif, webp)!'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute("SELECT image_url FROM posts WHERE id = %s;", (post_id,))
    existing = cur.fetchone()
    if not existing:
        cur.close()
        conn.close()
        return jsonify({'message': 'Yangilik topilmadi!'}), 404

    old_image_url = existing['image_url']
    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    image_url = f"/uploads/{filename}"

    try:
        cur.execute(
            "UPDATE posts SET image_url = %s WHERE id = %s RETURNING id;",
            (image_url, post_id)
        )
        updated = cur.fetchone()
        conn.commit()

        if not updated:
            return jsonify({'message': 'Yangilik topilmadi!'}), 404

        if old_image_url:
            old_filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], os.path.basename(old_image_url))
            if os.path.exists(old_filepath):
                os.remove(old_filepath)

        return jsonify({'message': 'Rasm muvaffaqiyatli yuklandi!', 'image_url': image_url}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()