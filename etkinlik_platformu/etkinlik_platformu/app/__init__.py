from flask import Flask
from flask_login import LoginManager
from .models import User

login_manager = LoginManager()

# Kullanıcıyı yüklemek için gerekli fonksiyonu ekleyelim
@login_manager.user_loader
def load_user(user_id):
    return User.get_by_id(user_id)

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'buraya-gizli-anahtarinizi-yazin'
    
    login_manager.init_app(app)
    login_manager.login_view = 'main.login'
    login_manager.login_message = 'Bu sayfayı görüntülemek için giriş yapmalısınız.'
    login_manager.login_message_category = 'info'

    from .routes import main
    app.register_blueprint(main, url_prefix='/')
    
    return app
