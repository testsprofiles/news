from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import token_required
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
    finally:
        cur.close()
        