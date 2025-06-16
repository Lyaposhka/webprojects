from datetime import datetime
from werkzeug.security import generate_password_hash
from models import db, User, Role, Equipment, Category, Photo, Disposal
from app import app
import os
import hashlib

def md5_file(path):
    with open(path, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

with app.app_context():
    db.drop_all()
    db.create_all()

    # Роли и пользователи
    admin = User(login='admin', password_hash=generate_password_hash('admin'))
    mod = User(login='moderator', password_hash=generate_password_hash('moderator'))
    user = User(login='user', password_hash=generate_password_hash('user'))

    role_admin = Role(name='admin')
    role_mod = Role(name='moderator')
    role_user = Role(name='user')

    admin.roles.append(role_admin)
    mod.roles.append(role_mod)
    user.roles.append(role_user)

    db.session.add_all([admin, mod, user, role_admin, role_mod, role_user])

    # Категории
    cat1 = Category(name='Принтеры', description='Лазерные и струйные принтеры')
    cat2 = Category(name='Компьютеры', description='Настольные ПК и ноутбуки')
    cat3 = Category(name='Сканеры', description='Планшетные и ручные сканеры')
    cat4 = Category(name='МФУ', description='Многофункциональные устройства')
    cat5 = Category(name='Мониторы', description='ЖК и LED мониторы')
    db.session.add_all([cat1, cat2, cat3, cat4, cat5])
    db.session.commit()

    # Оборудование
    devices = [
        ("HP LaserJet", "INV001", cat1, "2021-05-01", 15000, "active", "Рабочий принтер", "example1.jpg"),
        ("Lenovo ThinkPad", "INV002", cat2, "2022-08-20", 85000, "active", "Ноутбук", "example2.jpg"),
        ("Старый сканер", "INV003", cat3, "2015-04-12", 5000, "disposed", "Не работает", "disposed1.jpg"),
        ("Samsung Xpress", "INV004", cat1, "2020-02-10", 12000, "active", "Новый принтер", "example3.jpg"),
        ("Acer Aspire", "INV005", cat2, "2021-10-05", 62000, "active", "Быстрый ноутбук", "example4.jpg"),
        ("HP Laser MFP", "INV006", cat4, "2023-01-18", 19000, "repair", "Периодически заедает", "example5.jpg"),
        ("LG Monitor", "INV007", cat5, "2019-07-12", 9500, "active", "Монитор 24 дюйма", "example6.jpg"),
    ]

    for name, inv, cat, date_str, price, status, note, img in devices:
        eq = Equipment(
            name=name,
            inventory_number=inv,
            category=cat,
            purchase_date=datetime.strptime(date_str, "%Y-%m-%d"),
            price=price,
            status=status,
            note=note
        )
        db.session.add(eq)
        db.session.flush()

        # Добавляем фото
        photo_path = os.path.join(app.static_folder, 'photos', img)
        if os.path.exists(photo_path):
            photo = Photo(
                filename=img,
                mime_type='image/jpeg',
                md5_hash=md5_file(photo_path),
                equipment_id=eq.id
            )
            db.session.add(photo)

    # Добавим PDF акт для списанного
    pdf_path = os.path.join(app.static_folder, 'pdfs', 'example.pdf')
    if os.path.exists(pdf_path):
        disposal = Disposal(
            equipment_id=3,
            reason="Неисправность и моральный износ",
            pdf_filename="example.pdf"
        )
        db.session.add(disposal)

    db.session.commit()
