from datetime import timedelta

# config.py
MAPBOX_ACCESS_TOKEN = "pk.eyJ1IjoiZGV2ZWxvcGVyZmF0aWgiLCJhIjoiY20zNGFuMzlkMW1qejJrc2p6bWhiMjlyeiJ9.za4KWnRN9gFovJEUmf0uOw"
ELASTIC_EMAIL_API_KEY = '6A328E770A74F9020C9B91DF54C2EF6EF642C10CB806A7355D6812A64F6FD3ABC064405D67C8BA37C949D76A0F76DC9E'
class Config:
    SECRET_KEY = 'gizli_anahtariniz_buraya'  # Production'da güvenli bir key kullanın
    PERMANENT_SESSION_LIFETIME = timedelta(minutes=60)
    SESSION_COOKIE_HTTPONLY = True

class DevelopmentConfig(Config):
    DEBUG = True
    

class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    