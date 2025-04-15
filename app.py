import os
import json
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from functools import wraps
from database import (get_user, add_user, update_user_tariff, add_feedback,
                      update_module_progress, get_module_progress,
                      add_homework_submission, get_homework_submissions,
                      get_db_connection)
from modules_content import MODULES, MODULE_DESCRIPTIONS, HOMEWORK, ADDITIONAL_MATERIALS
import sqlite3
from config import ACCESS_CODES


# Функция для сохранения кодов доступа в config.py
def save_access_codes(access_codes):
    config_path = 'config.py'
    with open(config_path, 'r', encoding='utf-8') as file:
        config_content = file.read()

    # Найдем блок с ACCESS_CODES и заменим его
    import re
    pattern = r'ACCESS_CODES = \{[^}]*\}'
    replacement = f'ACCESS_CODES = {json.dumps(access_codes, indent=4, ensure_ascii=False)}'
    new_content = re.sub(pattern, replacement, config_content)

    with open(config_path, 'w', encoding='utf-8') as file:
        file.write(new_content)


# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "development_secret_key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure database
app.config["SQLALCHEMY_DATABASE_URI"] = 'sqlite:///course_bot.db'
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Simple admin auth
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "password")


# Admin routes
@app.route('/')
def index():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('index.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    flash('Вы вышли из системы', 'info')
    return redirect(url_for('login'))


@app.route('/users')
def users():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users ORDER BY registration_date DESC")
        users = cursor.fetchall()

    return render_template('users.html', users=users)


@app.route('/user/<int:user_id>')
def user_detail(user_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        # Get user details
        cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id, ))
        user = cursor.fetchone()

        # Get module progress
        cursor.execute(
            "SELECT module_id, completed, completion_date FROM module_progress WHERE user_id = ?",
            (user_id, ))
        progress = cursor.fetchall()

        # Get homework submissions
        cursor.execute(
            "SELECT * FROM homework_submissions WHERE user_id = ? ORDER BY submitted_date DESC",
            (user_id, ))
        submissions = cursor.fetchall()

        # Get feedback
        cursor.execute(
            "SELECT * FROM feedback WHERE user_id = ? ORDER BY sent_date DESC",
            (user_id, ))
        feedback = cursor.fetchall()

    if not user:
        flash('Пользователь не найден', 'danger')
        return redirect(url_for('users'))

    return render_template('user_detail.html',
                           user=user,
                           progress=progress,
                           submissions=submissions,
                           feedback=feedback,
                           modules=MODULES)


@app.route('/modules')
def modules():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    return render_template('modules.html',
                           modules=MODULES,
                           descriptions=MODULE_DESCRIPTIONS)


@app.route('/module/<int:module_id>')
def module_detail(module_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if module_id not in MODULES:
        flash('Модуль не найден', 'danger')
        return redirect(url_for('modules'))

    module_title = MODULES[module_id]
    module_description = MODULE_DESCRIPTIONS.get(module_id,
                                                 "Описание отсутствует")
    homework = HOMEWORK.get(module_id, "Домашнее задание отсутствует")
    materials = ADDITIONAL_MATERIALS.get(module_id, [])

    return render_template('module_detail.html',
                           module_id=module_id,
                           title=module_title,
                           description=module_description,
                           homework=homework,
                           materials=materials)


@app.route('/feedback')
def feedback_list():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT f.*, u.username, u.first_name, u.last_name 
            FROM feedback f
            JOIN users u ON f.user_id = u.user_id
            ORDER BY f.sent_date DESC
        """)
        feedback = cursor.fetchall()

    return render_template('feedback.html', feedback=feedback)


@app.route('/submissions')
def submissions():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT s.*, u.username, u.first_name, u.last_name 
            FROM homework_submissions s
            JOIN users u ON s.user_id = u.user_id
            ORDER BY s.submitted_date DESC
        """)
        submissions = cursor.fetchall()

    return render_template('submissions.html',
                           submissions=submissions,
                           modules=MODULES)


