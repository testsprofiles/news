from flask import Blueprint, request, jsonify, current_app
import os
import uuid
from database import get_db_connection
from utils.auth import token_required
from pydantic import ValidationError
from schemas.product import ProductCreate, ProductUpdate

products_bp = Blueprint('products', __name__)
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def _row_to_product(r):
    return {
        "id": r["id"],
        "name": r["name"],
        "description": r["description"],
        "price": r["price"],
        "image": r["image_url"],
        "category": {"id": r["category_id"], "name": r["category_name"]}
    }


@products_bp.route('/api/products', methods=['GET'])
def get_products():
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
    cur = conn.cursor()
    try:
        cur.execute(
            "SELECT p.id, p.name, p.description, p.price, p.image_url, "
            "p.category_id, c.name AS category_name FROM products p "
            "LEFT JOIN categories c ON p.category_id = c.id "
            "ORDER BY p.id;"
        )
        rows = cur.fetchall()
        return jsonify([_row_to_product(r) for r in rows]), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()


@products_bp.route('/api/products/<int:product_id>', methods=['GET'])
def get_single_product(product_id):
    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
    cur = conn.cursor()
    cur.execute(
        "SELECT p.id, p.name, p.description, p.price, p.image_url, "
        "p.category_id, c.name AS category_name FROM products p "
        "LEFT JOIN categories c ON p.category_id = c.id "
        "WHERE p.id = %s;", (product_id,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return jsonify({'message': 'Mahsulot topilmadi!'}), 404
    return jsonify(_row_to_product(row)), 200


@products_bp.route('/api/products', methods=['POST'])
@token_required
def create_product(current_user_id):
    try:
        data = ProductCreate(**(request.get_json() or {}))
    except ValidationError as e:
        return jsonify(e.errors()), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM categories WHERE id = %s;", (data.category_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'message': 'Bunday category_id mavjud emas!'}), 400

    try:
        cur.execute(
            "INSERT INTO products (name, description, price, category_id) "
            "VALUES (%s, %s, %s, %s) RETURNING id;",
            (data.name, data.description, data.price, data.category_id)
        )
        new_id = cur.fetchone()["id"]
        conn.commit()
        return jsonify({'message': 'Mahsulot qo`shildi!', 'id': new_id}), 201
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()

@products_bp.route('/api/products/<int:product_id>/image', methods=['POST'])
@token_required
def upload_product_image(current_user_id, product_id):
    if 'image' not in request.files:
        return jsonify({'message': 'Rasm fayli topilmadi!'}), 400

    file = request.files['image']
    if file.filename == '' or not allowed_file(file.filename):
        return jsonify({'message': 'Fayl noto`g`ri yoki tanlanmagan!'}), 400

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT id FROM products WHERE id = %s;", (product_id,))
    if not cur.fetchone():
        cur.close()
        conn.close()
        return jsonify({'message': 'Mahsulot topilmadi!'}), 404

    ext = file.filename.rsplit('.', 1)[1].lower()
    filename = f"{uuid.uuid4().hex}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    file.save(filepath)
    image_url = f"/uploads/{filename}"

    try:
        cur.execute("UPDATE products SET image_url = %s WHERE id = %s;", (image_url, product_id))
        conn.commit()
        return jsonify({'message': 'Rasm yuklandi!', 'image_url': image_url}), 200
    except Exception as e:
        conn.rollback()
        return jsonify({'message': f'Xatolik yuz berdi: {str(e)}'}), 500
    finally:
        cur.close()
        conn.close()