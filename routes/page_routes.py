from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import token_required
from pydantic import ValidationError
from schemas.page import PageCreate, PageUpdate
import psycopg2                                        


page_bp = Blueprint('page_bp', __name__)

@page_bp.route('/api/pages', methods=['GET'])
def get_pages():
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
    cur = conn.cursor()
    try:
        cur.execute("SELECT id, title, content, slug FROM pages;")
        pages = cur.fetchall()
        return jsonify(pages), 200

    finally:
        cur.close()
        conn.close()
@page_bp.route('/api/pages', methods=['POST'])
@token_required
def create_page(current_user_id):
    try:
        data = PageCreate(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
    cur = conn.cursor()
    try:
        cur.execute(
            "INSERT INTO pages (title, content, slug) VALUES (%s, %s, %s) RETURNING id;",
            (data.title, data.content, data.slug)
        )
        new_page = cur.fetchone()
        conn.commit()
        return jsonify({'message': 'Sahifa muvaffaqiyatli qo`shildi!', 'page': new_page}), 201
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({'message': 'Bunday slug allaqachon mavjud!'}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()


@page_bp.route('/api/pages/<int:page_id>', methods=['PUT'])
@token_required
def update_page(current_user_id, page_id):
    try:
        data = PageUpdate(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    title = data.title
    content = data.content
    slug = data.slug

    if title is None and content is None and slug is None:
        return jsonify({'message': 'Kamida bitta maydon yuborilishi kerak!'}), 400

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
        if slug is not None:
            fields.append("slug = %s")
            values.append(slug)

        values.append(page_id)
        query = f"UPDATE pages SET {', '.join(fields)} WHERE id = %s RETURNING id;"
        cur.execute(query, values)
        updated_page = cur.fetchone()
        conn.commit()

        if not updated_page:
            return jsonify({'message': 'Sahifa topilmadi!'}), 404

        return jsonify({'message': 'Sahifa muvaffaqiyatli yangilandi!'}), 200
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        return jsonify({'message': 'Bunday slug allaqachon mavjud!'}), 400
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()