@app.route('/submission/<int:submission_id>', methods=['GET', 'POST'])
def submission_detail(submission_id):
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        feedback = request.form.get('feedback')

        with get_db_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE homework_submissions SET feedback = ? WHERE id = ?",
                (feedback, submission_id))
            conn.commit()

        flash('Отзыв успешно сохранен', 'success')
        return redirect(
            url_for('submission_detail', submission_id=submission_id))

    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT s.*, u.username, u.first_name, u.last_name 
            FROM homework_submissions s
            JOIN users u ON s.user_id = u.user_id
            WHERE s.id = ?
        """, (submission_id, ))
        submission = cursor.fetchone()

    if not submission:
        flash('Запись не найдена', 'danger')
        return redirect(url_for('submissions'))

    module_id = submission[2]  # Index 2 corresponds to module_id
    module_name = MODULES.get(module_id, f"Модуль {module_id}")
    homework = HOMEWORK.get(module_id, "Домашнее задание отсутствует")

    return render_template('submission_detail.html',
                           submission=submission,
                           module_name=module_name,
                           homework=homework)


@app.route('/access_codes')
def access_codes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    return render_template('access_codes.html', access_codes=ACCESS_CODES)


@app.route('/add_access_code', methods=['POST'])
def add_access_code():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    code = request.form.get('code')
    tariff = request.form.get('tariff')

    if not code or not tariff:
        flash('Необходимо указать код и тариф', 'danger')
        return redirect(url_for('access_codes'))

    if tariff not in ACCESS_CODES:
        flash('Указан неверный тариф', 'danger')
        return redirect(url_for('access_codes'))

    # Проверяем, не существует ли уже такой код
    for t, codes in ACCESS_CODES.items():
        if code in codes:
            flash(f'Код уже существует для тарифа {t}', 'danger')
            return redirect(url_for('access_codes'))

    # Добавляем код
    current_codes = list(ACCESS_CODES[tariff])
    current_codes.append(code)
    ACCESS_CODES[tariff] = current_codes

    # Сохраняем изменения в config.py
    try:
        save_access_codes(ACCESS_CODES)
        flash('Код доступа успешно добавлен', 'success')
    except Exception as e:
        flash(f'Ошибка при сохранении кода: {str(e)}', 'danger')

    return redirect(url_for('access_codes'))


@app.route('/delete_access_code', methods=['POST'])
def delete_access_code():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    code = request.form.get('code')
    tariff = request.form.get('tariff')

    if not code or not tariff:
        flash('Необходимо указать код и тариф', 'danger')
        return redirect(url_for('access_codes'))

    if tariff not in ACCESS_CODES or code not in ACCESS_CODES[tariff]:
        flash('Указан неверный код или тариф', 'danger')
        return redirect(url_for('access_codes'))

    # Удаляем код
    current_codes = list(ACCESS_CODES[tariff])
    current_codes.remove(code)
    ACCESS_CODES[tariff] = current_codes

    # Сохраняем изменения в config.py
    try:
        save_access_codes(ACCESS_CODES)
        flash('Код доступа успешно удален', 'success')
    except Exception as e:
        flash(f'Ошибка при удалении кода: {str(e)}', 'danger')

    return redirect(url_for('access_codes'))


# =================================================================
# API для мини-приложения Telegram
# =================================================================


def get_token_from_header():
    """Получает токен из заголовка Authorization"""
    auth_header = request.headers.get('Authorization')
    if auth_header and auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


def api_auth_required(f):
    """Декоратор для проверки авторизации API запросов"""

    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = request.args.get('user_id')

        if not user_id:
            return jsonify({'error': 'User ID is required'}), 401

        # Проверяем, существует ли пользователь
        user = get_user(int(user_id))
        if not user:
            return jsonify({'error': 'User not found'}), 404

        return f(*args, **kwargs)

    return decorated


@app.route('/api/mini-app/user-data')
@api_auth_required
def api_user_data():
    """Возвращает данные пользователя для мини-приложения"""
    user_id = int(request.args.get('user_id'))
    user = get_user(user_id)

    # Получаем данные о прогрессе пользователя
    progress = get_module_progress(user_id)

    # Определяем тариф и доступные модули
    from config import MODULE_ACCESS
    tariff = user[4]
    available_modules = MODULE_ACCESS.get(tariff.lower(), [])

    # Конвертируем прогресс в более удобный формат
    completed_modules = [
        module_id for module_id, completed in progress if completed
    ]
    progress_data = []

    for module_id in available_modules:
        module_name = MODULES.get(module_id, f"Модуль {module_id}")
        is_completed = module_id in completed_modules
        progress_data.append({
            'module_id': module_id,
            'name': module_name,
            'completed': is_completed
        })

    # Рассчитываем общий прогресс в процентах
    completed_percentage = 0
    if available_modules:
        completed_percentage = round(
            (len(completed_modules) / len(available_modules)) * 100)

    # Получаем данные о выполненных домашних заданиях
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT module_id, COUNT(*) FROM homework_submissions WHERE user_id = ? GROUP BY module_id",
            (user_id, ))
        submissions_count = dict(cursor.fetchall())

    homework_data = []
    for module_id in available_modules:
        homework_data.append({
            'module_id':
            module_id,
            'name':
            f"Модуль {module_id}",
            'submissions_count':
            submissions_count.get(module_id, 0)
        })

    return jsonify({
        'user': {
            'user_id': user[0],
            'username': user[1],
            'first_name': user[2],
            'last_name': user[3],
            'tariff': tariff
        },
        'progress': {
            'percentage': completed_percentage,
            'modules': progress_data
        },
        'homework': homework_data
    })


@app.route('/mini-app')
def mini_app():
    """Страница мини-приложения для Telegram"""
    # В URL должен быть параметр user_id
    user_id = request.args.get('user_id')
    if not user_id:
        return "Требуется идентификатор пользователя", 400

    # Проверяем, существует ли пользователь
    user = get_user(int(user_id))
    if not user:
        return "Пользователь не найден", 404

    return render_template('mini_app.html', user_id=user_id)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
from flask import request  # добавь к остальным импортам

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Замени эти данные на свои
        ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
        ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'adminpass')

        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Неверное имя пользователя или пароль', 'danger')

    return render_template('login.html')
@app.route('/codes')
def codes():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    from config import ACCESS_CODES
    return render_template('codes.html', codes=ACCESS_CODES)
