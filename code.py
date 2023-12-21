from flask import Flask, request, jsonify, send_file
from flask_sqlalchemy import SQLAlchemy
import os
import secrets
from datetime import datetime, timedelta

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///file_sharing.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'your_secret_key'  # Change this to a random secure key
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    is_ops_user = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(50), nullable=True)
    is_verified = db.Column(db.Boolean, default=False)

class File(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)
    file_size = db.Column(db.Integer, nullable=False)
    assignment_id = db.Column(db.String(50), nullable=False, unique=True)
    uploader_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

def generate_token():
    return secrets.token_urlsafe(32)

@app.route('/ops-login', methods=['POST'])
def ops_login():
    # Authentication logic for Ops User (not implemented in this example)
    return jsonify({'message': 'Ops User Login'}), 200

@app.route('/upload-file', methods=['POST'])
def upload_file():
    # Authorization logic for Ops User (not implemented in this example)

    allowed_extensions = {'pptx', 'docx', 'xlsx'}
    file = request.files['file']

    if file.filename.split('.')[-1] not in allowed_extensions:
        return jsonify({'message': 'Invalid file type. Allowed types: pptx, docx, xlsx'}), 400

    uploader_id = request.form['user_id']
    user = User.query.get(uploader_id)

    if user.is_ops_user:
        return jsonify({'message': 'Ops User required for file upload'}), 403

    file_id = secrets.token_urlsafe(8)
    file.save(os.path.join('uploads', file_id))

    file_info = File(
        filename=file.filename,
        file_type=file.filename.split('.')[-1],
        file_size=os.path.getsize(os.path.join('uploads', file_id)),
        assignment_id=secrets.token_urlsafe(8),
        uploader_id=uploader_id
    )

    db.session.add(file_info)
    db.session.commit()

    return jsonify({'message': 'File uploaded successfully'}), 200

@app.route('/sign-up', methods=['POST'])
def sign_up():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    if User.query.filter_by(email=email).first():
        return jsonify({'message': 'Email is already taken'}), 400

    user = User(email=email, password=password, verification_token=generate_token())
    db.session.add(user)
    db.session.commit()

    verification_url = f'http://localhost:5000/email-verify/{user.id}?token={user.verification_token}'
    # Send verification email logic (not implemented in this example)

    return jsonify({'message': 'Registration successful. Check your email for verification instructions.'}), 200

@app.route('/email-verify/<user_id>', methods=['GET'])
def email_verify(user_id):
    user = User.query.get(user_id)

    if user and user.verification_token == request.args.get('token'):
        user.is_verified = True
        db.session.commit()
        return jsonify({'message': 'Email verified successfully'}), 200
    else:
        return jsonify({'message': 'Invalid verification token'}), 400

@app.route('/client-login', methods=['POST'])
def client_login():
    data = request.get_json()

    email = data.get('email')
    password = data.get('password')

    user = User.query.filter_by(email=email, password=password, is_verified=True).first()

    if user:
        return jsonify({'message': 'Client User Login'}), 200
    else:
        return jsonify({'message': 'Invalid credentials or email not verified'}), 401

@app.route('/secure-download-file/<file_id>', methods=['GET'])
def download_file(file_id):
    file = File.query.get(file_id)

    if not file:
        return jsonify({'message': 'File not found'}), 404

    # Authorization logic for Client User (not implemented in this example)

    access_token = secrets.token_urlsafe(32)
    expiration_time = datetime.now() + timedelta(minutes=30)

    # Store the access token and expiration time in the database or cache
    # You should implement secure storage based on your requirements

    download_url = f'http://localhost:5000/download-file/{file_id}?token={access_token}'

    return jsonify({'download-link': download_url, 'message': 'success'}), 200

@app.route('/download-file/<file_id>', methods=['GET'])
def secure_file_download(file_id):
    # Authorization logic for secure file download (not implemented in this example)

    # Check the access token and expiration time from the database or cache
    # You should implement secure retrieval based on your requirements

    # Example: Check expiration time
    if expiration_time < datetime.now():
        return jsonify({'message': 'Access token expired'}), 401

    file = File.query.get(file_id)
    file_path = os.path.join('uploads', f'{file_id}.{file.file_type}')

    return send_file(file_path, as_attachment=True)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
