from flask import Flask, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from routes.auth_routes import auth_bp
from routes.post_routes import posts_bp
from routes.category_routes import category_bp
from routes.comment_routes import comment_bp
from routes.page_routes import page_bp
import os
import uuid

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

SWAGGER_URL = '/apidocs'
API_URL = '/static/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={'app_name': "News Portal API"}
)

app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)


@app.route('/static/swagger.yaml')
def send_swagger():
    return send_from_directory('.', 'swagger.yaml')


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
    debug_mode = os.getenv("FLASK_DEBUG", "False") == "True"
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))