import pyodbc
from datetime import datetime

# Veritabanı bağlantısını yapacak fonksiyon
def get_db_connection():
    conn = pyodbc.connect('DRIVER={ODBC Driver 17 for SQL Server};'
                          'SERVER=DESKTOP-8MG4EKJ\SQLEXPRESS;'
                          'DATABASE=YOUR_DATABASE_NAME;'
                          'UID=YOUR_USERNAME;'
                          'PWD=YOUR_PASSWORD')
    return conn

# Çakışma kontrolü yapacak fonksiyon
def check_event_participation(user_id, start_date, end_date):
    conn = get_db_connection()
    cursor = conn.cursor()

    # Kullanıcının katıldığı etkinliklerdeki tarihleri kontrol eden SQL sorgusu
    cursor.execute("""
        SELECT e.id, e.start_date, e.end_date
        FROM event_participant ep
        JOIN event e ON ep.event_id = e.id
        WHERE ep.user_id = ? 
        AND (
            (? BETWEEN e.start_date AND e.end_date)
            OR (? BETWEEN e.start_date AND e.end_date)
            OR (e.start_date BETWEEN ? AND ?)
            OR (e.end_date BETWEEN ? AND ?)
        )
    """, (user_id, start_date, end_date, start_date, end_date, start_date, end_date))

    conflicting_events = cursor.fetchall()  # Çakışan etkinlikler varsa al

    cursor.close()
    conn.close()

    # Eğer çakışan etkinlikler varsa, True döndür
    if conflicting_events:
        return True
    else:
        return False

# Kullanıcının etkinlik kaydına göre çakışma kontrolü
def register_for_event(user_id, event_id, start_date, end_date):
    # Çakışmayı kontrol et
    if check_event_participation(user_id, start_date, end_date):
        print("Mevcut tarihlerde katıldığınız başka bir etkinlik var. Katılamazsınız!")
        return False  # Etkinlik kaydı engellendi
    else:
        print("Etkinliğe katılım başarılı!")
        # Burada etkinliğe katılım işlemi yapılabilir (insert işlemi)
        return True  # Etkinlik kaydı başarılı

# Test amacıyla bir örnek
if __name__ == "__main__":
    user_id = 1  # Örnek kullanıcı ID'si
    event_id = 2  # Katılmak istenen etkinlik ID'si
    start_date = '2024-12-01'  # Etkinlik başlangıç tarihi
    end_date = '2024-12-05'    # Etkinlik bitiş tarihi
    
    if register_for_event(user_id, event_id, start_date, end_date):
        print("Etkinlik kaydınız başarıyla alındı.")
    else:
        print("Etkinlik kaydınız yapılmadı.")
