from flask_login import UserMixin
import pyodbc

def get_db_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=DESKTOP-8MG4EKJ\SQLEXPRESS;'
        'DATABASE=Etkinlik_Platformu;'
        'Trusted_Connection=yes;'
    )

class User(UserMixin):
    def __init__(self, id, username, email, password=None, first_name=None, last_name=None,
                 birth_date=None, gender=None, phone=None, profile_photo=None, is_active=True, is_admin=None):
        self.id = id
        self.username = username
        self.email = email
        self.password = password
        self.first_name = first_name
        self.last_name = last_name
        self.birth_date = birth_date
        self.gender = gender
        self.phone = phone
        self.profile_photo = profile_photo
        self.interests = []  # İlgi alanlarını tutacak liste
        self._is_active = is_active  # Burada private bir değişken kullanıyoruz
        self.is_admin = is_admin
    @property
    def is_active(self):
        return self._is_active

    @staticmethod
    def get_by_id(user_id):
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Kullanıcı bilgilerini al
        cursor.execute("""
            SELECT id, username, email, password, first_name, last_name, 
                   birth_date, gender, phone, profile_photo, is_active 
            FROM [User] 
            WHERE id = ?
        """, (user_id,))
        user_data = cursor.fetchone()
        
        if user_data:
            user = User(
                id=user_data[0],
                username=user_data[1],
                email=user_data[2],
                password=user_data[3],
                first_name=user_data[4],
                last_name=user_data[5],
                birth_date=user_data[6],
                gender=user_data[7],
                phone=user_data[8],
                profile_photo=user_data[9],
                is_active=user_data[10]  # is_active verisi ekleniyor
            )
            
            # İlgi alanlarını al
            cursor.execute("""
                SELECT interest 
                FROM user_interests 
                WHERE user_id = ?
            """, (user_id,))
            interests = cursor.fetchall()
            user.interests = [interest[0] for interest in interests]
            
            cursor.close()
            conn.close()
            return user
            
        cursor.close()
        conn.close()
        return None
    
class Event:
    @staticmethod
    def get_all_events():
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM [Event]")
        return cursor.fetchall()
