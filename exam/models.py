from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

# ——— роли и пользователи ———

roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer, db.ForeignKey('user.id', ondelete='CASCADE')),
    db.Column('role_id', db.Integer, db.ForeignKey('role.id', ondelete='CASCADE'))
)

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True)

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    login = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    roles = db.relationship('Role', secondary=roles_users, backref=db.backref('users', lazy='dynamic'))

    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)

# ——— категории ———

class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True, nullable=False)
    description = db.Column(db.Text)

# ——— оборудование ———

class Equipment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    inventory_number = db.Column(db.String(64), unique=True, nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id', ondelete='SET NULL'))
    purchase_date = db.Column(db.Date)
    price = db.Column(db.Float)
    status = db.Column(db.String(20), nullable=False, default='active')  # active / repair / disposed
    note = db.Column(db.Text)

    category = db.relationship('Category', backref=db.backref('equipments', lazy=True))
    photo = db.relationship('Photo', backref='equipment', uselist=False, cascade="all, delete", passive_deletes=True)
    maintenances = db.relationship('Maintenance', backref='equipment', cascade="all, delete", passive_deletes=True)
    disposal = db.relationship('Disposal', backref='equipment', uselist=False, cascade="all, delete", passive_deletes=True)

# ——— фото ———

class Photo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(128), nullable=False)
    mime_type = db.Column(db.String(64), nullable=False)
    md5_hash = db.Column(db.String(64), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'))

# ——— обслуживание ———

class Maintenance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'))
    date = db.Column(db.Date, default=datetime.utcnow)
    type = db.Column(db.String(64))
    comment = db.Column(db.Text)

# ——— списание ———

class Disposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipment.id', ondelete='CASCADE'))
    reason = db.Column(db.Text)
    date = db.Column(db.DateTime, default=datetime.utcnow)
    pdf_filename = db.Column(db.String(128))
