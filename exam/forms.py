from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, SubmitField, TextAreaField,
    DecimalField, SelectField, FileField, BooleanField, DateField
)
from wtforms.validators import DataRequired, Length, Optional, NumberRange
from flask_wtf.file import FileAllowed

class LoginForm(FlaskForm):
    username = StringField('Логин', validators=[DataRequired(), Length(max=64)])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class EquipmentForm(FlaskForm):
    name = StringField('Название оборудования', validators=[DataRequired(), Length(max=128)])
    inventory_number = StringField('Инвентарный номер', validators=[DataRequired(), Length(max=64)])
    category = SelectField('Категория', coerce=int, validators=[DataRequired()])
    purchase_date = DateField('Дата покупки', format='%Y-%m-%d', validators=[DataRequired()])
    price = DecimalField('Стоимость', places=2, validators=[DataRequired(), NumberRange(min=0)])
    status = SelectField('Статус', choices=[
        ('В эксплуатации', 'В эксплуатации'),
        ('На ремонте', 'На ремонте'),
        ('Списано', 'Списано')
    ], validators=[DataRequired()])
    note = TextAreaField('Примечание', validators=[Optional()])
    photo = FileField('Фотография', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png'], 'Только изображения (.jpg, .jpeg, .png)')
    ])
    submit = SubmitField('Сохранить')

class MaintenanceForm(FlaskForm):
    type = StringField('Тип обслуживания', validators=[DataRequired(), Length(max=128)])
    comment = TextAreaField('Комментарий', validators=[Optional()])
    date = DateField('Дата обслуживания', format='%Y-%m-%d', validators=[DataRequired()])
    submit = SubmitField('Добавить запись')

class DisposalForm(FlaskForm):
    reason = TextAreaField('Причина списания', validators=[DataRequired()])
    act = FileField('Акт списания (PDF)', validators=[
        DataRequired(),
        FileAllowed(['pdf'], 'Только PDF-файлы')
    ])
    submit = SubmitField('Списать оборудование')
