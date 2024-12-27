from flask import Flask, request, jsonify, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from werkzeug.utils import secure_filename
from docx import Document
import os
import uuid

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///123.db'  
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  
    documents = db.relationship('Document', backref='user', lazy=True)

class Document(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    file_path = db.Column(db.String(200), nullable=False) 


@app.route('/documents/<int:document_id>', methods=['GET'])
def get_document(document_id):
    data = request.json
    document = Document.query.filter_by(id=document_id, user_id=data['user_id']).first()
    if document:
        return jsonify({"id": document.id, "title": document.title, "file_path": document.file_path})
    return jsonify({"message": "Document not found"}), 404

@app.route('/documents/<int:user_id>', methods=['GET'])
def get_documents(user_id):
    documents = Document.query.filter_by(user_id=user_id).all()
    return jsonify([{"id": d.id, "title": d.title, "file_path": d.file_path} for d in documents])

@app.route('/documents', methods=['POST'])
def add_document():
    data = request.json
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file:
        filename = secure_filename(file.filename)
        # Generate a unique filename to prevent overwrites
        unique_filename = str(uuid.uuid4()) + "_" + filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
        file.save(file_path)

        new_document = Document(user_id=data['user_id'], title=data['title'], file_path=unique_filename)
        db.session.add(new_document)
        db.session.commit()
        return jsonify({"message": "Document uploaded successfully", "file_path": unique_filename}), 201
    return jsonify({'error': 'Upload failed'}), 500


@app.route('/documents/<int:document_id>', methods=['PUT'])
def update_document(document_id): 
    pass  

@app.route('/documents/<int:document_id>', methods=['DELETE'])
def delete_document(document_id):
    data = request.json
    document = Document.query.filter_by(id=document_id, user_id=data['user_id']).first()
    if document:
        os.remove(os.path.join(app.config['UPLOAD_FOLDER'], document.file_path)) 
        db.session.delete(document)
        db.session.commit()
        return jsonify({'success': True}), 200
    return jsonify({'error': 'Document not found or unauthorized'}), 404

@app.route('/uploads/<path:filename>', methods=['GET'])
def download_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename, as_attachment=True)


@app.route('/users', methods=['POST'])
def create_user():
    data = request.json
    if User.query.filter_by(username=data['username']).first():
        return jsonify({'error': 'User already exists'}), 400

    new_user = User(username=data['username'], password=data['password'])
    db.session.add(new_user)
    db.session.commit()
    return jsonify({'id': new_user.id, 'username': new_user.username, 'password': new_user.password}), 201

@app.route('/users', methods=['GET'])
def get_user():
    username = request.args.get('username')
    user = User.query.filter_by(username=username).first()
    if user:
        return jsonify({'id': user.id, 'username': user.username, 'password': user.password}), 200
    return jsonify({'error': 'User not found'}), 404

@app.route('/user', methods=['GET'])
def get_user_by_id():
    user_id = request.args.get('id')
    user = User.query.filter_by(id=user_id).first()
    if user:
        return jsonify({'id': user.id, 'username': user.username, 'password': user.password}), 200
    return jsonify({'error': 'User not found'}), 404

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(port=5001, debug=False)
