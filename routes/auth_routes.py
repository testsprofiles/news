from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import create_token
import bcrypt

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/admin/login', methods=['POST'])
def admin_login():
   
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username va password kiritilishi shart!'}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
    user = cur.fetchone()
    cur.close()
    conn.close()

    if user and bcrypt.checkpw(password.encode('utf-8'), user['password'].encode('utf-8')):
        token = create_token(user['id'])
        return jsonify({
            'message': 'Muvaffaqiyatli login qilindi!',
            'token': token
        }), 200

    return jsonify({'message': 'Username yoki parol xato!'}), 401