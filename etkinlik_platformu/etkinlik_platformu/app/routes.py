from flask import Blueprint, current_app, jsonify, render_template, request, redirect, session, url_for, flash
from flask_login import login_user, login_required, logout_user, current_user
import requests
from werkzeug.security import generate_password_hash, check_password_hash
from api import get_route
from app.models import User, Event
import pyodbc
import os
from werkzeug.utils import secure_filename
from config import ELASTIC_EMAIL_API_KEY, MAPBOX_ACCESS_TOKEN
from flask_mail import Mail, Message 
import secrets
import datetime
from datetime import datetime, timedelta, timezone
import jwt
import re

from .notification import NotificationSystem

main = Blueprint('main', __name__)
mail = Mail()

UPLOAD_FOLDER = 'static/profile_photos'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Güvenlik için email doğrulama fonksiyonu
def validate_email(email):
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=DESKTOP-8MG4EKJ\SQLEXPRESS;'
        'DATABASE=Etkinlik_Platformu;'
        'Trusted_Connection=yes;'
    )

def send_password_reset_email(email, reset_link):
    try:
        # Elastic Email API endpoint ve parametreleri
        api_url = "https://api.elasticemail.com/v2/email/send"
        
        payload = {
            "apikey": ELASTIC_EMAIL_API_KEY,
            "from": "destek@sizin-domain.com",  # Onaylanmış email
            "fromName": "Etkinlik Platformu",
            "to": email,
            "subject": "Şifre Sıfırlama Talebi",
            "bodyHtml": f'''
            <strong>Şifre Sıfırlama Talebi</strong><br>
            Şifrenizi sıfırlamak için aşağıdaki linke tıklayın:<br>
            <a href="{reset_link}">Şifremi Sıfırla</a><br>
            Bu link 1 saat süreyle geçerli olacaktır.
            ''',
            "isTransactional": True
        }
        
        # API çağrısı
        response = requests.post(api_url, data=payload)
        
        # Detaylı hata ayıklama
        print("API Response Status Code:", response.status_code)
        print("API Response Content:", response.text)
        
        # Yanıtı kontrol et
        result = response.json()
        
        if result.get('success', False):
            print("Email başarıyla gönderildi")
            return True
        else:
            print(f"Email gönderme hatası: {result}")
            return False
    
    except requests.exceptions.RequestException as req_err:
        print(f"Ağ hatası: {req_err}")
        return False
    except ValueError as json_err:
        print(f"JSON çözümleme hatası: {json_err}")
        return False
    except Exception as e:
        print(f"Bilinmeyen hata: {e}")
        return False


@main.route('/home')
def home():
    return render_template('home.html')

@main.route('/login', methods=['GET', 'POST'])
def login():
    #if current_user.is_authenticated:
     #   return redirect(url_for('main.firstpage'))

    if request.method == 'POST':  # POST isteği ile giriş işlemi
        username = request.form.get('username')  # Email yerine kullanıcı adı
        password = request.form.get('password')
        remember = True if request.form.get('remember') else False

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute(""" 
                SELECT id, username, password, email, is_active 
                FROM [user] WHERE username = ? 
            """, (username,))
            user_data = cursor.fetchone()

            if user_data and check_password_hash(user_data[2], password):  # Şifre kontrolü
                if not user_data[4]:  # is_active kontrolü
                    flash('Hesabınız aktif değil. Lütfen email adresinizi doğrulayın.')
                    return redirect(url_for('main.login'))

                user = User(
                    id=user_data[0],
                    username=user_data[1],
                    email=user_data[3],
                    is_active=user_data[4]
                )
                login_user(user, remember=remember)

                next_page = request.args.get('next')  # Eğer kullanıcı önceden gittiği sayfayı istiyorsa
                return redirect(next_page or url_for('main.firstpage'))
            else:
                flash('Kullanıcı adı veya şifre hatalı.')

        except Exception as e:
            flash('Giriş yapılırken bir hata oluştu.')
        finally:
            cursor.close()
            conn.close()

    return render_template('login.html')
  

from werkzeug.security import generate_password_hash
from flask import request, redirect, url_for, flash
import os

UPLOAD_FOLDER = 'path/to/upload'  # Fotoğraf için dizin
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

