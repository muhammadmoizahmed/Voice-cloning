# VoiceForge AI - API Connections & Services

## 🌐 External API Connections

### Voice Service Providers

#### 1. ElevenLabs API
```python
# Connection Details
API Endpoint: https://api.elevenlabs.io/v1/
Authentication: API Key (xi-...)
Purpose: Voice cloning & Text-to-Speech

# Services Used
- Voice Cloning: POST /voices/add
- Text-to-Speech: POST /text-to-speech/{voice_id}
- Voice List: GET /voices
- Voice Delete: DELETE /voices/{voice_id}
```

**Connection Flow:**
```
User Upload → File Validation → ElevenLabs API → Voice ID → Database
Text Input → Voice Selection → ElevenLabs TTS → Audio File → User
```

#### 2. Fish.Audio API
```python
# Connection Details
API Endpoint: https://api.fish.audio/v1/
Authentication: API Key
Purpose: Alternative Text-to-Speech service

# Services Used
- Voice Cloning: POST /voice/clone
- Text-to-Speech: POST /tts
- Voice Management: GET/PUT/DELETE /voice/{id}
```

**Connection Flow:**
```
User Upload → File Validation → Fish.Audio API → Voice ID → Database
Text Input → Voice Selection → Fish.Audio TTS → Audio File → User
```

#### 3. Resemble AI API
```python
# Connection Details
API Endpoint: https://api.resemble.ai/v2/
Authentication: API Key
Purpose: Enhanced voice cloning

# Services Used
- Voice Cloning: POST /voices
- Text-to-Speech: POST /synthesize
- Voice Management: GET/PUT/DELETE /voices/{uuid}
```

**Connection Flow:**
```
User Upload → File Validation → Resemble AI API → Voice UUID → Database
Text Input → Voice Selection → Resemble AI TTS → Audio File → User
```

### Payment Processing

#### Stripe API
```python
# Connection Details
API Endpoint: https://api.stripe.com/v1/
Authentication: Secret Key (sk_test_... / sk_live_...)
Purpose: Payment processing & subscriptions

# Services Used
- Checkout Session: POST /checkout/sessions
- Payment Intent: GET/POST /payment_intents
- Subscription: GET/POST /subscriptions
- Webhook: POST /webhook
- Customer: GET/POST /customers
```

**Connection Flow:**
```
User Selects Plan → Stripe Checkout → Payment → Webhook → Plan Update
Subscription Renewal → Stripe Webhook → Plan Extension
```

### Email Service

#### SMTP Configuration
```python
# Connection Details
Server: smtp.gmail.com
Port: 587 (TLS)
Authentication: Username + App Password
Purpose: OTP verification & notifications

# Email Types
- OTP Verification: 6-digit code
- Password Reset: Secure reset link
- Welcome Email: Account activation
- Payment Confirmation: Receipt & plan details
```

**Connection Flow:**
```
User Action → Email Template → SMTP Server → User Inbox
OTP Input → Verification → Account Access
```

## 🔗 Internal API Connections

### Frontend to Backend

#### Authentication Flow
```javascript
// Frontend (JavaScript)
const login = async (email, password) => {
    const response = await axios.post('/api/v1/auth/login', {
        email, password
    });
    localStorage.setItem('token', response.data.access_token);
};

// Backend (FastAPI)
@app.post("/api/v1/auth/login")
async def login(credentials: UserLogin):
    user = authenticate_user(credentials.email, credentials.password)
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}
```

#### Voice Upload Flow
```javascript
// Frontend
const uploadVoice = async (formData) => {
    const response = await axios.post('/api/v1/voices/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    });
    return response.data;
};

// Backend
@app.post("/api/v1/voices/upload")
async def upload_voice(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    # Process file, call external API, save to database
    return {"voice_id": voice.id, "status": "cloning"}
```

#### Audio Generation Flow
```javascript
// Frontend
const generateAudio = async (voiceId, text) => {
    const response = await axios.post('/api/v1/generations', {
        voice_id: voiceId,
        script_text: text
    });
    return response.data;
};

// Backend
@app.post("/api/v1/generations")
async def generate_audio(
    data: AudioGenerationCreate,
    current_user: User = Depends(get_current_user)
):
    # Check usage limits, call TTS API, save result
    return {"generation_id": generation.id, "status": "processing"}
```

### Backend to External APIs

