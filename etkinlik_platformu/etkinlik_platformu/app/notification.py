# notifications.py
from flask import jsonify, current_app
from datetime import datetime
import pyodbc

def get_db_connection():
    return pyodbc.connect(
        'DRIVER={ODBC Driver 17 for SQL Server};'
        'SERVER=DESKTOP-8MG4EKJ\SQLEXPRESS;'
        'DATABASE=Etkinlik_Platformu;'
        'Trusted_Connection=yes;'
    )

class NotificationSystem:
    def __init__(self, user_id):
        self.user_id = user_id
        
    def get_notifications(self, include_read=False):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            query = """
                SELECT id, event_id, message, timestamp, is_read
                FROM notifications
                WHERE user_id = ?
                {}
                ORDER BY timestamp DESC
            """.format("" if include_read else "AND is_read = 0")
            
            cursor.execute(query, (self.user_id,))
            notifications = cursor.fetchall()
            
            result = [{
                'id': n['id'],
                'event_id': n['event_id'],
                'message': n['message'],
                'timestamp': n['timestamp'],
                'is_read': bool(n['is_read'])
            } for n in notifications]
            
            return result
            
        except Exception as e:
            current_app.logger.error(f"Error fetching notifications: {str(e)}")
            return []
            
        finally:
            cursor.close()
            conn.close()
    
    def mark_as_read(self, notification_id=None):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            if notification_id:
                # Tek bir bildirimi okundu olarak işaretle
                cursor.execute("""
                    UPDATE notifications
                    SET is_read = 1, read_at = ?
                    WHERE id = ? AND user_id = ?
                """, (datetime.now().isoformat(), notification_id, self.user_id))
            else:
                # Tüm bildirimleri okundu olarak işaretle
                cursor.execute("""
                    UPDATE notifications
                    SET is_read = 1, read_at = ?
                    WHERE user_id = ? AND is_read = 0
                """, (datetime.now().isoformat(), self.user_id))
            
            conn.commit()
            return True
            
        except Exception as e:
            current_app.logger.error(f"Error marking notification as read: {str(e)}")
            return False
            
        finally:
            cursor.close()
            conn.close()
    
    def add_notification(self, message, event_id=None):
        try:
            conn = get_db_connection()
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO notifications (user_id, event_id, message, timestamp, is_read)
                VALUES (?, ?, ?, ?, 0)
            """, (self.user_id, event_id, message, datetime.now().isoformat()))
            
            conn.commit()
            return cursor.lastrowid
            
        except Exception as e:
            current_app.logger.error(f"Error adding notification: {str(e)}")
            return None
            
        finally:
            cursor.close()
            conn.close()