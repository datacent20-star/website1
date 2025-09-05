from flask import Flask, render_template, request, redirect, url_for, flash, abort, jsonify, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
import os
from datetime import datetime
import requests
import json
import threading
import re

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key-here-change-in-production'

# Initialize Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Telegram конфигурация
TELEGRAM_BOT_TOKEN = '7910995507:AAEoOR8OdaqkSFyWhr5mIFmGJ1wus-7fPUk'
TELEGRAM_CHAT_ID = '-1002275825444'

class User(UserMixin):
    def __init__(self, id, username, password_hash):
        self.id = id
        self.username = username
        self.password_hash = password_hash

# Функции для работы с Telegram через requests
def send_telegram_message(chat_id, message):
    """Отправка сообщения в Telegram через API"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram message: {e}")
        return None

def send_telegram_reply(chat_id, message, reply_to_message_id=None):
    """Отправка ответа в Telegram"""
    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }
        if reply_to_message_id:
            data['reply_to_message_id'] = reply_to_message_id
            
        response = requests.post(url, data=data, timeout=10)
        return response.json()
    except Exception as e:
        print(f"Error sending Telegram reply: {e}")
        return None

def send_telegram_notification(service_type, data):
    """Отправка уведомления о заявке"""
    try:
        if service_type == 'callback':
            message = f"📞 <b>НОВА ЗАЯВКА НА ДЗВІНОК</b>\n\n" \
                     f"👤 Ім'я: {data['name']}\n" \
                     f"📞 Телефон: {data['phone']}\n" \
                     f"⏰ Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        elif service_type == 'service':
            message = f"🚀 <b>НОВА ЗАЯВКА НА ПОСЛУГУ</b>\n\n" \
                     f"📋 Послуга: {data['service_title']}\n" \
                     f"👤 Ім'я: {data['name']}\n" \
                     f"📞 Телефон: {data['phone']}\n" \
                     f"📧 Email: {data.get('email', 'Не вказано')}\n" \
                     f"🏠 Адреса: {data.get('address', 'Не вказано')}\n" \
                     f"💬 Коментар: {data.get('message', 'Не вказано')}\n" \
                     f"⏰ Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        elif service_type == 'promotion':
            message = f"🎯 <b>НОВА ЗАЯВКА ЗА АКЦІЄЮ</b>\n\n" \
                     f"👤 Ім'я: {data['name']}\n" \
                     f"📞 Телефон: {data['phone']}\n" \
                     f"📧 Email: {data.get('email', 'Не вказано')}\n" \
                     f"🏠 Адреса: {data.get('address', 'Не вказано')}\n" \
                     f"📋 Тариф: {data.get('tariff', 'Не вказано')}\n" \
                     f"💬 Коментар: {data.get('comment', 'Не вказано')}\n" \
                     f"⏰ Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        elif service_type == 'chat':
            message = f"💬 <b>НОВЕ ПОВІДОМЛЕННЯ В ЧАТІ</b>\n\n" \
                     f"👤 Користувач: {data['user']}\n" \
                     f"📝 Повідомлення: {data['message']}\n" \
                     f"🆔 ID сесії: {data['session_id']}\n" \
                     f"⏰ Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n" \
                     f"💡 <i>Для відповіді відправте: /reply {data['session_id']} ваш текст</i>"
        
        elif service_type == 'review':
            message = f"⭐ <b>НОВИЙ ВІДГУК</b>\n\n" \
                     f"👤 Ім'я: {data['name']}\n" \
                     f"⭐ Оцінка: {'★' * data['rating']}{'☆' * (5 - data['rating'])}\n" \
                     f"📝 Відгук: {data['text'][:100]}...\n" \
                     f"⏰ Час: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        
        # Отправляем сообщение
        result = send_telegram_message(TELEGRAM_CHAT_ID, message)
        if result and not result.get('ok'):
            print(f"Telegram API error: {result}")
        
        return result
        
    except Exception as e:
        print(f"Error in send_telegram_notification: {e}")

def handle_telegram_command(message_text, chat_id):
    """Обработка команд из Telegram"""
    try:
        if message_text.startswith('/reply'):
            # Формат: /reply session_id текст ответа
            match = re.match(r'/reply\s+(\S+)\s+(.+)', message_text)
            if match:
                session_id = match.group(1)
                reply_text = match.group(2)
                
                # Сохраняем ответ в базу
                conn = sqlite3.connect('database.db')
                c = conn.cursor()
                c.execute("INSERT INTO chat_messages (session_id, admin_message, is_from_user) VALUES (?, ?, ?)",
                         (session_id, reply_text, False))
                conn.commit()
                conn.close()
                
                # Отправляем подтверждение
                send_telegram_message(chat_id, f"✅ Відповідь для сесії {session_id} відправлена: {reply_text}")
                return True
                
        elif message_text.startswith('/help'):
            help_text = (
                "🤖 <b>Команди бота:</b>\n\n"
                "/help - Допомога\n"
                "/reply [session_id] [текст] - Відповісти клієнту\n"
                "/stats - Статистика заявок\n"
                "/list - Список активних сесій"
            )
            send_telegram_message(chat_id, help_text)
            return True
            
    except Exception as e:
        print(f"Error handling Telegram command: {e}")
        send_telegram_message(chat_id, "❌ Помилка обробки команди")
    
    return False

# Create database and tables if they don't exist
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Create news table
    c.execute('''CREATE TABLE IF NOT EXISTS news
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  content TEXT NOT NULL,
                  image_url TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create services table
    c.execute('''CREATE TABLE IF NOT EXISTS services
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  title TEXT NOT NULL,
                  description TEXT NOT NULL,
                  image_url TEXT,
                  form_title TEXT,
                  form_fields TEXT)''')
    
    # Create callback requests table
    c.execute('''CREATE TABLE IF NOT EXISTS callback_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  status TEXT DEFAULT 'new',
                  telegram_message_id TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create service requests table
    c.execute('''CREATE TABLE IF NOT EXISTS service_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  service_id INTEGER,
                  service_title TEXT,
                  name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  email TEXT,
                  address TEXT,
                  message TEXT,
                  status TEXT DEFAULT 'new',
                  telegram_message_id TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  FOREIGN KEY (service_id) REFERENCES services (id))''')
    
    # Create promotion requests table
    c.execute('''CREATE TABLE IF NOT EXISTS promotion_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT NOT NULL,
                  phone TEXT NOT NULL,
                  email TEXT,
                  address TEXT,
                  tariff TEXT,
                  comment TEXT,
                  status TEXT DEFAULT 'new',
                  telegram_message_id TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create chat messages table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_messages
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT NOT NULL,
                  user_message TEXT,
                  admin_message TEXT,
                  is_from_user BOOLEAN,
                  telegram_message_id TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create chat sessions table
    c.execute('''CREATE TABLE IF NOT EXISTS chat_sessions
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  session_id TEXT UNIQUE NOT NULL,
                  telegram_chat_id TEXT,
                  user_name TEXT,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create reviews table
    c.execute('''CREATE TABLE IF NOT EXISTS reviews
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  client_name TEXT NOT NULL,
                  rating INTEGER CHECK(rating >= 1 AND rating <= 5),
                  text TEXT NOT NULL,
                  is_approved BOOLEAN DEFAULT FALSE,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Create FAQ table
    c.execute('''CREATE TABLE IF NOT EXISTS faq
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  question TEXT NOT NULL,
                  answer TEXT NOT NULL,
                  category TEXT,
                  order_index INTEGER DEFAULT 0,
                  is_active BOOLEAN DEFAULT TRUE)''')
    
    # Create admin user table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password_hash TEXT NOT NULL)''')
    
    # Check if admin user exists, if not create one
    c.execute("SELECT COUNT(*) FROM users WHERE username = 'admin'")
    if c.fetchone()[0] == 0:
        password_hash = generate_password_hash('admin')
        c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", 
                 ('admin', password_hash))
    
    # Add sample services
    c.execute("SELECT COUNT(*) FROM services")
    if c.fetchone()[0] == 0:
        sample_services = [
            ('Інтернет для дому', 'Швидкісний інтернет для вашого будинку', '', 'Підключення інтернету', 'name,phone,address'),
            ('Цифрове TV', 'Якісне телебачення з сотнями каналів', '', 'Підключення TV', 'name,phone,package'),
            ('Відеоспостереження', 'Системи безпеки для вашого дому', '', 'Замовлення відеоспостереження', 'name,phone,address,rooms'),
            ('Інтернет для бізнесу', 'Надійні рішення для вашого бізнесу', '', 'Консультація для бізнесу', 'name,company,phone,email')
        ]
        
        for service in sample_services:
            c.execute("INSERT INTO services (title, description, image_url, form_title, form_fields) VALUES (?, ?, ?, ?, ?)", service)
    
    # Add sample news
    c.execute("SELECT COUNT(*) FROM news")
    if c.fetchone()[0] == 0:
        c.execute("INSERT INTO news (title, content, image_url) VALUES (?, ?, ?)",
                 ('Ласкаво просимо до нашого сайту!', 'Ми раді вітати вас на нашому новому сайті. Тут ви знайдете всю необхідну інформацію про наші послуги.', ''))
        c.execute("INSERT INTO news (title, content, image_url) VALUES (?, ?, ?)",
                 ('Нові тарифи на інтернет', 'Запускаємо нові тарифи з підвищеною швидкістю та кращими умовами для наших клієнтів.', ''))
    
    # Add sample FAQ
    c.execute("SELECT COUNT(*) FROM faq")
    if c.fetchone()[0] == 0:
        sample_faq = [
            ('Як підключити інтернет?', 'Для підключення інтернету заповніть форму на нашому сайті або зателефонуйте нам.', 'Підключення'),
            ('Які способи оплати?', 'Ми приймаємо оплату готівкою, банківською карткою та через термінали.', 'Оплата'),
            ('Як відновити доступ?', 'Зв\'яжіться з нашою технічною підтримкою для відновлення доступу.', 'Техпідтримка')
        ]
        
        for faq in sample_faq:
            c.execute("INSERT INTO faq (question, answer, category) VALUES (?, ?, ?)", faq)
    
    conn.commit()
    conn.close()

# User loader callback
@login_manager.user_loader
def load_user(user_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_data = c.fetchone()
    conn.close()
    
    if user_data:
        return User(id=user_data[0], username=user_data[1], password_hash=user_data[2])
    return None

# Routes
@app.route('/')
def index():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM news ORDER BY created_at DESC LIMIT 3")
    news_items = c.fetchall()
    
    c.execute("SELECT * FROM services")
    services = c.fetchall()
    conn.close()
    
    return render_template('index.html', news_items=news_items, services=services)

@app.route('/tariffs')
def tariffs():
    tariff_type = request.args.get('type', 'apartment')
    return render_template('tariffs.html', tariff_type=tariff_type)

@app.route('/promotions')
def promotions():
    return render_template('promotions.html')

@app.route('/news')
def news():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM news ORDER BY created_at DESC")
    news_items = c.fetchall()
    conn.close()
    
    return render_template('news.html', news_items=news_items)

@app.route('/news/<int:news_id>')
def news_item(news_id):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM news WHERE id = ?", (news_id,))
    news_item = c.fetchone()
    conn.close()
    
    if news_item is None:
        abort(404)
        
    return render_template('news_item.html', news_item=news_item)

@app.route('/reviews')
def reviews():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reviews WHERE is_approved = TRUE ORDER BY created_at DESC")
    reviews = c.fetchall()
    conn.close()
    
    return render_template('reviews.html', reviews=reviews)

@app.route('/faq')
def faq():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM faq WHERE is_active = TRUE ORDER BY order_index, category")
    faq_items = c.fetchall()
    conn.close()
    
    # Группируем по категориям
    faq_by_category = {}
    for item in faq_items:
        category = item[3] or 'Загальні питання'
        if category not in faq_by_category:
            faq_by_category[category] = []
        faq_by_category[category].append(item)
    
    return render_template('faq.html', faq_by_category=faq_by_category)

# API Routes
@app.route('/get_service/<int:service_id>')
def get_service(service_id):
    try:
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM services WHERE id = ?", (service_id,))
        service = c.fetchone()
        conn.close()
        
        if service:
            return jsonify({
                'id': service[0],
                'title': service[1],
                'description': service[2],
                'image_url': service[3],
                'form_title': service[4],
                'form_fields': service[5].split(',')
            })
        return jsonify({'error': 'Service not found'}), 404
    except Exception as e:
        print(f"Error in get_service: {e}")
        return jsonify({'error': 'Internal server error'}), 500

@app.route('/callback', methods=['POST'])
def callback():
    try:
        phone = request.form.get('phone')
        name = request.form.get('name', 'Клієнт')
        
        if not phone:
            flash('Будь ласка, введіть номер телефону')
            return redirect(url_for('index'))
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO callback_requests (name, phone) VALUES (?, ?)", 
                 (name, phone))
        conn.commit()
        conn.close()
        
        # Отправляем уведомление в Telegram
        send_telegram_notification('callback', {
            'name': name,
            'phone': phone
        })
        
        flash('Дякуємо! Ми вам передзвонимо найближчим часом.')
        return redirect(url_for('index'))
        
    except Exception as e:
        print(f"Error in callback: {e}")
        flash('Помилка при відправці заявки. Спробуйте ще раз.')
        return redirect(url_for('index'))

@app.route('/api/callback_request', methods=['POST'])
def callback_request():
    try:
        name = request.form.get('name')
        phone = request.form.get('phone')
        
        if not name or not phone:
            return jsonify({'success': False, 'message': 'Будь ласка, заповніть всі обов\'язкові поля.'}), 400
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO callback_requests (name, phone) VALUES (?, ?)", 
                 (name, phone))
        conn.commit()
        conn.close()
        
        # Отправляем уведомление в Telegram
        send_telegram_notification('callback', {
            'name': name,
            'phone': phone
        })
        
        return jsonify({'success': True, 'message': 'Дякуємо! Ми вам передзвонимо найближчим часом.'})
    except Exception as e:
        print(f"Error in callback_request: {e}")
        return jsonify({'success': False, 'message': 'Помилка при відправці заявки. Спробуйте ще раз.'}), 500

@app.route('/api/chat_message', methods=['POST'])
def chat_message():
    try:
        message = request.form.get('message')
        session_id = request.form.get('session_id', 'default')
        user = request.form.get('user', 'Гість')
        
        if not message:
            return jsonify({'success': False, 'message': 'Повідомлення не може бути порожнім.'}), 400
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO chat_messages (session_id, user_message, is_from_user) VALUES (?, ?, ?)",
                 (session_id, message, True))
        
        # Сохраняем сессию
        c.execute("INSERT OR IGNORE INTO chat_sessions (session_id, user_name) VALUES (?, ?)",
                 (session_id, user))
        
        conn.commit()
        conn.close()
        
        # Отправляем уведомление в Telegram
        send_telegram_notification('chat', {
            'user': user,
            'message': message,
            'session_id': session_id
        })
        
        return jsonify({'success': True, 'message': 'Повідомлення відправлено. Ми відповімо вам найближчим часом.'})
    except Exception as e:
        print(f"Error in chat_message: {e}")
        return jsonify({'success': False, 'message': 'Помилка при відправці повідомлення. Спробуйте ще раз.'}), 500

@app.route('/api/submit_service_form/<int:service_id>', methods=['POST'])
def submit_service_form(service_id):
    try:
        form_data = request.get_json()
        
        if not form_data:
            return jsonify({'success': False, 'message': 'Дані не отримані.'}), 400
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        # Получаем информацию об услуге
        c.execute("SELECT title FROM services WHERE id = ?", (service_id,))
        service = c.fetchone()
        service_title = service[0] if service else "Невідома послуга"
        
        # Сохраняем заявку
        c.execute("INSERT INTO service_requests (service_id, service_title, name, phone, email, address, message) VALUES (?, ?, ?, ?, ?, ?, ?)",
                 (service_id, 
                  service_title,
                  form_data.get('name', ''),
                  form_data.get('phone', ''),
                  form_data.get('email', ''),
                  form_data.get('address', ''),
                  form_data.get('message', '')))
        
        conn.commit()
        conn.close()
        
        # Отправляем уведомление в Telegram
        send_telegram_notification('service', {
            'service_title': service_title,
            'name': form_data.get('name', ''),
            'phone': form_data.get('phone', ''),
            'email': form_data.get('email', ''),
            'address': form_data.get('address', ''),
            'message': form_data.get('message', '')
        })
        
        return jsonify({'success': True, 'message': 'Дякуємо! Ваша заявка прийнята. Ми зв\'яжемося з вами найближчим часом.'})
    except Exception as e:
        print(f"Error in submit_service_form: {e}")
        return jsonify({'success': False, 'message': 'Помилка при відправці форми. Спробуйте ще раз.'}), 500

@app.route('/api/submit_promotion_form', methods=['POST'])
def submit_promotion_form():
    try:
        form_data = request.get_json()
        
        if not form_data:
            return jsonify({'success': False, 'message': 'Дані не отримані.'}), 400
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        
        # Сохраняем заявку по акции
        c.execute("INSERT INTO promotion_requests (name, phone, email, address, tariff, comment) VALUES (?, ?, ?, ?, ?, ?)",
                 (form_data.get('name', ''),
                  form_data.get('phone', ''),
                  form_data.get('email', ''),
                  form_data.get('address', ''),
                  form_data.get('tariff', ''),
                  form_data.get('comment', '')))
        
        conn.commit()
        conn.close()
        
        # Отправляем уведомление в Telegram
        send_telegram_notification('promotion', {
            'name': form_data.get('name', ''),
            'phone': form_data.get('phone', ''),
            'email': form_data.get('email', ''),
            'address': form_data.get('address', ''),
            'tariff': form_data.get('tariff', ''),
            'comment': form_data.get('comment', '')
        })
        
        return jsonify({'success': True, 'message': 'Дякуємо! Ваша заявка на акцію прийнята. Ми зв\'яжемося з вами найближчим часом.'})
    except Exception as e:
        print(f"Error in submit_promotion_form: {e}")
        return jsonify({'success': False, 'message': 'Помилка при відправці форми. Спробуйте ще раз.'}), 500

@app.route('/api/add_review', methods=['POST'])
def add_review():
    try:
        name = request.form.get('name')
        rating = request.form.get('rating')
        text = request.form.get('text')
        
        if not name or not rating or not text:
            return jsonify({'success': False, 'message': 'Будь ласка, заповніть всі обов\'язкові поля.'}), 400
        
        rating = int(rating)
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("INSERT INTO reviews (client_name, rating, text) VALUES (?, ?, ?)",
                 (name, rating, text))
        conn.commit()
        conn.close()
        
        # Отправляем уведомление в Telegram
        send_telegram_notification('review', {
            'name': name,
            'rating': rating,
            'text': text
        })
        
        return jsonify({'success': True, 'message': 'Дякуємо за ваш відгук! Він буде опублікований після перевірки модератором.'})
    except Exception as e:
        print(f"Error in add_review: {e}")
        return jsonify({'success': False, 'message': 'Помилка при додаванні відгуку. Спробуйте ще раз.'}), 500

# Telegram webhook для обработки сообщений
@app.route('/telegram_webhook', methods=['POST'])
def telegram_webhook():
    try:
        data = request.get_json()
        if 'message' in data:
            message = data['message']
            chat_id = message['chat']['id']
            text = message.get('text', '')
            
            # Обрабатываем команды
            if text.startswith('/'):
                handle_telegram_command(text, chat_id)
            else:
                # Простое эхо для теста
                send_telegram_message(chat_id, "✅ Повідомлення отримано. Використовуйте /help для допомоги.")
                
        return jsonify({'status': 'ok'})
    except Exception as e:
        print(f"Error in telegram_webhook: {e}")
        return jsonify({'status': 'error'}), 500

# Admin routes
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE username = ?", (username,))
        user_data = c.fetchone()
        conn.close()
        
        if user_data and check_password_hash(user_data[2], password):
            user = User(id=user_data[0], username=user_data[1], password_hash=user_data[2])
            login_user(user)
            return redirect(url_for('admin'))
        else:
            flash('Невірне ім\'я користувача або пароль')
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/admin')
@login_required
def admin():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Get statistics
    c.execute("SELECT COUNT(*) FROM callback_requests WHERE status = 'new'")
    new_callbacks = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM service_requests WHERE status = 'new'")
    new_services = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM promotion_requests WHERE status = 'new'")
    new_promotions = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM reviews WHERE is_approved = FALSE")
    new_reviews = c.fetchone()[0]
    
    # Get recent requests
    c.execute("SELECT * FROM callback_requests ORDER BY created_at DESC LIMIT 5")
    recent_callbacks = c.fetchall()
    
    c.execute("SELECT * FROM service_requests ORDER BY created_at DESC LIMIT 5")
    recent_services = c.fetchall()
    
    conn.close()
    
    return render_template('admin.html',
                         new_callbacks=new_callbacks,
                         new_services=new_services,
                         new_promotions=new_promotions,
                         new_reviews=new_reviews,
                         recent_callbacks=recent_callbacks,
                         recent_services=recent_services)

@app.route('/admin/requests')
@login_required
def admin_requests():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    c.execute("SELECT * FROM callback_requests ORDER BY created_at DESC")
    callback_requests = c.fetchall()
    
    c.execute("SELECT * FROM service_requests ORDER BY created_at DESC")
    service_requests = c.fetchall()
    
    c.execute("SELECT * FROM promotion_requests ORDER BY created_at DESC")
    promotion_requests = c.fetchall()
    
    conn.close()
    
    return render_template('admin_requests.html',
                         callback_requests=callback_requests,
                         service_requests=service_requests,
                         promotion_requests=promotion_requests)

@app.route('/admin/request/update/<string:request_type>/<int:request_id>/<string:status>')
@login_required
def update_request_status(request_type, request_id, status):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if request_type == 'callback':
        c.execute("UPDATE callback_requests SET status = ? WHERE id = ?", (status, request_id))
    elif request_type == 'service':
        c.execute("UPDATE service_requests SET status = ? WHERE id = ?", (status, request_id))
    elif request_type == 'promotion':
        c.execute("UPDATE promotion_requests SET status = ? WHERE id = ?", (status, request_id))
    
    conn.commit()
    conn.close()
    
    flash('Статус заявки оновлено')
    return redirect(url_for('admin_requests'))

@app.route('/admin/reviews')
@login_required
def admin_reviews():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute("SELECT * FROM reviews ORDER BY created_at DESC")
    reviews = c.fetchall()
    conn.close()
    
    return render_template('admin_reviews.html', reviews=reviews)

@app.route('/admin/review/update/<int:review_id>/<string:action>')
@login_required
def update_review(review_id, action):
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    if action == 'approve':
        c.execute("UPDATE reviews SET is_approved = TRUE WHERE id = ?", (review_id,))
    elif action == 'reject':
        c.execute("DELETE FROM reviews WHERE id = ?", (review_id,))
    
    conn.commit()
    conn.close()
    
    flash('Відгук оновлено')
    return redirect(url_for('admin_reviews'))

# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize database
    init_db()
    
    print("Starting Flask application...")
    print("Telegram notifications enabled: ", bool(TELEGRAM_BOT_TOKEN and TELEGRAM_BOT_TOKEN != '7910995507:AAEoOR8OdaqkSFyWhr5mIFmGJ1wus-7fPUk'))
    
    # Start Flask application
    app.run(debug=True, host='0.0.0.0', port=5000)