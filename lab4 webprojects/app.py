import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from forms import RegistrationForm, LoginForm, CreateUserForm, EditUserForm, ChangePasswordForm
from models import User, Role
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import dbapi2 as sqlite
from extensions import db

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app) # Инициализация базы данных

# Проверка внешних ключей SQLlite
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


# Декоратор аутентификации(чтобы сохранить её на долгое время)
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get('logged_in') != True:
            return redirect(url_for('login', next=request.url))
        return f(*args, **kwargs)
    return decorated_function

# Загрузка пользователя перед сессией(из бд)
@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        try:
            g.user = db.session.get(User, session['user_id'])
        except Exception:
            g.user = None

# Шаблоны
@app.route('/')
def index():
    users = User.query.all()
    roles = {role.id: role.name for role in Role.query.all()} # показ ролей  и пользователей
    return render_template('index.html', users=users, roles=roles)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256') #хэширование пароля и добавляяет всё в бд
        new_user = User(
            username=form.username.data,
            password=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            middle_name=form.middle_name.data,
            role_id=form.role_id.data  # Получение форм
        )
        db.session.add(new_user)
        db.session.commit()
        flash('Спасибо за регистрацию!', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', form=form)


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User.query.filter_by(username=form.username.data).first()
        if user and check_password_hash(user.password, form.password.data): #Вход
            session['logged_in'] = True 
            session['user_id'] = user.id
            flash('Успешный вход!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    session.pop('logged_in', None)
    session.pop('user_id', None)
    flash('Вы вышли из системы!', 'info') #Выход из сессии
    return redirect(url_for('index'))


@app.route('/user/<int:user_id>')
def user_details(user_id):
    user = db.session.get(User, user_id)
    if user:
        return render_template('user_details.html', user=user) #Данные о пользователе
    else:
        flash('Пользователь не найден.', 'error')
        return redirect(url_for('index'))


@app.route('/user/create', methods=['GET', 'POST'])
@login_required
def create_user():
    form = CreateUserForm(request.form)
    form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]

    if request.method == 'POST' and form.validate():
        try:
            hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256') #Создание пользователя

            new_user = User(
                username=form.username.data,
                password=hashed_password,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                middle_name=form.middle_name.data,
                role_id=form.role_id.data if form.role_id.data else None,
                created_at=datetime.utcnow()
            )
            db.session.add(new_user)
            db.session.commit()
            flash('Пользователь успешно создан!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка создания пользователя: {e}', 'error')
            form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]

    return render_template('create_user.html', form=form)



@app.route('/user/edit/<int:user_id>', methods=['GET', 'POST']) #Редактирование
@login_required
def edit_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('Пользователь не найден.', 'error')
        return redirect(url_for('index'))
    form = EditUserForm(request.form, obj=user)
    form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]


    if request.method == 'POST' and form.validate():
        try:
            form.populate_obj(user) 
            db.session.commit()
            flash('Пользователь успешно обновлен!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Ошибка обновления пользователя: {e}', 'error')
            form.role_id.choices = [(role.id, role.name) for role in Role.query.all()]

    return render_template('edit_user.html', form=form, user=user)

@app.route('/user/delete/<int:user_id>', methods=['POST'])
@login_required
def delete_user(user_id):
    user = db.session.get(User, user_id)
    if not user:
        flash('Пользователь не найден.', 'error')      #Удаление пользователя
        return redirect(url_for('index'))

    try:
        db.session.delete(user)
        db.session.commit()
        flash('Пользователь успешно удален!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Ошибка удаления пользователя: {e}', 'error')

    return redirect(url_for('index'))

@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        user = g.user 
        if user and check_password_hash(user.password, form.old_password.data):
            hashed_password = generate_password_hash(form.new_password.data, method='pbkdf2:sha256') #Смена пароля
            user.password = hashed_password
            db.session.commit()
            flash('Пароль успешно изменен!', 'success')
            return redirect(url_for('index'))
        else:
            flash('Неверный старый пароль', 'error')
    return render_template('change_password.html', form=form)

# Обработка ошибок
@app.errorhandler(404)
def not_found(error):
    return render_template('404.html'), 404

# Инициализация бд(для первого раза)
@app.route('/initdb')
def initdb():
    """Initialize the database."""
    db.create_all()

    
    if Role.query.count() == 0:
        # Создание ролей
        admin_role = Role(name='Admin', description='Administrator')
        user_role = Role(name='User', description='Regular User')

        db.session.add(admin_role)
        db.session.add(user_role)
        db.session.commit()

        print("Default roles created.")

    return "Database initialized (if not already)."



if __name__ == '__main__':
    app.run() # Запустить приложение