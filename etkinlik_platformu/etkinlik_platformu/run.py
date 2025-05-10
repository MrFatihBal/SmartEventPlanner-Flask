from flask import Flask, flash, render_template, redirect, url_for
from flask_cors import CORS
from flask_login import LoginManager, current_user, login_required
from flask_mail import Mail
import pyodbc
from app.models import User
from app import create_app

# create_app fonksiyonunu kullanarak app'i oluşturun
app = create_app()
CORS(app)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # SMTP sunucusu (örnek: Gmail)
app.config['MAIL_PORT'] = 587  # Port numarası
app.config['MAIL_USE_TLS'] = True  # TLS kullanma
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'your-email@gmail.com'  # Gönderici mail adresi
app.config['MAIL_PASSWORD'] = 'your-email-password'  # Mail şifresi
app.config['MAIL_DEFAULT_SENDER'] = 'your-email@gmail.com'  # Gönderen adres
mail = Mail(app)
# LoginManager'i app'e bağlayın
login_manager = LoginManager()
login_manager.login_view = 'main.login'
login_manager.init_app(app)

@login_manager.user_loader
def load_user(user_id):
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};SERVER=DESKTOP-8MG4EKJ\SQLEXPRESS;DATABASE=Etkinlik_Platformu;Trusted_Connection=yes;')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM [user] WHERE id = ?", (user_id,))
    user_data = cursor.fetchone()
    cursor.close()
    conn.close()
    if user_data:
        return User(id=user_data[0], username=user_data[1], email=user_data[2])
    return None
      

# Ana sayfa route'u
@app.route('/')
def index():
    return redirect(url_for('main.home'))


if __name__ == '__main__':
    app.run(debug=True)