@main.route('/register', methods=['GET', 'POST'])
def register():
    interests = [
        "Spor", "Müzik", "Sinema", "Kitap", "Seyahat", "Yemek", "Teknoloji",
        "Sanat", "Fotoğrafçılık", "Dans", "Tiyatro", "Doğa", "Bilim",
        "Tarih", "Moda", "Oyun", "Fitness", "Yoga", "Meditasyon", "Bahçecilik"
    ]

    if request.method == 'POST':
        form_data = {
            'email': request.form.get('email'),
            'first_name': request.form.get('firstname'),
            'last_name': request.form.get('lastname'),
            'username': request.form.get('username'),
            'password': request.form.get('password'),
            'birth_date': request.form.get('birthdate'),
            'gender': request.form.get('gender'),
            'phone': request.form.get('phone'),
            'selected_interests': request.form.getlist('interests')
        }

        # Gerekli alanlar kontrolü
        required_fields = ['email', 'username', 'password']
        for field in required_fields:
            if not form_data[field]:
                flash(f'{field.capitalize()} alanı zorunludur.')
                return redirect(url_for('main.register'))

        # Fotoğraf yüklemesi
        photo_filename = None
        if 'photo' in request.files:
            photo = request.files['photo']
            if photo and allowed_file(photo.filename):
                filename = secure_filename(photo.filename)
                photo_filename = f"{form_data['username']}_{filename}"
                os.makedirs(UPLOAD_FOLDER, exist_ok=True)
                photo.save(os.path.join(UPLOAD_FOLDER, photo_filename))

        # Veritabanı bağlantısı
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Email ve kullanıcı adı kontrolü
            cursor.execute("SELECT * FROM [user] WHERE email = ?", (form_data['email'],))
            if cursor.fetchone():
                flash('Email adresi zaten kayıtlı')
                return redirect(url_for('main.register'))

            cursor.execute("SELECT * FROM [user] WHERE username = ?", (form_data['username'],))
            if cursor.fetchone():
                flash('Kullanıcı adı zaten kullanımda')
                return redirect(url_for('main.register'))

            # Parola şifreleme
            hashed_password = generate_password_hash(form_data['password'], method='pbkdf2:sha256')

            # Kullanıcı kaydı
            cursor.execute("""
                INSERT INTO [user] (username, email, password, first_name, last_name,
                birth_date, gender, phone, profile_photo)
                OUTPUT INSERTED.id
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                form_data['username'], form_data['email'], hashed_password,
                form_data['first_name'], form_data['last_name'], form_data['birth_date'],
                form_data['gender'], form_data['phone'], photo_filename
            ))

            # Eklenen kullanıcının ID'sini al
            user_id = cursor.fetchone()[0]

            # İlgi alanlarını kaydet
            for interest in form_data['selected_interests']:
                cursor.execute("""
                    INSERT INTO user_interests (user_id, interest)
                    VALUES (?, ?)
                """, (user_id, interest))

            # Kullanıcıya 20 puan ekliyoruz
            cursor.execute("""
                INSERT INTO user_points (user_id, points, reason, earned_at)
                VALUES (?, ?, ?, ?)
            """, (user_id, 20, 'Yeni Kayıt', datetime.now()))

            conn.commit()
            flash('Kayıt başarılı! Şimdi giriş yapabilirsiniz.')
            return redirect(url_for('main.login'))

        except Exception as e:
            conn.rollback()
            flash(f'Kayıt işlemi sırasında bir hata oluştu: {str(e)}')
            return redirect(url_for('main.register'))

        finally:
            cursor.close()
            conn.close()

    return render_template('register.html', interests=interests)



@main.route('/firstpage')
@login_required
def firstpage():
    # Etkinlik verilerini veritabanından çekiyoruz
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, description, location.STAsText() AS location FROM [Event]")
    events = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return render_template('firstpage.html', events=events)




@main.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.login'))

@main.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email')

        # Email formatını kontrol et
        if not validate_email(email):
            flash('Geçersiz email formatı.')
            return redirect(url_for('main.forgot_password'))

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            cursor.execute("""SELECT id, email FROM [user] WHERE email = ?""", (email,))
            user = cursor.fetchone()

            if user:
                # Token oluştur
                token = secrets.token_urlsafe(32)
                reset_link = url_for('main.reset_password', token=token, _external=True)

                # Token'ı veritabanına kaydet
                cursor.execute("""
                    INSERT INTO password_reset_tokens 
                    (user_id, token, expiration, used) 
                    VALUES (?, ?, DATEADD(hour, 1, GETDATE()), 0)
                """, (user[0], token))
                conn.commit()

                # SendGrid ile email gönder
                if send_password_reset_email(user[1], reset_link):
                    flash('Şifre sıfırlama linki e-posta adresinize gönderildi.')
                else:
                    flash('Email gönderme hatası. Daha sonra tekrar deneyin.')
                
                return redirect(url_for('main.login'))
            else:
                flash('Bu e-posta adresi ile bir hesap bulunamadı.')

        except Exception as e:
            print(f"Hata: {e}")
            flash('Bir hata oluştu. Daha sonra tekrar deneyin.')
        finally:
            cursor.close()
            conn.close()

    return render_template('forgot_password.html')

@main.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = request.form.get('password')
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Token'ı veritabanında kontrol et
            cursor.execute("""
                SELECT user_id FROM password_reset_tokens 
                WHERE token = ? AND expiration > GETDATE() AND used = 0
            """, (token,))
            token_data = cursor.fetchone()

            if token_data:
                # Şifreyi hashle ve güncelle
                hashed_password = generate_password_hash(new_password, method='pbkdf2:sha256')
                cursor.execute("""UPDATE [user] SET password = ? WHERE id = ?""", (hashed_password, token_data[0]))
                
                # Token'ı kullanılmış olarak işaretle
                cursor.execute("""UPDATE password_reset_tokens SET used = 1 WHERE token = ?""", (token,))
                conn.commit()

                flash('Şifreniz başarıyla güncellendi. Şimdi giriş yapabilirsiniz.')
                return redirect(url_for('main.login'))
            else:
                flash('Geçersiz veya süresi dolmuş token.')

        except Exception as e:
            conn.rollback()
            print(f"Hata: {e}")
            flash('Şifre sıfırlanırken bir hata oluştu.')
        finally:
            cursor.close()
            conn.close()

    return render_template('reset_password.html')

@main.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Kullanıcı bilgilerini güncelle
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        phone = request.form['phone']

        try:
            cursor.execute("""
                UPDATE [user]
                SET first_name = ?, last_name = ?, email = ?, phone = ?
                WHERE id = ?
            """, (first_name, last_name, email, phone, current_user.id))
            conn.commit()
            flash('Bilgileriniz başarıyla güncellendi.', 'success')
        except Exception as e:
            conn.rollback()
            flash(f'Bilgiler güncellenirken bir hata oluştu: {str(e)}', 'error')

    # Kullanıcı bilgilerini ve katıldığı etkinlikleri getir
    cursor.execute("SELECT username, email, first_name, last_name, phone FROM [user] WHERE id = ?", (current_user.id,))
    user_info = cursor.fetchone()

    cursor.execute("""
        SELECT e.title, e.description, e.start_date, e.end_date
        FROM Event e
        JOIN event_participant ep ON e.id = ep.event_id
        WHERE ep.user_id = ?
    """, (current_user.id,))
    joined_events = cursor.fetchall()

    cursor.execute("""
        SELECT points, reason, earned_at FROM user_points WHERE user_id = ?
    """, (current_user.id,))
    user_points = cursor.fetchall()

    # Toplam puanı hesapla
    cursor.execute("SELECT SUM(points) FROM user_points WHERE user_id = ?", (current_user.id,))
    total_points = cursor.fetchone()[0] or 0  # Eğer toplam puan yoksa 0 döndür

    cursor.close()
    conn.close()

    return render_template('profile.html', user_info=user_info, joined_events=joined_events, user_points=user_points, total_points=total_points)




@main.route('/map/<int:event_id>')
@login_required
def map_view(event_id):
    # Etkinlik bilgilerini veritabanından çekiyoruz
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, description, location.STAsText() AS location, category FROM [Event] WHERE id = ?", (event_id,))
    event = cursor.fetchone()  # Tek bir etkinlik

    cursor.close()
    conn.close()

    if not event:
        flash("Etkinlik bulunamadı.")
        return redirect(url_for('main.firstpage'))
    
    # location verisini 'POINT(longitude latitude)' formatından çıkarıyoruz
    location_str = event[3]  # 'POINT (28.9784 41.0082)'
    location_str = location_str.replace('POINT (', '').replace(')', '')
    
    # longitude ve latitude'yi ayırıyoruz
    try:
        longitude, latitude = map(float, location_str.split())  # String'i float'a çevirip iki değere ayırıyoruz
    except ValueError:
        flash("Geçersiz konum verisi.")
        return redirect(url_for('main.firstpage'))

    # Başlangıç (Kocaeli) ve hedef (İstanbul) konumlarını tanımlıyoruz
    start_location = (41.0082, 28.9784)  # Kocaeli'nin koordinatları (örnek)
    end_location = (latitude, longitude)  # Etkinliğin koordinatları

    # 3 farklı ulaşım türüyle rota alıyoruz
    travel_modes = ['driving', 'walking', 'cycling']
    routes = {}
    
    for mode in travel_modes:
        route = get_route(start_location, end_location, mode)
        if route:
            routes[mode] = route['routes'][0]['geometry']

    return render_template('map.html', event=event, longitude=longitude, latitude=latitude, routes=routes, mapbox_access_token=MAPBOX_ACCESS_TOKEN)

# app/routes.py veya main.py içinde
@main.route('/events')
@login_required
def event_list():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT id, title, description, image_url, longitude, latitude FROM Event")
    events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('firstpage.html', events=events)

@main.route('/alleventmap')
@login_required
def alleventmap():
    # Etkinlik verilerini veritabanından çekiyoruz
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id, title, description, location.STAsText() AS location FROM [Event]")
    events = cursor.fetchall()
    
    # Veriyi frontend için düzenliyoruz
    event_list = []
    for event in events:
        location_str = event[3]  # Konum verisi
        location_str = location_str.replace('POINT (', '').replace(')', '')
        try:
            longitude, latitude = map(float, location_str.split())
            event_list.append({
                "id": event[0],
                "title": event[1],
                "description": event[2],
                "longitude": longitude,
                "latitude": latitude
            })
        except ValueError:
            continue  # Geçersiz konum varsa atla

    cursor.close()
    conn.close()
    
    return render_template('alleventmap.html', events=event_list, mapbox_access_token=MAPBOX_ACCESS_TOKEN)

from datetime import datetime
from flask import request, redirect, url_for, flash
from flask_login import current_user
import os

UPLOAD_FOLDER = 'path/to/upload'  # Fotoğraf için dizin
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

@main.route('/create_event', methods=['GET', 'POST'])
@login_required
def create_event():
    if request.method == 'POST':
        # Form verilerini alıyoruz
        title = request.form['title']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        latitude = request.form['location_lat']  # Harita ile gelen konum
        longitude = request.form['location_lon']
        categories = request.form.getlist('category')  # Birden fazla kategori seçimi
        creator_id = current_user.id  # Kullanıcının ID'sini dinamik alıyoruz

        # Tarih formatını düzenliyoruz
        start_date = datetime.strptime(start_date, '%Y-%m-%dT%H:%M')
        end_date = datetime.strptime(end_date, '%Y-%m-%dT%H:%M')

        # Konumu POINT formatına dönüştür
        location_point = f"POINT ({longitude} {latitude})"

        # Etkinliği ekliyoruz
        conn = get_db_connection()
        cursor = conn.cursor()

        # Etkinlik oluşturma SQL sorgusu
        sql = """
        INSERT INTO Event (name, title, description, start_date, end_date, location, category, creator_id)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """
        cursor.execute(sql, (title, title, description, start_date, end_date, location_point, ','.join(categories), creator_id))
        conn.commit()

        # Etkinlik oluşturma işlemi başarılı, kullanıcının puanını 15 arttırıyoruz
        try:
            # Kullanıcıya 15 puan veriyoruz
            cursor.execute("""
                INSERT INTO user_points (user_id, points, reason, earned_at)
                VALUES (?, ?, ?, ?)
            """, (creator_id, 15, 'Etkinlik Oluşturma', datetime.now()))
            conn.commit()

        except Exception as e:
            flash(f"Puan eklenirken bir hata oluştu: {str(e)}")
            conn.rollback()

        finally:
            cursor.close()
            conn.close()

        flash("Etkinlik başarıyla oluşturuldu ve 15 puan kazandınız!")
        return redirect(url_for('main.create_event'))  # Etkinlik oluşturulduktan sonra tekrar aynı sayfaya yönlendirir

    # İlgi alanlarını veritabanından çekiyoruz
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id, interest_name FROM interests")
    interests = cursor.fetchall()
    cursor.close()
    conn.close()

    return render_template('create_event.html', interests=interests, mapbox_access_token=MAPBOX_ACCESS_TOKEN)
@main.route('/join_event/<int:event_id>', methods=['POST'])
@login_required
def join_event(event_id):
    # Kullanıcı ID'sini alıyoruz
    user_id = current_user.id
    print(f"Katılım isteği alınan kullanıcı ID: {user_id}, Etkinlik ID: {event_id}")

    # Veritabanı bağlantısı
    conn = get_db_connection()
    cursor = conn.cursor()

    # Katılmak istenen etkinlik bilgilerini alıyoruz
    cursor.execute("SELECT start_date, end_date FROM [Event] WHERE id = ?", (event_id,))
    event = cursor.fetchone()

    if not event:
        return jsonify({"status": "error", "message": "Etkinlik bulunamadı!"}), 404

    event_start_date = event[0]
    event_end_date = event[1]

    # Kullanıcının katıldığı etkinliklerde çakışma olup olmadığını kontrol ediyoruz
    cursor.execute("""
        SELECT e.id, e.title
        FROM [Event] e
        JOIN event_participant ep ON e.id = ep.event_id
        WHERE ep.user_id = ? AND (
            (e.start_date BETWEEN ? AND ?) OR
            (e.end_date BETWEEN ? AND ?) OR
            (? BETWEEN e.start_date AND e.end_date)
        )
    """, (user_id, event_start_date, event_end_date, event_start_date, event_end_date, event_start_date))

    conflicting_event = cursor.fetchone()

    if conflicting_event:
        return jsonify({
            "status": "error",
            "message": f"Mevcut tarihlerde katıldığınız başka bir etkinlik var: {conflicting_event[1]}"
        }), 400

    # Katılım zamanı
    joined_at = datetime.now()

    try:
        # Katılımı event_participant tablosuna kaydediyoruz
        cursor.execute("""
            INSERT INTO event_participant (user_id, event_id, joined_at)
            VALUES (?, ?, ?)
        """, (user_id, event_id, joined_at))

        # Kullanıcının puanını güncelliyoruz (10 puan ekliyoruz)
        cursor.execute("""
            INSERT INTO user_points (user_id, points, reason, earned_at)
            VALUES (?, ?, ?, ?)
        """, (user_id, 10, 'Etkinliğe Katılım', datetime.now()))

        # Değişiklikleri kaydediyoruz
        conn.commit()

        return jsonify({
            "status": "success",
            "message": "Başarıyla etkinliğe katıldınız ve 10 puan kazandınız!"
        })

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({
            "status": "error",
            "message": f"Katılma işlemi sırasında hata oluştu: {e}"
        }), 500

    finally:
        cursor.close()
        conn.close()

    
@main.route('/chat', methods=['GET'])
@login_required
def chat():
    # Kullanıcının katıldığı etkinlikleri getir
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT e.id, e.title
        FROM Event e
        JOIN event_participant ep ON e.id = ep.event_id
        WHERE ep.user_id = ?
    """, (current_user.id,))
    joined_events = cursor.fetchall()

    cursor.close()
    conn.close()

    return render_template('chat.html', joined_events=joined_events)




