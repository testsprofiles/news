from flask import Blueprint, request, jsonify
from database import get_db_connection
from utils.auth import token_required

comment_bp = Blueprint('comment_bp', __name__)

@comment_bp.route('/api/comments', methods=['GET'])
def get_comments():
    conn = get_db_connection()
    if not conn:                                              
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500  
    cur = conn.cursor()
    cur.execute("SELECT id, post_id, text FROM comments;")
    comments = cur.fetchall()
    cur.close()
    conn.close()

    result = []
    for comment in comments:
        result.append({
            "id": comment['id'],
            "post_id": comment['post_id'],
            "text": comment['text']
        })

    return jsonify(result), 200


@comment_bp.route('/api/comments', methods=['POST'])
@token_required
def create_comment(current_user): 
    data = request.get_json() or {}
    post_id = data.get('post_id')
    text = data.get('text')


    if not post_id or not text:
        return jsonify({"error": "post_id va text kiritilishi shart!"}), 400

    if not isinstance(post_id, int):
        return jsonify({"error": "post_id int bolishi kerak !"}), 400

    text = str(text).strip()
    if len(text) == 0:
        return jsonify({"error": "Izoh matni bosh bolishi mumkin emas!"}), 400

    if len(text) < 5:
        return jsonify({"error": " kamida 5 ta belgi bolishi kerak!"}), 400

    if len(text) > 1000:
        return jsonify({"error": " Maksimal 1000 ta belgi ruxsat etilgan."}), 400

    conn = get_db_connection()
    if not conn:
        return jsonify({'message': 'Baza bilan ulanishda xatolik!'}), 500
    cur = conn.cursor()


    cur.execute("SELECT id FROM posts WHERE id = %s;", (post_id,))
    post = cur.fetchone()
    if not post:
        cur.close()
        conn.close()
        return jsonify({"error": f"{post_id} -id li  post topilmadi!"}), 404


    cur.execute(
        "insert into comments (post_id, text) values (%s, %s) returning id;",
        (post_id, text)
    )
    new_id = cur.fetchone()['id']
    conn.commit()
    cur.close()
    conn.close()

    return jsonify({
        "message": "Izoh  saqlandi ", 
        "id": new_id
        
    }), 201 