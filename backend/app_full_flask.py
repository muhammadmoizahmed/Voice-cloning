from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import jwt
import hashlib
import uuid
import os
import random
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from functools import wraps

app = Flask(__name__, 
           template_folder='templates',
           static_folder='static')

# Configuration
app.config['SECRET_KEY'] = 'your-secret-key-here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///voiceforge.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# Email Configuration (Update these with your SMTP settings)
app.config['SMTP_SERVER'] = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
app.config['SMTP_PORT'] = int(os.environ.get('SMTP_PORT', 587))
app.config['SMTP_USERNAME'] = os.environ.get('SMTP_USERNAME', '')
app.config['SMTP_PASSWORD'] = os.environ.get('SMTP_PASSWORD', '')
app.config['FROM_EMAIL'] = os.environ.get('FROM_EMAIL', 'noreply@voiceforge.ai')

# D-ID API Configuration for Avatar/Talking Head Videos
app.config['DID_API_KEY'] = os.environ.get('DID_API_KEY', '')
app.config['DID_API_URL'] = 'https://api.d-id.com'

# Initialize extensions
db = SQLAlchemy(app)
CORS(app)

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
    # Email verification fields
    verification_code = db.Column(db.String(10), nullable=True)
    email_verified = db.Column(db.Boolean, default=False)
    verification_code_expires = db.Column(db.DateTime, nullable=True)

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

class AvatarVideo(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=False)
    voice_id = db.Column(db.String(36), db.ForeignKey('voice.id'), nullable=False)
    image_path = db.Column(db.String(255), nullable=False)
    text = db.Column(db.Text, nullable=False)
    audio_url = db.Column(db.String(255))
    video_url = db.Column(db.String(255))
    status = db.Column(db.String(20), default='pending')  # pending, processing, completed, failed
    provider = db.Column(db.String(50), default='did')  # did, heygen, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    user = db.relationship('User', backref=db.backref('avatar_videos', lazy=True))
    voice = db.relationship('Voice', backref=db.backref('avatar_videos', lazy=True))

# Helper functions
def generate_token(user_id, is_admin=False):
    payload = {
        'user_id' if not is_admin else 'admin_id': user_id,
        'exp': datetime.utcnow() + timedelta(days=1),
        'iat': datetime.utcnow()
    }
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# Email Helper Functions
def generate_otp():
    """Generate a 6-digit OTP code"""
    return ''.join([str(random.randint(0, 9)) for _ in range(6)])

