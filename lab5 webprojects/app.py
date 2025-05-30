import os # Added import
from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_user, logout_user, login_required, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
from datetime import datetime
from forms import RegistrationForm, LoginForm, CreateUserForm, EditUserForm, ChangePasswordForm
from models import User, Role, VisitLog  
from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlite3 import dbapi2 as sqlite
from extensions import db
from reports import reports_bp, check_rights  

app = Flask(__name__)
app.config.from_object('config.Config')

db.init_app(app) 

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Работа с внешними ключами
@event.listens_for(Engine, "connect")
def _set_sqlite_pragma(dbapi_connection, connection_record):
    if isinstance(dbapi_connection, sqlite.Connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON;")
        cursor.close()


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id)) #Загрузка пользователя

@app.before_request
def log_visit():
    """Logs every visit to a page."""
    path = request.path
    user_id = current_user.is_authenticated and current_user.id or None
    visit_log = VisitLog(path=path, user_id=user_id)
    db.session.add(visit_log)
    db.session.commit()
    
# Шаблоны
@app.route('/')
def index():
    users = User.query.all()
    roles = {role.id: role.name for role in Role.query.all()} # Роли

    return render_template('index.html', users=users, roles=roles, current_user=current_user)

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        hashed_password = generate_password_hash(form.password.data, method='pbkdf2:sha256')          #Регистрация
        new_user = User(
            username=form.username.data,
            password=hashed_password,
            first_name=form.first_name.data,
            last_name=form.last_name.data,
            middle_name=form.middle_name.data,
            role_id=form.role_id.data  
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
        if user and check_password_hash(user.password, form.password.data):
            login_user(user)                                                          # Логин
            flash('Успешный вход!', 'success')
            next_url = request.args.get('next')
            return redirect(next_url or url_for('index'))
        else:
            flash('Неверное имя пользователя или пароль', 'error')
    return render_template('login.html', form=form)


@app.route('/logout')
@login_required
def logout():
    logout_user()                                                #Логаут
    flash('Вы вышли из системы!', 'info')
    return redirect(url_for('index'))


@app.route('/user/<int:user_id>')
def user_details(user_id):
    user = db.session.get(User, user_id)
    if user:
        return render_template('user_details.html', user=user)       #Профиль пользователя
    else:
        flash('Пользователь не найден.', 'error')
        return redirect(url_for('index'))


@app.route('/admin/users')
@login_required
@check_rights('Admin')
def user_list():
    users = User.query.all()
    return render_template('user_list.html', users=users)                #Список пользователей для админа

@app.route('/admin/user/create', methods=['GET', 'POST'])
@login_required
@check_rights('Admin')
def create_user():
    form = CreateUserForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, role=form.role.data)        #Создание пользователя(для админа)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('User created successfully!')
        return redirect(url_for('user_list'))
    return render_template('register.html', title='Create User', form=form)

@app.route('/admin/user/<int:user_id>/edit', methods=['GET', 'POST'])
@login_required
@check_rights('Admin')
def edit_user(user_id):
    user = User.query.get_or_404(user_id)
    form = AdminEditProfileForm(user.username, obj=user)
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data                                               #Редактирование пользователя(для админа)
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        user.role = form.role.data
        db.session.commit()
        flash('User updated successfully!')
        return redirect(url_for('user_list'))
    elif request.method == 'GET':
        form.username.data = user.username
        form.email.data = user.email
        form.first_name.data = user.first_name
        form.last_name.data = user.last_name
        form.role.data = user.role
    return render_template('user_edit.html', title='Edit User', form=form, user=user)

@app.route('/admin/user/<int:user_id>/delete')
@login_required
@check_rights('Admin')
def delete_user(user_id):
    user = User.query.get_or_404(user_id)                            #Удаление пользователя(для админа)
    db.session.delete(user)
    db.session.commit()
    flash('User deleted successfully!')
    return redirect(url_for('user_list'))


@app.route('/visit_logs')
@login_required
def visit_logs():
    page = request.args.get('page', 1, type=int)
    visits = VisitLog.query.filter_by(user_id=current_user.id).order_by(VisitLog.created_at.desc()).paginate(            #Список посещения
        page=page, per_page=app.config['ITEMS_PER_PAGE'])

    return render_template('visit_logs.html', visits=visits)


@app.route('/change_password', methods=['GET', 'POST'])
@login_required
def change_password():
    form = ChangePasswordForm(request.form)
    if request.method == 'POST' and form.validate():
        user = current_user # access user from flask-login
        if user and check_password_hash(user.password, form.old_password.data):
            hashed_password = generate_password_hash(form.new_password.data, method='pbkdf2:sha256')          #Смена пароля
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

# Инициализация бд для первого запуска
@app.route('/initdb')
def initdb():
    """Initialize the database."""
    db.create_all()

    
    if Role.query.count() == 0:
        
        admin_role = Role(name='Admin', description='Administrator')
        user_role = Role(name='User', description='Regular User')

        db.session.add(admin_role)
        db.session.add(user_role)
        db.session.commit()

        print("Default roles created.")

    return "Database initialized (if not already)."

app.register_blueprint(reports_bp)  # Register the Blueprint HERE


if __name__ == '__main__':
    app.run() # Запустить приложение