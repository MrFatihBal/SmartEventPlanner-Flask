# SmartEventPlanner-Flask
# 🎉 Etkinlik Platformu - Flask Tabanlı Web Uygulaması

Bu proje, kullanıcıların etkinlik oluşturabildiği, etkinliklere katılabildiği ve sistemin bildirim gönderdiği Flask tabanlı bir etkinlik yönetim platformudur.

## 🚀 Özellikler

- 👥 Kullanıcı girişi ve kaydı
- 📅 Etkinlik oluşturma ve listeleme
- 🔔 Bildirim sistemi (`notification.py`)
- 🧠 Olası çatışmalar için çözüm algoritması (`cakisma.py`)
- 📁 SQLite ve SQLAlchemy ile veri yönetimi
- 🌐 HTML tabanlı arayüz (Jinja2 - `templates/` klasörü içinde)

## 🧩 Proje Yapısı
etkinlik_platformu/
├── app/ # Ana uygulama
│ ├── models.py # Veritabanı modelleri
│ ├── routes.py # Tüm route işlemleri
│ ├── notification.py # Bildirim sistemi
│ ├── cakisma.py # Etkinlik çakışma algoritması
│ └── templates/ # HTML şablonlar
├── static/ # CSS, JS dosyaları
├── config.py # Ayarlar
├── run.py # Uygulama başlatıcı
├── api.py # API endpoint'leri
├── migrations/ # Alembic migration dosyaları
└── venv/ # Sanal ortam 