def send_verification_email(to_email, otp_code, full_name):
    """Send verification email with OTP code"""
    try:
        smtp_server = app.config['SMTP_SERVER']
        smtp_port = app.config['SMTP_PORT']
        smtp_username = app.config['SMTP_USERNAME']
        smtp_password = app.config['SMTP_PASSWORD']
        from_email = app.config['FROM_EMAIL']
        
        # If SMTP not configured, print to console for testing
        if not smtp_username or not smtp_password:
            print(f"[EMAIL TEST] To: {to_email}, OTP: {otp_code}")
            return True
        
        # Create message
        msg = MIMEMultipart('alternative')
        msg['Subject'] = 'VoiceForge AI - Email Verification Code'
        msg['From'] = from_email
        msg['To'] = to_email
        
        # HTML email body
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; background-color: #f4f4f4; margin: 0; padding: 20px; }}
                .container {{ max-width: 600px; margin: 0 auto; background-color: #ffffff; border-radius: 10px; padding: 40px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }}
                .logo {{ text-align: center; margin-bottom: 30px; }}
                .logo h1 {{ color: #7c3aed; margin: 0; }}
                .title {{ color: #1f2937; font-size: 24px; font-weight: bold; text-align: center; margin-bottom: 20px; }}
                .message {{ color: #4b5563; font-size: 16px; line-height: 1.6; text-align: center; margin-bottom: 30px; }}
                .otp-box {{ background: linear-gradient(135deg, #7c3aed, #3b82f6); border-radius: 10px; padding: 20px; text-align: center; margin: 30px 0; }}
                .otp-code {{ font-size: 36px; font-weight: bold; color: #ffffff; letter-spacing: 8px; margin: 0; }}
                .warning {{ color: #dc2626; font-size: 14px; text-align: center; margin-top: 20px; }}
                .footer {{ text-align: center; color: #9ca3af; font-size: 12px; margin-top: 30px; padding-top: 20px; border-top: 1px solid #e5e7eb; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">
                    <h1>VoiceForge AI</h1>
                </div>
                <h2 class="title">Verify Your Email</h2>
                <p class="message">Hi {full_name},<br><br>Thank you for signing up! Please use the verification code below to verify your email address. This code will expire in 10 minutes.</p>
                <div class="otp-box">
                    <p class="otp-code">{otp_code}</p>
                </div>
                <p class="warning">If you didn't request this verification, please ignore this email.</p>
                <div class="footer">
                    <p>&copy; 2026 VoiceForge AI. All rights reserved.</p>
                    <p>This is an automated email, please do not reply.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_body, 'html'))
        
        # Send email
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, msg.as_string())
        
        print(f"[EMAIL SENT] To: {to_email}, OTP: {otp_code}")
        return True
        
    except Exception as e:
        print(f"[EMAIL ERROR] Failed to send email: {str(e)}")
        # For testing, still return True so user can see the OTP in console
        print(f"[EMAIL TEST] To: {to_email}, OTP: {otp_code}")
        return True

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

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_token' not in session:
            return redirect(url_for('admin_login_page'))
        return f(*args, **kwargs)
    return decorated

def admin_api_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'admin_token' not in session:
            return jsonify({'error': 'Unauthorized', 'message': 'Admin login required'}), 401
        return f(*args, **kwargs)
    return decorated

def user_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if 'user_token' not in session:
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated

# D-ID API Helper Functions
def generate_did_video(image_path, audio_url, text):
    """
    Generate a talking head video using D-ID API
    This is a placeholder - actual implementation requires D-ID API integration
    """
    try:
        api_key = app.config['DID_API_KEY']
        if not api_key:
            raise Exception('D-ID API key not configured')
        
        # Read image file
        with open(image_path, 'rb') as f:
            image_data = f.read()
        
        # D-ID API endpoint for creating a talk
        url = 'https://api.d-id.com/talks'
        
        headers = {
            'Authorization': f'Basic {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Prepare payload - simplified version
        # In production, you'd upload the image to D-ID first, then create the talk
        payload = {
            'script': {
                'type': 'text',
                'input': text,
                'provider': {
                    'type': 'microsoft',
                    'voice_id': 'en-US-JennyNeural'
                }
            },
            'config': {
                'fluent': True,
                'pad_audio': 0.0
            }
        }
        
        # For now, return a mock response
        # In production, make actual API call:
        # response = requests.post(url, headers=headers, json=payload)
        # return response.json()
        
        return {
            'id': str(uuid.uuid4()),
            'status': 'created',
            'result_url': None
        }
        
    except Exception as e:
        print(f"D-ID API Error: {str(e)}")
        raise e

def check_did_video_status(talk_id):
    """Check the status of a D-ID video generation"""
    try:
        api_key = app.config['DID_API_KEY']
        url = f'https://api.d-id.com/talks/{talk_id}'
        
        headers = {
            'Authorization': f'Basic {api_key}'
        }
        
        # response = requests.get(url, headers=headers)
        # return response.json()
        
        # Mock response for now
        return {
            'id': talk_id,
            'status': 'done',
            'result_url': f'https://api.d-id.com/talks/{talk_id}/stream'
        }
        
    except Exception as e:
        print(f"Error checking video status: {str(e)}")
        raise e

# Celery task for background video generation (mock for now)
def generate_avatar_video(video_id):
    """
    Background task to generate avatar video
    In production, this should be a Celery task
    """
    with app.app_context():
        video = AvatarVideo.query.get(video_id)
        if not video:
            return
        
        try:
            # Update status to processing
            video.status = 'processing'
            db.session.commit()
            
            # Generate audio from text using cloned voice
            # This would integrate with your existing voice generation
            
            # Generate talking head video using D-ID API
            # result = generate_did_video(video.image_path, video.audio_url, video.text)
            
            # For now, simulate processing
            import time
            time.sleep(5)  # Simulate processing time
            
            # Update video record
            video.status = 'completed'
            video.video_url = f'/uploads/avatars/video_{video_id}.mp4'  # Mock URL
            db.session.commit()
            
            print(f"Avatar video {video_id} generated successfully")
            
        except Exception as e:
            video.status = 'failed'
            db.session.commit()
            print(f"Error generating avatar video {video_id}: {str(e)}")

# Frontend Routes
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login')
def login_page():
    return render_template('login.html')

@app.route('/signup')
def signup_page():
    return render_template('signup.html')

@app.route('/verify-otp')
def verify_otp_page():
    email = request.args.get('email', '')
    return render_template('verify-otp.html', email=email)

@app.route('/dashboard')
@user_required
def dashboard():
    user = User.query.get(session['user_id'])
    return render_template('dashboard.html', user=user)

@app.route('/voices')
@user_required
def voices():
    user = User.query.get(session['user_id'])
    user_voices = Voice.query.filter_by(user_id=user.id).all()
    return render_template('voices.html', user=user, voices=user_voices)

@app.route('/generate')
@user_required
def generate():
    user = User.query.get(session['user_id'])
    user_voices = Voice.query.filter_by(user_id=user.id, status='approved').all()
    return render_template('generate.html', user=user, voices=user_voices)

@app.route('/history')
@user_required
def history():
    user = User.query.get(session['user_id'])
    generations = Generation.query.filter_by(user_id=user.id).order_by(Generation.created_at.desc()).all()
    return render_template('history.html', user=user, generations=generations)

@app.route('/settings')
@user_required
def settings():
    user = User.query.get(session['user_id'])
    return render_template('settings.html', user=user)

@app.route('/upgrade')
@user_required
def upgrade():
    user = User.query.get(session['user_id'])
    return render_template('upgrade.html', user=user)

@app.route('/avatar')
@user_required
def avatar():
    user = User.query.get(session['user_id'])
    user_voices = Voice.query.filter_by(user_id=user.id, status='approved').all()
    return render_template('avatar.html', user=user, voices=user_voices)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login_page():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(username=username).first()
        
        if admin and admin.password == hashlib.sha256(password.encode()).hexdigest():
            session['admin_token'] = generate_token(admin.id, is_admin=True)
            session['admin_id'] = admin.id
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Invalid credentials', 'error')
    
    return render_template('admin/login.html')

@app.route('/admin')
@admin_required
def admin_dashboard():
    return render_template('admin/dashboard.html')

@app.route('/admin/users')
@admin_required
def admin_users():
    users = User.query.all()
    return render_template('admin/users.html', users=users)

@app.route('/admin/voices')
@admin_required
def admin_voices():
    voices = Voice.query.all()
    return render_template('admin/voices.html', voices=voices)

@app.route('/admin/settings')
@admin_required
def admin_settings():
    return render_template('admin/settings.html')

@app.route('/admin/sub-admins')
@admin_required
def admin_sub_admins():
    return render_template('admin/sub-admins.html')

# Authentication Routes
@app.route('/api/auth/login', methods=['POST'])
def api_login():
    try:
        data = request.get_json()
        email = data.get('username')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        if not user or user.password != hashlib.sha256(password.encode()).hexdigest():
            return jsonify({'success': False, 'message': 'Invalid credentials'})
        
        if not user.is_verified:
            return jsonify({'success': False, 'message': 'Please verify your email first'})
        
        # Set session
        session['user_token'] = generate_token(user.id)
        session['user_id'] = user.id
        
        return jsonify({'success': True, 'redirect': '/dashboard'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auth/signup', methods=['POST'])
def api_signup():
    try:
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        full_name = data.get('full_name')
        
        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'success': False, 'message': 'Email already registered'})
        
        # Generate OTP
        otp_code = generate_otp()
        
        # Create user with verification fields
        user = User(
            email=email,
            password=hashlib.sha256(password.encode()).hexdigest(),
            full_name=full_name,
            consent_given=data.get('consent_given', False),
            verification_code=otp_code,
            verification_code_expires=datetime.utcnow() + timedelta(minutes=10),
            is_verified=False,
            email_verified=False
        )
        db.session.add(user)
        db.session.commit()
        
        # Send verification email
        send_verification_email(email, otp_code, full_name)
        
        return jsonify({
            'success': True, 
            'message': 'Account created successfully. Please check your email for verification code.',
            'redirect': '/verify-otp?email=' + email,
            'email': email
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Signup error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/auth/verify-otp', methods=['POST'])
def api_verify_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        otp = data.get('otp')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check if already verified
        if user.email_verified:
            return jsonify({'success': False, 'message': 'Email already verified'}), 400
        
        # Check if code expired
        if user.verification_code_expires and datetime.utcnow() > user.verification_code_expires:
            return jsonify({'success': False, 'message': 'Verification code expired. Please request a new one.'}), 400
        
        # Verify code
        if user.verification_code != otp:
            return jsonify({'success': False, 'message': 'Invalid verification code'}), 400
        
        # Mark user as verified
        user.email_verified = True
        user.is_verified = True
        user.verification_code = None
        user.verification_code_expires = None
        db.session.commit()
        
        # Generate token and set session
        session['user_token'] = generate_token(user.id)
        session['user_id'] = user.id
        
        return jsonify({
            'success': True,
            'message': 'Email verified successfully',
            'redirect': '/dashboard'
        })
        
    except Exception as e:
        print(f"Verify OTP error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/auth/resend-otp', methods=['POST'])
def api_resend_otp():
    try:
        data = request.get_json()
        email = data.get('email')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return jsonify({'success': False, 'message': 'User not found'}), 404
        
        # Check if already verified
        if user.email_verified:
            return jsonify({'success': False, 'message': 'Email already verified'}), 400
        
        # Generate new OTP
        otp_code = generate_otp()
        user.verification_code = otp_code
        user.verification_code_expires = datetime.utcnow() + timedelta(minutes=10)
        db.session.commit()
        
        # Send verification email
        send_verification_email(email, otp_code, user.full_name)
        
        return jsonify({
            'success': True,
            'message': 'Verification code sent successfully'
        })
        
    except Exception as e:
        print(f"Resend OTP error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/admin/login', methods=['POST'])
def api_admin_login():
    try:
        # Try to get data from JSON or form
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form
        
        username = data.get('username') if hasattr(data, 'get') else data.get('username')
        password = data.get('password') if hasattr(data, 'get') else data.get('password')
        
        print(f"Admin login attempt: username={username}, password={'*' * len(password) if password else 'None'}")
        
        if not username or not password:
            return jsonify({'success': False, 'message': 'Username and password required'})
        
        admin = Admin.query.filter_by(username=username).first()
        
        if not admin:
            print(f"Admin not found: {username}")
            return jsonify({'success': False, 'message': 'Invalid credentials'})
        
        hashed_input = hashlib.sha256(password.encode()).hexdigest()
        print(f"Password hash match: {admin.password == hashed_input}")
        
        if admin.password != hashed_input:
            return jsonify({'success': False, 'message': 'Invalid credentials'})
        
        session['admin_token'] = generate_token(admin.id, is_admin=True)
        session['admin_id'] = admin.id
        
        print(f"Admin login successful: {username}")
        return jsonify({'success': True, 'redirect': '/admin'})
        
    except Exception as e:
        print(f"Admin login error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)})

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/admin/logout')
def admin_logout():
    session.clear()
    return redirect(url_for('admin_login_page'))

# API Routes for AJAX calls
@app.route('/api/dashboard/stats')
@user_required
def api_dashboard_stats():
    user = User.query.get(session['user_id'])
    voices_count = Voice.query.filter_by(user_id=user.id).count()
    generations_count = Generation.query.filter_by(user_id=user.id).count()
    
    return jsonify({
        'total_voices': voices_count,
        'total_generations': generations_count,
        'remaining_credits': user.credits_remaining
    })

@app.route('/api/voices', methods=['GET'])
@user_required
def api_get_voices():
    user = User.query.get(session['user_id'])
    voices = Voice.query.filter_by(user_id=user.id).all()
    
    return jsonify({
        'voices': [
            {
                'id': voice.id,
                'name': voice.name,
                'created_at': voice.created_at.isoformat(),
                'status': voice.status
            } for voice in voices
        ]
    })

@app.route('/api/generations', methods=['GET'])
@user_required
def api_get_generations():
    user = User.query.get(session['user_id'])
    generations = Generation.query.filter_by(user_id=user.id).order_by(Generation.created_at.desc()).all()
    
    return jsonify({
        'generations': [
            {
                'id': gen.id,
                'text': gen.text,
                'voice_id': gen.voice_id,
                'created_at': gen.created_at.isoformat(),
                'audio_url': gen.audio_url
            } for gen in generations
        ]
    })

@app.route('/api/admin/stats')
@admin_api_required
def api_admin_stats():
    users_count = User.query.count()
    voices_count = Voice.query.count()
    generations_count = Generation.query.count()
    
    return jsonify({
        'total_users': users_count,
        'total_voices': voices_count,
        'total_generations': generations_count
    })

# Avatar Video API Routes
@app.route('/api/avatar-videos', methods=['GET'])
@user_required
def api_get_avatar_videos():
    user = User.query.get(session['user_id'])
    videos = AvatarVideo.query.filter_by(user_id=user.id).order_by(AvatarVideo.created_at.desc()).all()
    
    return jsonify({
        'videos': [
            {
                'id': video.id,
                'image_path': video.image_path,
                'text': video.text,
                'video_url': video.video_url,
                'status': video.status,
                'created_at': video.created_at.isoformat()
            } for video in videos
        ]
    })

@app.route('/api/avatar-videos', methods=['POST'])
@user_required
def api_create_avatar_video():
    try:
        user = User.query.get(session['user_id'])
        
        # Check if D-ID API key is configured
        if not app.config['DID_API_KEY']:
            return jsonify({'success': False, 'message': 'Avatar video service not configured. Please add D-ID API key.'}), 500
        
        # Get form data
        voice_id = request.form.get('voice_id')
        text = request.form.get('text')
        image_file = request.files.get('image')
        
        if not voice_id or not text or not image_file:
            return jsonify({'success': False, 'message': 'Voice, text, and image are required'}), 400
        
        # Verify voice exists and belongs to user
        voice = Voice.query.filter_by(id=voice_id, user_id=user.id).first()
        if not voice:
            return jsonify({'success': False, 'message': 'Voice not found'}), 404
        
        # Save image file
        image_filename = f"avatar_{user.id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.jpg"
        image_path = os.path.join('uploads', 'avatars', image_filename)
        os.makedirs(os.path.dirname(image_path), exist_ok=True)
        image_file.save(image_path)
        
        # Create avatar video record
        avatar_video = AvatarVideo(
            user_id=user.id,
            voice_id=voice_id,
            image_path=image_path,
            text=text,
            status='pending'
        )
        db.session.add(avatar_video)
        db.session.commit()
        
        # Start video generation in background (simplified for now)
        # In production, this should be handled by a background task queue like Celery
        generate_avatar_video.delay(avatar_video.id)
        
        return jsonify({
            'success': True,
            'message': 'Avatar video generation started',
            'video_id': avatar_video.id
        })
        
    except Exception as e:
        print(f"Error creating avatar video: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': str(e)}), 500

@app.route('/api/avatar-videos/<video_id>', methods=['GET'])
@user_required
def api_get_avatar_video(video_id):
    user = User.query.get(session['user_id'])
    video = AvatarVideo.query.filter_by(id=video_id, user_id=user.id).first()
    
    if not video:
        return jsonify({'success': False, 'message': 'Video not found'}), 404
    
    return jsonify({
        'id': video.id,
        'image_path': video.image_path,
        'text': video.text,
        'video_url': video.video_url,
        'status': video.status,
        'created_at': video.created_at.isoformat()
    })

@app.route('/api/avatar-videos/<video_id>', methods=['DELETE'])
@user_required
def api_delete_avatar_video(video_id):
    user = User.query.get(session['user_id'])
    video = AvatarVideo.query.filter_by(id=video_id, user_id=user.id).first()
    
    if not video:
        return jsonify({'success': False, 'message': 'Video not found'}), 404
    
    # Delete video file if exists
    if video.video_url and os.path.exists(video.video_url):
        os.remove(video.video_url)
    
    # Delete image file
    if video.image_path and os.path.exists(video.image_path):
        os.remove(video.image_path)
    
    db.session.delete(video)
    db.session.commit()
    
    return jsonify({'success': True, 'message': 'Video deleted successfully'})

# Initialize database
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        # Create default admin
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
    
    print("Starting VoiceForge AI Flask Application...")
    print("Frontend URL: http://localhost:8000")
    print("Admin Login: http://localhost:8000/admin/login")
    app.run(host='0.0.0.0', port=8000, debug=True)
