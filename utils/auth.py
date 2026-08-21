import jwt
import os
import datetime
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY topilmadi!")

def create_token(user_id, role="admin"):
   
    payload = {
        'user_id': user_id,
    'role': role,
    'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=24)    }
    return jwt.encode(payload, SECRET_KEY, algorithm="HS256")


def token_required(f):

    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        if 'Authorization' in request.headers:
            auth_header = request.headers['Authorization']
            if auth_header.startswith("Bearer "):
                token = auth_header.split(" ")[1]

        if not token:
            return jsonify({'message': 'Token topilmadi! Tizimga kirish taqiqlanadi.'}), 401

        try:
            data = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])
            current_user_id = data['user_id']
            current_role = data.get('role')

        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token muddati tugagan! Qayta login qiling.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Yaroqsiz token!'}), 401

        if current_role != 'admin':
            return jsonify({'message': 'Ruxsat etilmagan amal! Faqat admin uchun.'}), 403

        return f(current_user_id, *args, **kwargs)

    return decorated