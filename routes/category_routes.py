from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import token_required

category_bp = Blueprint('category', __name__)



@category_bp.route('/api/categories', methods=['GET'])
def get_categories():
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
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

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO categories (name) VALUES (%s) RETURNING id, name;",
        (name,)
    )
    new_category = cur.fetchone()
    conn.commit()
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

    cur = conn.cursor()
    cur.execute(
        "UPDATE categories SET name = %s WHERE id = %s RETURNING id, name;",
        (name, cat_id)
    )
    updated = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not updated:
        return jsonify({'message': 'Kategoriya topilmadi!'}), 404

    return jsonify({'message': 'Kategoriya yangilandi!', 'category': updated}), 200


@category_bp.route('/api/categories/<int:cat_id>', methods=['DELETE'])
@token_required
def delete_category(current_user_id, cat_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute("DELETE FROM categories WHERE id = %s RETURNING id;", (cat_id,))
    deleted = cur.fetchone()
    conn.commit()
    cur.close()
    conn.close()

    if not deleted:
        return jsonify({'message': 'Kategoriya topilmadi!'}), 404

    return jsonify({'message': 'Kategoriya o`chirib tashlandi!'}), 200