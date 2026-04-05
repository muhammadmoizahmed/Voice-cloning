from flask import Flask, request, jsonify
from flask_cors import CORS
import os
from datetime import datetime, timedelta
import jwt
import hashlib
import uuid
from functools import wraps

app = Flask(__name__)
CORS(app)

# Secret key for JWT
app.config['SECRET_KEY'] = 'your-secret-key-here'

# In-memory storage (for demo)
users = {}
admin_users = {}
voices = []
generations = []

# JWT Token decorator
def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_user = data['user']
        except:
            return jsonify({'message': 'Token is invalid'}), 401
        
        return f(current_user, *args, **kwargs)
    return decorated

# Admin token decorator
def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Admin token is missing'}), 401
        
        try:
            token = token.replace('Bearer ', '')
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
            current_admin = data['admin']
        except:
            return jsonify({'message': 'Admin token is invalid'}), 401
        
        return f(current_admin, *args, **kwargs)
    return decorated

# Helper function to generate token
def generate_token(user_data, is_admin=False):
    payload = {
        'user' if not is_admin else 'admin': user_data,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    key = 'admin' if is_admin else 'user'
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# Routes
@app.route('/')
def home():
    return jsonify({
        "app": "VoiceForge AI",
        "version": "1.0.0",
        "description": "AI Voice Cloning Platform",
        "endpoints": {
            "auth": "/api/v1/auth",
            "voices": "/api/v1/voices",
            "generations": "/api/v1/generations",
            "dashboard": "/api/v1/dashboard",
            "admin": "/api/v1/admin"
        }
    })

# Auth Routes
@app.route('/api/v1/auth/signup', methods=['POST'])
def signup():
    try:
        data = request.get_json()
        
        # Validation
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
        
        if email in users:
            return jsonify([{
                "type": "value_error",
                "loc": ["email"],
                "msg": "Email already registered",
                "input": email,
                "url": "string"
            }]), 422
        
        # Create user
        user_id = str(uuid.uuid4())
        users[email] = {
            'id': user_id,
            'email': email,
            'password': hashlib.sha256(password.encode()).hexdigest(),
            'full_name': full_name,
            'created_at': datetime.utcnow().isoformat(),
            'verified': False
        }
        
        return jsonify({
            'message': 'User created successfully',
            'requires_verification': True,
            'email': email
        }), 201
        
    except Exception as e:
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
        
        if email not in users:
            return jsonify([{
                "type": "value_error",
                "loc": ["email"],
                "msg": "Invalid email or password",
                "input": email,
                "url": "string"
            }]), 422
        
        user = users[email]
        if user['password'] != hashlib.sha256(password.encode()).hexdigest():
            return jsonify([{
                "type": "value_error",
                "loc": ["password"],
                "msg": "Invalid email or password",
                "input": "****",
                "url": "string"
            }]), 422
        
        # Generate token
        token = generate_token({
            'id': user['id'],
            'email': user['email'],
            'full_name': user['full_name']
        })
        
        return jsonify({
            'access_token': token,
            'token_type': 'bearer',
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name']
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
        
        if email not in users:
            return jsonify([{
                "type": "value_error",
                "loc": ["email"],
                "msg": "Invalid email",
                "input": email,
                "url": "string"
            }]), 422
        
        # For demo, accept any 6-digit OTP
        if len(otp_code) != 6 or not otp_code.isdigit():
            return jsonify([{
                "type": "value_error",
                "loc": ["otp_code"],
                "msg": "Invalid OTP format",
                "input": otp_code,
                "url": "string"
            }]), 422
        
        users[email]['verified'] = True
        
        user = users[email]
        token = generate_token({
            'id': user['id'],
            'email': user['email'],
            'full_name': user['full_name']
        })
        
        return jsonify({
            'access_token': token,
            'user': {
                'id': user['id'],
                'email': user['email'],
                'full_name': user['full_name']
            }
        })
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

@app.route('/api/v1/auth/resend-otp', methods=['POST'])
def resend_otp():
    try:
        email = request.args.get('email')
        
        if not email:
            return jsonify([{
                "type": "value_error",
                "loc": ["query"],
                "msg": "Email is required",
                "input": email,
                "url": "string"
            }]), 422
        
        if email not in users:
            return jsonify([{
                "type": "value_error",
                "loc": ["email"],
                "msg": "Email not found",
                "input": email,
                "url": "string"
            }]), 422
        
        # For demo, just return success
        return jsonify({'message': 'OTP sent successfully'})
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Admin Routes
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
        
        # Default admin credentials
        if username == 'admin' and password == 'admin123':
            token = generate_token({
                'id': '1',
                'email': 'admin@voiceforge.com',
                'full_name': 'Administrator',
                'role': 'admin'
            }, is_admin=True)
            
            return jsonify({
                'access_token': token,
                'admin': {
                    'id': '1',
                    'email': 'admin@voiceforge.com',
                    'full_name': 'Administrator',
                    'role': 'admin'
                }
            })
        
        return jsonify([{
            "type": "value_error",
            "loc": ["credentials"],
            "msg": "Invalid admin credentials",
            "input": {"username": username},
            "url": "string"
        }]), 422
        
    except Exception as e:
        return jsonify({'message': str(e)}), 500

# Dashboard Route
@app.route('/api/v1/dashboard/stats', methods=['GET'])
@token_required
def dashboard_stats(current_user):
    return jsonify({
        'total_voices': 5,
        'total_generations': 23,
        'remaining_credits': 27
    })

# Voices Routes
@app.route('/api/v1/voices', methods=['GET'])
@token_required
def get_voices(current_user):
    return jsonify({
        'voices': [
            {
                'id': '1',
                'name': 'My Voice',
                'created_at': '2024-01-01T00:00:00Z',
                'status': 'active'
            }
        ]
    })

@app.route('/api/v1/voices', methods=['POST'])
@token_required
def create_voice(current_user):
    return jsonify({
        'message': 'Voice created successfully',
        'voice_id': str(uuid.uuid4())
    }), 201

# Generations Routes
@app.route('/api/v1/generations', methods=['POST'])
@token_required
def create_generation(current_user):
    return jsonify({
        'message': 'Audio generated successfully',
        'generation_id': str(uuid.uuid4()),
        'audio_url': '/api/v1/generations/audio/sample.mp3'
    }), 201

@app.route('/api/v1/generations', methods=['GET'])
@token_required
def get_generations(current_user):
    return jsonify({
        'generations': [
            {
                'id': '1',
                'text': 'Hello world',
                'voice_id': '1',
                'created_at': '2024-01-01T00:00:00Z',
                'audio_url': '/api/v1/generations/audio/sample.mp3'
            }
        ]
    })

# Admin Dashboard
@app.route('/api/v1/admin/stats', methods=['GET'])
@admin_token_required
def admin_stats(current_admin):
    return jsonify({
        'total_users': 150,
        'total_voices': 450,
        'total_generations': 2300
    })

if __name__ == '__main__':
    print("Starting VoiceForge AI Flask Backend...")
    app.run(host='0.0.0.0', port=8000, debug=True)
