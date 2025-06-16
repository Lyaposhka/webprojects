from flask import Flask, render_template, redirect, url_for, flash, request, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Role, Equipment, Category, Photo, Disposal, Maintenance
import os
from datetime import datetime
import hashlib

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///library.db'
app.config['UPLOAD_FOLDER'] = 'static/photos'
app.config['PDF_FOLDER'] = 'static/pdfs'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['PDF_FOLDER'], exist_ok=True)

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

def md5_file(file):
    return hashlib.md5(file.read()).hexdigest()

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def require_role(role_name):
    if not current_user.is_authenticated or not current_user.has_role(role_name):
        flash('У вас недостаточно прав для выполнения данного действия.')
        return redirect(url_for('index'))

@app.route('/')
def index():
    query = Equipment.query.filter(Equipment.status != 'disposed').order_by(Equipment.purchase_date.desc())
    category = request.args.get('category')
    status = request.args.get('status')
    if category:
        query = query.join(Category).filter(Category.name == category)
    if status:
        query = query.filter(Equipment.status == status)
    page = request.args.get('page', 1, type=int)
    equipment = query.paginate(page=page, per_page=10)
    return render_template('index.html', equipment=equipment)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(login=request.form['login']).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Невозможно аутентифицироваться с указанными логином и паролем')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/equipment/<int:id>')
def view_equipment(id):
    eq = Equipment.query.get_or_404(id)
    return render_template('view_equipment.html', eq=eq)

@app.route('/add', methods=['GET', 'POST'])
@login_required
def add_equipment():
    if not current_user.has_role('admin'):
        return require_role('admin')
    categories = Category.query.all()
    if request.method == 'POST':
        try:
            eq = Equipment(
                name=request.form['name'],
                inventory_number=request.form['inventory_number'],
                category_id=request.form['category_id'],
                purchase_date=datetime.strptime(request.form['purchase_date'], '%Y-%m-%d'),
                price=float(request.form['price']),
                status=request.form['status'],
                note=request.form['note']
            )
            db.session.add(eq)
            db.session.flush()

            file = request.files['photo']
            md5 = hashlib.md5(file.read()).hexdigest()
            file.seek(0)
            existing = Photo.query.filter_by(md5_hash=md5).first()
            if not existing:
                ext = os.path.splitext(secure_filename(file.filename))[1]
                filename = f'{eq.id}{ext}'
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                file.save(filepath)
                photo = Photo(
                    filename=filename,
                    mime_type=file.mimetype,
                    md5_hash=md5,
                    equipment_id=eq.id
                )
                db.session.add(photo)
            db.session.commit()
            return redirect(url_for('index'))
        except Exception:
            db.session.rollback()
            flash('При сохранении данных возникла ошибка. Проверьте корректность введённых данных.')
    return render_template('add_equipment.html', categories=categories)

@app.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_equipment(id):
    if not current_user.has_role('admin'):
        return require_role('admin')
    eq = Equipment.query.get_or_404(id)
    try:
        if eq.photo:
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], eq.photo.filename))
        db.session.delete(eq)
        db.session.commit()
        flash('Оборудование удалено.')
    except Exception:
        db.session.rollback()
        flash('Ошибка удаления.')
    return redirect(url_for('index'))

@app.route('/dispose/<int:id>', methods=['GET', 'POST'])
@login_required
def dispose_equipment(id):
    if not current_user.has_role('admin'):
        return require_role('admin')
    eq = Equipment.query.get_or_404(id)
    if request.method == 'POST':
        reason = request.form['reason']
        pdf = request.files['pdf']
        filename = f"{eq.id}_{secure_filename(pdf.filename)}"
        pdf.save(os.path.join(app.config['PDF_FOLDER'], filename))
        eq.status = 'disposed'
        disposal = Disposal(
            equipment_id=eq.id,
            reason=reason,
            pdf_filename=filename
        )
        db.session.add(disposal)
        db.session.commit()
        return redirect(url_for('index'))
    return render_template('dispose_equipment.html', equipment=eq)

@app.route('/repair/<int:id>', methods=['POST'])
@login_required
def mark_repair(id):
    if not (current_user.has_role('moderator') or current_user.has_role('admin')):
        return require_role('moderator')
    eq = Equipment.query.get_or_404(id)
    eq.status = 'repair'
    db.session.commit()
    return redirect(url_for('index'))

@app.route('/change_status/<int:id>', methods=['POST'])
@login_required
def change_status(id):
    if not current_user.has_role('admin'):
        return require_role('admin')
    eq = Equipment.query.get_or_404(id)
    new_status = request.form.get('status')
    if new_status in ['active', 'repair', 'disposed']:
        eq.status = new_status
        db.session.commit()
        flash('Статус изменён.')
    else:
        flash('Недопустимый статус.')
    return redirect(url_for('view_equipment', id=id))

@app.route('/maintenance/<int:id>', methods=['POST'])
@login_required
def add_maintenance(id):
    if not (current_user.has_role('moderator') or current_user.has_role('admin')):
        return require_role('moderator')
    comment = request.form['comment']
    maint = Maintenance(equipment_id=id, comment=comment, type='тех. обслуживание')
    db.session.add(maint)
    db.session.commit()
    return redirect(url_for('view_equipment', id=id))

@app.route('/disposed')
@login_required
def disposed():
    eq = Equipment.query.filter_by(status='disposed').all()
    return render_template('disposed.html', equipment=eq)

@app.route('/download/<filename>')
@login_required
def download_pdf(filename):
    return send_from_directory(app.config['PDF_FOLDER'], filename)

@app.route('/initdb')
def initdb():
    db.drop_all()
    db.create_all()
    admin = User(login='admin', password_hash=generate_password_hash('admin'))
    mod = User(login='moderator', password_hash=generate_password_hash('moderator'))
    user = User(login='user', password_hash=generate_password_hash('user'))
    r1 = Role(name='admin')
    r2 = Role(name='moderator')
    r3 = Role(name='user')
    admin.roles.append(r1)
    mod.roles.append(r2)
    user.roles.append(r3)
    c1 = Category(name='Принтеры', description='Лазерные и струйные')
    c2 = Category(name='Компьютеры', description='ПК и ноутбуки')
    db.session.add_all([r1, r2, r3, admin, mod, user, c1, c2])
    db.session.commit()
    return 'База инициализирована.'

if __name__ == '__main__':
    app.run(debug=True)