@main.route('/chat/messages/<int:event_id>', methods=['GET', 'POST'])
@login_required
def chat_messages(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        # Yeni mesaj ekleme
        message = request.json.get('message')
        timestamp = datetime.now()

        if not message:
            return jsonify({'status': 'error', 'message': 'Mesaj boş olamaz!'}), 400

        cursor.execute("""
            INSERT INTO chat_messages (event_id, user_id, message, timestamp)
            VALUES (?, ?, ?, ?)
        """, (event_id, current_user.id, message, timestamp))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({'status': 'success', 'message': 'Mesaj gönderildi!'})

    # Eski mesajları çekme
    cursor.execute("""
        SELECT cm.message, u.username, cm.timestamp
        FROM chat_messages cm
        JOIN [user] u ON cm.user_id = u.id
        WHERE cm.event_id = ?
        ORDER BY cm.timestamp ASC
    """, (event_id,))
    messages = cursor.fetchall()

    cursor.close()
    conn.close()

    # Mesajları JSON formatında döndür
    return jsonify({'status': 'success', 'messages': [
        {'username': msg[1], 'message': msg[0], 'timestamp': msg[2]} for msg in messages
    ]})


@main.route('/notifications', methods=['GET'])
@login_required
def get_notifications():
    try:
        print("Bildirimler istendi - Kullanıcı:", current_user.id)
        conn = get_db_connection()
        cursor = conn.cursor()
        

        cursor.execute("""
            SELECT id, event_id, message, timestamp
            FROM notifications
            WHERE user_id = ? AND is_read = 0
            ORDER BY timestamp DESC
        """, (current_user.id,))
        
        notifications = cursor.fetchall()
        print("Bulunan bildirimler:", notifications)

        result = []
        for n in notifications:
            notification_data = {
                'id': n[0],
                'event_id': n[1],
                'message': n[2],
                'timestamp': n[3]
            }
            result.append(notification_data)

        cursor.close()
        conn.close()

        return jsonify({
            'status': 'success',
            'notifications': result
        })

    except Exception as e:
        print("Hata oluştu:", str(e))
        return jsonify({
            'status': 'error',
            'message': str(e)
        }), 500

@main.route('/notifications/read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_as_read(notification_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE notifications
        SET is_read = 1
        WHERE id = ? AND user_id = ?
    """, (notification_id, current_user.id))

    conn.commit()
    cursor.close()
    conn.close()

    return jsonify({'status': 'success', 'message': 'Bildirim okundu!'})


def is_admin(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT is_admin FROM [User] WHERE id = ?", (user_id,))
    result = cursor.fetchone()

    conn.close()

    if result:
        return result[0]  # is_admin değeri doğrudan döndürülür
    return False

@main.route('/admin_panel', methods=['GET'])
@login_required
def admin_panel():
    if not is_admin(current_user.id):
        flash("Bu sayfaya erişim izniniz yok.")
        return redirect(url_for('main.home'))

    conn = get_db_connection()
    cursor = conn.cursor()

    # Kullanıcıları veritabanından çekiyoruz
    try:
        cursor.execute("""
            SELECT id, username, email, first_name, last_name, birth_date, gender, phone, is_admin, is_active
            FROM [User]
        """)
        users = cursor.fetchall()
    except Exception as e:
        print("Kullanıcıları çekerken hata:", e)
        flash("Kullanıcıları çekerken bir hata oluştu.")
        users = []

    # Etkinlikleri veritabanından çekiyoruz
    try:
        cursor.execute("""
            SELECT id, title, description, start_date, end_date, location.STAsText() AS location, 
                   category, creator_id, is_approved, created_at
            FROM [Event]
        """)
        events = cursor.fetchall()

        # Konum verilerini işleme
        formatted_events = []
        for event in events:
            location_str = event[5]  # location.STAsText() sonucu
            if location_str:
                location_str = location_str.replace('POINT (', '').replace(')', '')
                try:
                    longitude, latitude = map(float, location_str.split())
                except ValueError:
                    longitude, latitude = None, None
            else:
                longitude, latitude = None, None

            formatted_events.append({
                "id": event[0],
                "title": event[1],
                "description": event[2],
                "start_date": event[3],
                "end_date": event[4],
                "longitude": longitude,
                "latitude": latitude,
                "category": event[6],
                "creator_id": event[7],
                "is_approved": event[8],
                "created_at": event[9]
            })

    except Exception as e:
        print("Etkinlikleri çekerken hata:", e)
        flash("Etkinlikleri çekerken bir hata oluştu.")
        formatted_events = []

    finally:
        cursor.close()
        conn.close()

    return render_template('admin_panel.html', users=users, events=formatted_events)


@main.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
@login_required
def edit_user(user_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        birth_date = request.form['birth_date']

        try:
            cursor.execute("""
                UPDATE [User]
                SET username = ?, email = ?, birth_date = ?
                WHERE id = ?
            """, (username, email, birth_date, user_id))
            conn.commit()
            flash("Kullanıcı bilgileri başarıyla güncellendi.")
            return redirect(url_for('main.admin_panel'))
        except Exception as e:
            conn.rollback()
            flash(f"Kullanıcı güncellenirken bir hata oluştu: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    # GET isteği: Kullanıcının mevcut bilgilerini getir
    cursor.execute("SELECT id,username,email,birth_date,is_active,is_admin,gender,phone FROM [User] WHERE id = ?", (user_id,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit_user.html', user=user)

@main.route('/delete_user/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    # Veritabanı bağlantısını aç
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Kullanıcıya ait tüm etkinlikleri sil (katılımcıysa ve oluşturucuysa)
        cursor.execute("DELETE FROM event_participant WHERE user_id = ?", (user_id,))
        cursor.execute("DELETE FROM event WHERE creator_id = ?", (user_id,))

        # Kullanıcının tüm ilişkili diğer verilerini de sil (varsa)
        cursor.execute("DELETE FROM event_participant WHERE user_id = ?", (user_id,))  # Örneğin katılımcılar

        # Kullanıcıyı sil
        cursor.execute("DELETE FROM users WHERE id = ?", (user_id,))

        # Değişiklikleri kaydet
        conn.commit()

        flash("Kullanıcı ve ilişkili tüm veriler başarıyla silindi.")

    except Exception as e:
        conn.rollback()
        flash(f"Kullanıcı silinirken bir hata oluştu: {str(e)}")

    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('main.admin_panel'))






@main.route('/delete_event/<int:event_id>', methods=['POST'])
@login_required
def delete_event(event_id):
    # Veritabanı bağlantısı
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # Event_participant tablosundaki ilişkili kayıtları sil
        cursor.execute("DELETE FROM event_participant WHERE event_id = ?", (event_id,))
        conn.commit()

        # Etkinliği sil
        cursor.execute("DELETE FROM Event WHERE id = ?", (event_id,))
        conn.commit()

        flash("Etkinlik başarıyla silindi.")
    except Exception as e:
        conn.rollback()
        flash(f"Etkinlik silinirken bir hata oluştu: {str(e)}")
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for('main.admin_panel'))


@main.route('/edit_event/<int:event_id>', methods=['GET', 'POST'])
@login_required
def edit_event(event_id):
    conn = get_db_connection()
    cursor = conn.cursor()

    if request.method == 'POST':
        title = request.form['title']
        description = request.form['description']
        start_date = request.form['start_date']
        end_date = request.form['end_date']
        category = request.form['category']

        try:
            cursor.execute("""
                UPDATE Event
                SET title = ?, description = ?, start_date = ?, end_date = ?, category = ?
                WHERE id = ?
            """, (title, description, start_date, end_date, category, event_id))
            conn.commit()
            flash("Etkinlik başarıyla güncellendi.")
            return redirect(url_for('main.admin_panel'))
        except Exception as e:
            conn.rollback()
            flash(f"Etkinlik güncellenirken bir hata oluştu: {str(e)}")
        finally:
            cursor.close()
            conn.close()

    # GET isteği: Mevcut etkinlik bilgilerini getir
    cursor.execute("SELECT id, title, description, start_date, end_date, category FROM Event WHERE id = ?", (event_id,))
    event = cursor.fetchone()
    cursor.close()
    conn.close()

    return render_template('edit_event.html', event=event)



@main.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Verify exact column names
            cursor.execute("""
                SELECT id, password, is_admin FROM [user]
                WHERE username = ?
            """, (username,))
            user = cursor.fetchone()

            if not user:
                flash("Kullanıcı bulunamadı.", "danger")
                return redirect(url_for('main.admin_login'))

            user_id, hashed_password, is_admin = user

            # Admin kontrolü - farklı kontrol yöntemleri
            if is_admin is None or is_admin == 0:
                flash("Bu kullanıcı bir admin değil.", "danger")
                return redirect(url_for('main.admin_login'))

            # Şifre doğrulama
            if check_password_hash(hashed_password, password):
                user = User.get_by_id(user_id)
                login_user(user)

                flash('Admin girişi başarılı!', 'success')
                return redirect(url_for('main.admin_panel'))
            else:
                flash('Geçersiz şifre.', 'danger')
        except Exception as e:
            flash(f"Hata oluştu: {str(e)}", "danger")
        finally:
            cursor.close()
            conn.close()

    return render_template('admin_login.html')


@main.route('/admin_logout')
def admin_logout():
    session.pop('admin_logged_in', None)
    return redirect(url_for('main.home'))














