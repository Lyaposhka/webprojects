from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

app = Flask(__name__)
app.secret_key = 'supersecretkeywhichevenicantremember'  # Ключ для хранения сессии

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login' 

class User(UserMixin):
    def __init__(self, id, username, password): #Параметры для аутентификации
        self.id = id
        self.username = username
        self.password = password 

users = {"user": User(id=1, username="user", password="qwerty")} #Пользователь и пароль

@login_manager.user_loader
def load_user(user_id):
    for user in users.values():
        if str(user.id) == user_id: #загрузка пользователя сессии
            return user
    return None

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/counter')
def counter():
    session['visits'] = session.get('visits', 0) + 1
    return render_template('counter.html', visits=session['visits']) #Счётчик посещений

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        remember = 'remember' in request.form    #Запоминание
        user = users.get(username)
        if user and user.password == password:
            login_user(user, remember=remember)
            flash('Вы успешно вошли!', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('index'))    ##ФОРМА ВХОДА
        flash('Неверные учетные данные', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Вы вышли из системы', 'info') #Логаут
    return redirect(url_for('index'))

@app.route('/secret')
@login_required
def secret():
    return render_template('secret.html') #Секретная страница

if __name__ == '__main__':
    app.run(debug=True)
