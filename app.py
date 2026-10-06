from flask import Flask, abort, send_from_directory
from flask_swagger_ui import get_swaggerui_blueprint
from routes.auth_routes import auth_bp
from routes.post_routes import posts_bp
from routes.category_routes import category_bp
from routes.comment_routes import comment_bp
from routes.page_routes import page_bp
from routes.product_routes import products_bp
import os
import uuid


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, 'frontend')
FRONTEND_JS_DIR = os.path.join(FRONTEND_DIR, 'js')

# Pages the Telegram Web App may open. An allow-list keeps the catch-all static
# route from ever being usable for path traversal.
FRONTEND_PAGES = ('index', 'login', 'post', 'admin', 'page')


app = Flask(__name__)

SWAGGER_URL = '/apidocs'
API_URL = '/static/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
    config={
        'app_name': "News Portal API",
        'persistAuthorization': True
    }
)
app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024  # 5MB limit

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




@app.route('/static/swagger.yaml')
def send_swagger():
    return send_from_directory('.', 'swagger.yaml')


app.register_blueprint(auth_bp)
app.register_blueprint(posts_bp)
app.register_blueprint(category_bp)
app.register_blueprint(comment_bp)
app.register_blueprint(page_bp)
app.register_blueprint(products_bp)             


@app.route('/health', methods=['GET'])
def health():
    """Machine-readable liveness probe used by the Docker/deploy health checks."""
    return {
        "message": "News CMS RESTful API muvaffaqiyatli ishlamoqda!",
        "status": "active"
    }, 200


@app.route('/', methods=['GET'])
def index():
    """Web App entry point opened by the Telegram bot's WebApp button.

    This used to answer with the API status JSON, which is why the Web App
    showed an empty screen instead of the portal.
    """
    return send_from_directory(FRONTEND_DIR, 'index.html')


@app.route('/<page>.html', methods=['GET'])
def frontend_page(page):
    """Serve the portal's static pages (login/post/admin/page)."""
    if page not in FRONTEND_PAGES:
        abort(404)
    return send_from_directory(FRONTEND_DIR, f'{page}.html')


@app.route('/js/<path:filename>', methods=['GET'])
def frontend_js(filename):
    """Serve the portal's JavaScript bundles referenced by the HTML pages."""
    return send_from_directory(FRONTEND_JS_DIR, filename)


if __name__ == '__main__':
    debug_mode = os.getenv("FLASK_DEBUG", "False") == "True"
    app.run(debug=debug_mode, host='0.0.0.0', port=int(os.getenv("PORT", 5000)))

