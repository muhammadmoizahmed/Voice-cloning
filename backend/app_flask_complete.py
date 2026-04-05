from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import hashlib
import uuid
import os
from functools import wraps

app = Flask(__name__)
CORS(app)

# Database Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voiceforge.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50MB max file size

# Initialize Database
db = SQLAlchemy(app)

# Database Models
class User(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    plan = db.Column(db.String(50), default='free')
    credits_remaining = db.Column(db.Integer, default=3)
    consent_given = db.Column(db.Boolean, default=False)

class Admin(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    role = db.Column(db.String(20), default='admin')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Voice(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    file_path = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('voices', lazy=True))

class Generation(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    voice_id = db.Column(db.String(36), db.ForeignKey('voice.id'), nullable=False)
    text = db.Column(db.Text, nullable=False)
    audio_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('generations', lazy=True))
    voice = db.relationship('Voice', backref=db.backref('generations', lazy=True))

# JWT Token decorators
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = User.query.get(data['user_id'])
            if not current_user:
                return jsonify({'message': 'User not found'}), 401
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Admin token is missing'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_admin = Admin.query.get(data['admin_id'])
            if not current_admin:
                return jsonify({'message': 'Admin not found'}), 401
        except:
            return jsonify({'message': 'Admin token is invalid'}), 401
        
        return f(current_admin, *args, **kwargs)
    return decorated

def generate_token(user_id, is_admin=False):
    payload = {
        'user_id' if not is_admin else 'admin_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# Routes
@app.route('/')
def home():
    return jsonify({
        "app": "VoiceForge AI",
        "version": "1.0.0",
        "description": "AI Voice Cloning Platform",
        "backend": "Flask",
        "database": "SQLite"
    })

# Auth Routes
@app.route('/api/v1/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        if not data or not all(k in data for k in ['email', 'password', 'full_name']):
            return jsonify([{
                "type": "value_error",
                "loc": ["body"],
                "msg": "Email, password, and full name are required",
                "input": data,
                "url": "string"
            }]), 422
        
        email = data['email']
        password = data['password']
        full_name = data['full_name']
        consent = data.get('consent_given', False)
        
        if User.query.filter_by(email=email).first():
            return jsonify([{
                "type": "value_error",
                "loc": ["email"],
                "msg": "Email already registered",
                "input": email,
                "url": "string"
            }]), 422
        
        user = User(
            email=email,
            password=hashlib.sha256(password.encode()).hexdigest(),
            full_name=full_name,
            consent_given=consent
        )
        db.session.add(user)
        db.session.commit()
        
        return jsonify({
            'message': 'User created successfully',
            'requires_verification': True,
            'email': email
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@app.route('/api/v1/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify([{
                "type": "value_error",
                "loc": ["body"],
                "msg": "Email and password are required",
                "input": data,
                "url": "string"
            }]), 422
        
        email = data['username']
        password = data['password']
        
        user = User.query.filter_by(email=email).first()
        if not user or user.password != hashlib.sha256(password.encode()).hexdigest():
            return jsonify([{
                "type": "value_error",
                "loc": ["credentials"],
                "msg": "Invalid email or password",
                "input": email,
                "url": "string"
            }]), 422
        
        if not user.is_verified:
            return jsonify({
                'requires_otp': True,
                'email': user.email
            })
        
        token = generate_token(user.id)
        
        return jsonify({
            'access_token': token,
            'token_type': 'bearer',
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name
            }
        })
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/v1/auth/verify-otp', methods=['POST'])
def verify_otp():
    try:
        email = request.args.get('email')
        otp_code = request.args.get('otp_code')
        
        if not email or not otp_code:
            return jsonify([{
                "type": "value_error",
                "loc": ["query"],
                "msg": "Email and OTP code are required",
                "input": {"email": email, "otp_code": otp_code},
                "url": "string"
            }]), 422
        
        user = User.query.filter_by(email=email).first()
        if not user:
            return jsonify([{
                "type": "value_error",
                "loc": ["email"],
                "msg": "Invalid email",
                "input": email,
                "url": "string"
            }]), 422
        
        if len(otp_code) != 6 or not otp_code.isdigit():
            return jsonify([{
                "type": "value_error",
                "loc": ["otp_code"],
                "msg": "Invalid OTP format",
                "input": otp_code,
                "url": "string"
            }]), 422
        
        user.is_verified = True
        db.session.commit()
        
        token = generate_token(user.id)
        
        return jsonify({
            'access_token': token,
            'user': {
                'id': user.id,
                'email': user.email,
                'full_name': user.full_name
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'message': str(e)}), 500

@app.route('/api/v1/admin/login', methods=['POST'])
def admin_login():
    try:
        data = request.get_json()
        
        if not data or 'username' not in data or 'password' not in data:
            return jsonify([{
                "type": "value_error",
                "loc": ["body"],
                "msg": "Username and password are required",
                "input": data,
                "url": "string"
            }]), 422
        
        username = data['username']
        password = data['password']
        
        admin = Admin.query.filter_by(username=username).first()
        if not admin or admin.password != hashlib.sha256(password.encode()).hexdigest():
            return jsonify([{
                "type": "value_error",
                "loc": ["credentials"],
                "msg": "Invalid admin credentials",
                "input": {"username": username},
                "url": "string"
            }]), 422
        
        token = generate_token(admin.id, is_admin=True)
        
        return jsonify({
            'access_token': token,
            'admin': {
                'id': admin.id,
                'email': admin.email,
                'full_name': admin.full_name,
                'role': admin.role
            }
        })
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

if __name__ == '__main__':
    print("Starting VoiceForge AI Flask Backend...")
    with app.app_context():
        db.create_all()
        
        if not Admin.query.filter_by(username='admin').first():
            admin = Admin(
                username='admin',
                password=hashlib.sha256('admin123'.encode()).hexdigest(),
                email='admin@voiceforge.com',
                full_name='Administrator',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("Default admin created: admin/admin123")
    
    app.run(host='0.0.0.0', port=8000, debug=True)
