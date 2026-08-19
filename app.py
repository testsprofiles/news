from flask import Flask
from routes.auth_routes import auth_bp
from routes.post_routes import posts_bp
from routes.category_routes import category_bp
from routes.comment_routes import comment_bp
from routes.page_routes import page_bp

app = Flask(__name__)

app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(category_bp)
app.register_blueprint(comment_bp)
app.register_blueprint(page_bp)

@app.route('/', methods=['GET'])
def index():
    return {
        "message": "News CMS RESTful API muvaffaqiyatli ishlamoqda!",
        "status": "active"
    }, 200


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)