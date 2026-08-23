from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import token_required
import psycopg2
import psycopg2.extras
import re


category_bp = Blueprint('category', __name__)

def make_slug(text):
    text = text.lower().strip()
    return re.sub(r'[\s_]+', '-', text)

@category_bp.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM categories ORDER BY id ASC;")
    categories = cur.fetchall()
    cur.close()
    conn.close()

    return jsonify(categories), 200


@category_bp.route('/api/categories', methods=['POST'])
@token_required
def create_category(current_user_id):
    data = request.get_json() or {}
    name = data.get('name')

    if not name:
        return jsonify({'message': 'Kategoriya nomi (name) kiritilishi shart!'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
        
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    new_slug = make_slug(name)
    cur.execute("SELECT id, name FROM categories;")
    all_categories = cur.fetchall()
    
    for cat in all_categories:
        if make_slug(cat['name']) == new_slug:
            cur.close()
            conn.close()
            return jsonify({'message': 'Bu nomdagi (yoki o`xshash slugli) kategoriya allaqachon mavjud!'}), 400
    try:
        cur.execute(
            "INSERT INTO categories (name) VALUES (%s) RETURNING id, name;",
            (name,)
        )
        new_category = cur.fetchone()
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': 'Bu kategoriya nomi allaqachon mavjud!'}), 400
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500

    cur.close()
    conn.close()

    return jsonify({
        'message': 'Kategoriya qo`shildi!',
        'category': new_category
    }), 201


@category_bp.route('/api/categories/<int:cat_id>', methods=['PUT'])
@token_required
def update_category(current_user_id, cat_id):
    data = request.get_json() or {}
    name = data.get('name')

    if not name:
        return jsonify({'message': 'Kategoriya nomi kiritilishi shart!'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    new_slug = make_slug(name)
    cur.execute("SELECT id, name FROM categories WHERE id != %s;", (cat_id,))
    other_categories = cur.fetchall()
    
    for cat in other_categories:
        if make_slug(cat['name']) == new_slug:
            cur.close()
            conn.close()
            return jsonify({'message': 'Bu nomdagi (yoki o`xshash slugli) kategoriya allaqachon mavjud!'}), 400
    try:
        cur.execute(
            "UPDATE categories SET name = %s WHERE id = %s RETURNING id, name;",
            (name, cat_id)
        )
        updated = cur.fetchone()
        
        if not updated:
            conn.rollback()
            cur.close()
            conn.close()
            return jsonify({'message': 'Kategoriya topilmadi!'}), 404
            
        conn.commit()
    except psycopg2.errors.UniqueViolation:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': 'Bu nomdagi kategoriya allaqachon mavjud!'}), 400
    except Exception as e:
        conn.rollback()
        cur.close()
        conn.close()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500

    cur.close()
    conn.close()

    return jsonify({'message': 'Kategoriya yangilandi!', 'category': updated}), 200

@category_bp.route('/api/categories/<int:cat_id>', methods=['DELETE'])
@token_required
def delete_category(current_user_id, cat_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("DELETE FROM categories WHERE id = %s RETURNING id;", (cat_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not deleted:
        return jsonify({'message': 'Kategoriya topilmadi!'}), 404

    return jsonify({'message': 'Kategoriya o`chirib tashlandi!'}), 200
    