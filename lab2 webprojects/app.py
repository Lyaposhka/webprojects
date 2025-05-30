from flask import Flask, request, render_template, redirect, url_for
import re

app = Flask(__name__)

def validate_phone_number(phone):
    cleaned_phone = re.sub(r'[^\d+]', '', phone)  # Удаляем все ненужные символы
    
    if not re.fullmatch(r'[\d+()\s.-]+', phone):
        return "Недопустимый ввод. В номере телефона встречаются недопустимые символы."
    
    digits = re.sub(r'\D', '', cleaned_phone)  # Оставляем только цифры
    
    if (digits.startswith("8") or digits.startswith("7")) and len(digits) != 11:
        return "Недопустимый ввод. Неверное количество цифр."
    elif not digits.startswith("8") and not digits.startswith("7") and len(digits) != 10:
        return "Недопустимый ввод. Неверное количество цифр."
    
    return None

def format_phone_number(phone):
    digits = re.sub(r'\D', '', phone)
    return f"8-{digits[1:4]}-{digits[4:7]}-{digits[7:9]}-{digits[9:11]}" if len(digits) == 11 else f"{digits[:3]}-{digits[3:6]}-{digits[6:8]}-{digits[8:]}" #Преобразование в нужный формат

@app.route('/')
def index():
    return render_template('index.html') #Шаблон

@app.route('/request-info')
def request_info():
    return render_template('request_info.html', request=request) #загрузка request'ов

@app.route('/phone-form', methods=['GET', 'POST'])
def phone_form():
    error = None
    formatted_phone = None
    
    if request.method == 'POST':
        phone = request.form.get('phone')
        error = validate_phone_number(phone)
        if not error:
            formatted_phone = format_phone_number(phone) #Если нет проблем в полученном номере--переводим номер в нужный формат
    
    return render_template('phone_form.html', error=error, formatted_phone=formatted_phone) #показ номера

if __name__ == '__main__':
    app.run(debug=True)
