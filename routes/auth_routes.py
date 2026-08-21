from flask import Blueprint, request, jsonify
from database import db_cursor
from utils.auth import create_token
import bcrypt

auth_bp = Blueprint('auth', __name__)
   
@auth_bp.route('/auth/login', methods=['POST'])
def auth_login():
   
    data = request.get_json() or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username va password kiritilishi shart!'}), 400

    try:
        with db_cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s;", (username,))
            user = cur.fetchone()
    except ConnectionError:
         return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500

    try:
        password_ok = user and bcrypt.checkpw(
            password.encode('utf-8'), user['password'].encode('utf-8') )
    except ValueError:
        password_ok = False

    if password_ok:
        oken = create_token(user['id'], role='admin')
        return jsonify({
            'message': 'Muvaffaqiyatli login qilindi!',
            'token': token
        }), 200

    return jsonify({'message': 'Username yoki parol xato!'}), 401
    

  