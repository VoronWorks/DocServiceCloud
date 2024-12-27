from flask import Flask, render_template, redirect, url_for, request, jsonify, flash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
from flask import Flask, request, render_template, redirect, url_for, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from docx import Document
import os
import requests
import uuid

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'


db_service = 'http://localhost:5001/'
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password



def get_user(user):
    return User(user['id'], user['username'], user['password'])

@login_manager.user_loader
def load_user(user_id):
    response = requests.get(f'{db_service}user?id={user_id}')
    if response.status_code == 200:
        user = response.json()
        return get_user(user)
    return None

# @app.route('/login', methods=['GET', 'POST'])
# def login():
#     if request.method == 'POST':
#         username = request.form['username']
#         password = request.form['password']
#         user = users.get(username)
#         if user and user.password == password:
#             login_user(user)
#             return redirect(url_for('index'))
#         flash('Invalid credentials', 'danger')
#     return render_template('login.html')




@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        # Хэшируем пароль
        hashed_password = generate_password_hash(password)

        # Отправляем данные в базу
        response = requests.post(f'{db_service}users', json={
            'username': username,
            'password': hashed_password
        })

        if response.status_code == 201:
            login_user(get_user(response.json()))
            return redirect(url_for('login'))
        else:
            return 'User already exists or registration failed', 400

    return render_template('login.html', flag=1)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        # Проверяем данные
        response = requests.get(f'{db_service}users?username={username}')
        if response.status_code == 200:
            user = response.json()
            print(user)
            # print(check_password_hash(user['password'], password))
            if check_password_hash(user['password'], password):
                login_user(get_user(user))
                return redirect(url_for('index'))
            flash('Invalid credentials', 'danger')
    return render_template('login.html', flag=0)

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))
@app.route('/')
@login_required
def index():
    response = requests.get(f'{db_service}documents/{session["user_id"]}')
    documents = response.json() if response.status_code == 200 else []
    return render_template('index.html', documents=documents)


@app.route('/edit', methods=['GET'])
@app.route('/edit/<int:document_id>', methods=['GET'])
@login_required
def edit(document_id=None):
    document = None
    if document_id:
        response = requests.get(f'{db_service}documents/{document_id}', json={'user_id': session["user_id"]})
        if response.status_code == 200:
            document = response.json()
    return render_template('edit.html', document=document)


@app.route('/save', methods=['POST'])
@login_required
def save_document():
    data = request.form  # Request.form for file uploads
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    if file:
        filename = secure_filename(file.filename)
        unique_filename = str(uuid.uuid4()) + "_" + filename
        
        if 'id' in data:
            pass  
        
        else:  

             file.save(os.path.join('uploads', unique_filename)) #Saves to uploads folder
             response = requests.post(f'{db_service}documents', json={'user_id': session["user_id"], 'title': data['title'], 'file_path': unique_filename})
    return jsonify({'success': response.status_code in [200, 201]})




@app.route('/delete/<int:document_id>', methods=['DELETE'])
@login_required
def delete_document(document_id):
    response = requests.delete(f'{db_service}documents/{document_id}', json={'user_id': session["user_id"]})
    return jsonify({'success': response.status_code == 200})


if __name__ == '__main__':
    app.run(port=443, debug=False, ssl_context=('cert.pem', 'key.pem')) 