#### Voice Cloning Service
```python
# Service Class
class VoiceCloningService:
    def __init__(self, provider: str = "elevenlabs"):
        self.provider = provider
        self.api_key = self.get_api_key(provider)
    
    async def clone_voice(self, file_path: str, name: str):
        if self.provider == "elevenlabs":
            return await self.clone_with_elevenlabs(file_path, name)
        elif self.provider == "fish_audio":
            return await self.clone_with_fish_audio(file_path, name)
        elif self.provider == "resemble":
            return await self.clone_with_resemble(file_path, name)
    
    async def clone_with_elevenlabs(self, file_path: str, name: str):
        url = "https://api.elevenlabs.io/v1/voices/add"
        headers = {"xi-api-key": self.api_key}
        
        with open(file_path, "rb") as f:
            files = {"files": f}
            data = {"name": name}
            
            async with httpx.AsyncClient() as client:
                response = await client.post(url, headers=headers, files=files, data=data)
                return response.json()
```

#### Text-to-Speech Service
```python
class TTSService:
    def __init__(self, provider: str = "elevenlabs"):
        self.provider = provider
        self.api_key = self.get_api_key(provider)
    
    async def generate_speech(self, text: str, voice_id: str):
        if self.provider == "elevenlabs":
            return await self.generate_with_elevenlabs(text, voice_id)
        elif self.provider == "fish_audio":
            return await self.generate_with_fish_audio(text, voice_id)
    
    async def generate_with_elevenlabs(self, text: str, voice_id: str):
        url = f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}"
        headers = {
            "xi-api-key": self.api_key,
            "Content-Type": "application/json"
        }
        
        data = {
            "text": text,
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.75
            }
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            return response.content
```

#### Payment Service
```python
class PaymentService:
    def __init__(self):
        stripe.api_key = settings.stripe_secret_key
    
    async def create_checkout_session(self, plan_id: int, user_id: int):
        plan = get_plan_by_id(plan_id)
        
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {'name': plan.display_name},
                    'unit_amount': int(plan.price_monthly * 100),
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f'{settings.frontend_url}/upgrade?success=true',
            cancel_url=f'{settings.frontend_url}/upgrade?canceled=true',
            metadata={'user_id': user_id, 'plan_id': plan_id}
        )
        
        return session.id
```

## 🔄 Database Connections

### SQLAlchemy ORM Setup
```python
# Database Configuration
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Dependency Injection
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### Model Relationships
```python
# User Model
class User(Base):
    __tablename__ = "users"
    
    # Relationships
    voices = relationship("Voice", back_populates="user", cascade="all, delete-orphan")
    generations = relationship("AudioGeneration", back_populates="user", cascade="all, delete-orphan")
    payments = relationship("Payment", back_populates="user", cascade="all, delete-orphan")

# Voice Model
class Voice(Base):
    __tablename__ = "voices"
    
    # Relationships
    user = relationship("User", back_populates="voices")
    generations = relationship("AudioGeneration", back_populates="voice")
```

### Database Operations
```python
# CRUD Operations
class UserService:
    def __init__(self, db: Session):
        self.db = db
    
    def create_user(self, user_data: UserCreate):
        db_user = User(**user_data.dict())
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        return db_user
    
    def get_user_by_email(self, email: str):
        return self.db.query(User).filter(User.email == email).first()
    
    def update_user_plan(self, user_id: int, plan: PlanType):
        user = self.db.query(User).filter(User.id == user_id).first()
        if user:
            user.plan = plan
            user.plan_renewal_date = datetime.utcnow() + timedelta(days=30)
            self.db.commit()
        return user
```

## 📁 File Storage Connections

### Local File System
```python
# File Upload Handler
class FileService:
    def __init__(self):
        self.upload_dir = settings.upload_dir
        self.output_dir = settings.output_dir
    
    def save_upload(self, file: UploadFile, filename: str):
        file_path = os.path.join(self.upload_dir, filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        return file_path
    
    def save_output(self, audio_content: bytes, filename: str):
        file_path = os.path.join(self.output_dir, filename)
        with open(file_path, "wb") as f:
            f.write(audio_content)
        return file_path
```

### Static File Serving
```python
# FastAPI Static Files
app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")
app.mount("/outputs", StaticFiles(directory=settings.output_dir), name="outputs")
app.mount("/static", StaticFiles(directory="static"), name="static")
```

## 🔐 Security Connections

### JWT Authentication
```python
# JWT Service
class JWTService:
    def __init__(self):
        self.secret_key = settings.jwt_secret_key
        self.algorithm = settings.jwt_algorithm
        self.expiration_hours = settings.jwt_expiration_hours
    
    def create_access_token(self, data: dict):
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(hours=self.expiration_hours)
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str):
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.PyJWTError:
            return None
