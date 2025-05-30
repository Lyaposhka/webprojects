from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, EqualTo, Regexp, ValidationError
from models import User, Role  # Import Role

def validate_username(form, field):
    """
    Проверяет, что имя пользователя уникально.
    """
    existing_user = User.query.filter_by(username=field.data).first()
    if existing_user:
        raise ValidationError('Это имя пользователя уже занято. Пожалуйста, выберите другое.')


class RegistrationForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=5, max=20), Regexp(r'^[a-zA-Z0-9_]+$', message="Имя пользователя должно содержать только буквы, цифры и подчеркивания."), validate_username])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8, max=128)])
    confirm_password = PasswordField('Подтвердите пароль', validators=[DataRequired(), EqualTo('password', message="Пароли должны совпадать")])
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int, choices=[(1, 'Admin'), (2, 'User')]) # Add role field
    submit = SubmitField('Зарегистрироваться')

class LoginForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired()])
    password = PasswordField('Пароль', validators=[DataRequired()])
    remember_me = BooleanField('Запомнить меня')
    submit = SubmitField('Войти')

class CreateUserForm(FlaskForm):
    username = StringField('Имя пользователя', validators=[DataRequired(), Length(min=5, max=20), Regexp(r'^[a-zA-Z0-9_]+$', message="Имя пользователя должно содержать только буквы, цифры и подчеркивания."), validate_username])
    password = PasswordField('Пароль', validators=[DataRequired(), Length(min=8, max=128)])
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int, choices=[])
    submit = SubmitField('Создать пользователя')

class EditUserForm(FlaskForm):
    first_name = StringField('Имя', validators=[DataRequired()])
    last_name = StringField('Фамилия', validators=[DataRequired()])
    middle_name = StringField('Отчество')
    role_id = SelectField('Роль', coerce=int, choices=[])
    submit = SubmitField('Обновить пользователя')


def password_complexity(form, field):
    password = field.data
    if len(password) < 8:
        raise ValidationError("Пароль должен содержать не менее 8 символов.")
    if len(password) > 128:
        raise ValidationError("Пароль должен содержать не более 128 символов.")
    if not any(char.isupper() for char in password):
        raise ValidationError("Пароль должен содержать хотя бы одну заглавную букву.")
    if not any(char.islower() for char in password):
        raise ValidationError("Пароль должен содержать хотя бы одну строчную букву.")
    if not any(char.isdigit() for char in password):
        raise ValidationError("Пароль должен содержать хотя бы одну цифру.")
    if any(char.isspace() for char in password):
        raise ValidationError("Пароль не должен содержать пробелы.")
    # Extended character check
    allowed_chars = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZабвгдеёжзийклмнопрстуфхцчшщъыьэюяАБВГДЕЁЖЗИЙКЛМНОПРСТУФХЦЧШЩЪЫЬЭЮЯ0123456789~!@#$%^&*()_+=-`[]\{}|;':\",./<>?"
    if not all(char in allowed_chars for char in password):
        raise ValidationError("Пароль содержит недопустимые символы. Разрешенные символы: латинские/кириллические буквы, цифры и ~!@#$%^&*()_+=-`[]\{}|;':\",./<>?")


class ChangePasswordForm(FlaskForm):
    old_password = PasswordField('Старый пароль', validators=[DataRequired()])
    new_password = PasswordField('Новый пароль', validators=[DataRequired(), password_complexity])
    confirm_new_password = PasswordField('Подтвердите новый пароль', validators=[DataRequired(), EqualTo('new_password', message='Пароли должны совпадать')])
    submit = SubmitField('Сменить пароль')