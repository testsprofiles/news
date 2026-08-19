import jwt
import os
import datetime
from functools import wraps
from flask import request, jsonify
from dotenv import load_dotenv

load_dotenv()
SECRET_KEY = os.getenv("SECRET_KEY", "super_maxfiy_kalit_123")

def create_token(user_id):
   
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
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
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token muddati tugagan! Qayta login qiling.'}), 401
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Yaroqsiz token!'}), 401

        return f(current_user_id, *args, **kwargs)

    return decorated