```

### Password Hashing
```python
# Password Service
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class PasswordService:
    @staticmethod
    def hash_password(password: str):
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str):
        return pwd_context.verify(plain_password, hashed_password)
```

## 📊 Monitoring Connections

### Audit Logging
```python
# Audit Service
class AuditService:
    def __init__(self, db: Session):
        self.db = db
    
    def log_action(self, user_id: int, action: str, resource_type: str, resource_id: int = None):
        audit_log = AuditLog(
            user_id=user_id,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            ip_address=request.client.host,
            user_agent=request.headers.get("user-agent"),
            created_at=datetime.utcnow()
        )
        self.db.add(audit_log)
        self.db.commit()
```

### Error Tracking
```python
# Error Handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True)
    
    # Send to external monitoring (Sentry, etc.)
    if settings.sentry_dsn:
        sentry_sdk.capture_exception(exc)
    
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )
```

## 🔄 Webhook Connections

### Stripe Webhook Handler
```python
# Webhook Service
class WebhookService:
    def __init__(self, db: Session):
        self.db = db
    
    async def handle_stripe_webhook(self, payload: bytes, signature: str):
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, settings.stripe_webhook_secret
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail="Invalid payload")
        
        if event.type == "checkout.session.completed":
            await self.handle_payment_success(event.data.object)
        elif event.type == "invoice.payment_succeeded":
            await self.handle_subscription_renewal(event.data.object)
    
    async def handle_payment_success(self, session):
        user_id = int(session.metadata["user_id"])
        plan_id = int(session.metadata["plan_id"])
        
        # Update user plan
        user_service = UserService(self.db)
        await user_service.update_user_plan(user_id, plan_id)
        
        # Send confirmation email
        await email_service.send_payment_confirmation(user_id, plan_id)
```

## 📱 Frontend Connections

### JavaScript API Client
```javascript
// API Service Class
class VoiceForgeAPI {
    constructor() {
        this.baseURL = '/api/v1';
        this.setupAuth();
    }
    
    setupAuth() {
        const token = localStorage.getItem('token');
        if (token) {
            axios.defaults.headers.common['Authorization'] = `Bearer ${token}`;
        }
    }
    
    // Authentication
    async login(email, password) {
        const response = await axios.post(`${this.baseURL}/auth/login`, {
            email, password
        });
        localStorage.setItem('token', response.data.access_token);
        this.setupAuth();
        return response.data;
    }
    
    // Voices
    async uploadVoice(formData) {
        const response = await axios.post(`${this.baseURL}/voices/upload`, formData, {
            headers: { 'Content-Type': 'multipart/form-data' }
        });
        return response.data;
    }
    
    // Generations
    async generateAudio(voiceId, text) {
        const response = await axios.post(`${this.baseURL}/generations`, {
            voice_id: voiceId,
            script_text: text
        });
        return response.data;
    }
    
    // Payments
    async createCheckoutSession(planId) {
        const response = await axios.post(`${this.baseURL}/payments/create-checkout-session`, {
            plan_id: planId
        });
        return response.data;
    }
}

// Global API Instance
window.VoiceForgeAPI = new VoiceForgeAPI();
```

### Real-time Updates
```javascript
// WebSocket Connection (Future Enhancement)
class RealtimeService {
    constructor() {
        this.ws = null;
        this.reconnectAttempts = 0;
        this.maxReconnectAttempts = 5;
    }
    
    connect() {
        this.ws = new WebSocket(`ws://localhost:8002/ws`);
        
        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.reconnectAttempts = 0;
        };
        
        this.ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
        };
        
        this.ws.onclose = () => {
            if (this.reconnectAttempts < this.maxReconnectAttempts) {
                this.reconnectAttempts++;
                setTimeout(() => this.connect(), 1000 * this.reconnectAttempts);
            }
        };
    }
    
    handleMessage(data) {
        switch(data.type) {
            case 'voice_cloned':
                this.updateVoiceStatus(data.voice_id, 'completed');
                break;
            case 'audio_generated':
                this.updateGenerationStatus(data.generation_id, 'completed');
                break;
            case 'payment_completed':
                this.updateUserPlan(data.user_id, data.plan);
                break;
        }
    }
}
```

---

This documentation provides a comprehensive overview of all API connections and services in the VoiceForge AI platform, showing how different components interact with each other and with external services.
