# VoiceForge AI - Render Deployment Guide

## 🚀 Deploy to Render.com

This guide will help you deploy VoiceForge AI to Render.com in just a few minutes.

## 📋 Prerequisites

1. **Render Account**: Sign up at [render.com](https://render.com)
2. **GitHub/GitLab Account**: To connect your repository
3. **Repository**: Push your code to GitHub/GitLab

## 🎯 Quick Deploy (Blue Print)

### Step 1: Prepare Your Repository

```bash
# Make sure all Render files are committed
git add render.yaml Dockerfile.render render-start.sh
git commit -m "Add Render deployment configuration"
git push origin main
```

### Step 2: Create Blueprint on Render

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Click **"New +"** → **"Blueprint"**
3. Connect your GitHub/GitLab repository
4. Select the repository with VoiceForge AI
5. Render will automatically read `render.yaml` and create services

### Step 3: Configure Environment Variables

After the blueprint is created, add these environment variables in Render dashboard:

#### Required API Keys:
```bash
# Voice Services (Choose at least one)
ELEVENLABS_API_KEY=your_elevenlabs_api_key
FISH_AUDIO_API_KEY=your_fish_audio_key
RESEMBLE_API_KEY=your_resemble_ai_key

# Stripe Payment (Required for payments)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_PUBLISHABLE_KEY=pk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...

# Email Service (Required for OTP)
SMTP_USERNAME=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

### Step 4: Deploy!

Render will automatically:
- ✅ Build the Docker image
- ✅ Create PostgreSQL database
- ✅ Deploy the web service
- ✅ Run database migrations
- ✅ Start the application

## 🔧 Manual Deploy (Alternative)

If you prefer manual setup:

### 1. Create PostgreSQL Database

1. Go to Render Dashboard
2. Click **"New +"** → **"PostgreSQL"**
3. Name: `voiceforge-db`
4. Plan: Starter (or higher)
5. Create Database

### 2. Create Web Service

1. Click **"New +"** → **"Web Service"**
2. Connect your repository
3. Configure:
   - **Name**: `voiceforge-ai`
   - **Runtime**: Docker
   - **Dockerfile Path**: `./Dockerfile.render`
   - **Plan**: Standard
4. Add Environment Variables (from above)
5. Create Web Service

### 3. Add Disk (For File Storage)

1. Go to your Web Service
2. Click **"Disks"**
3. Add Disk:
   - **Name**: `voiceforge-data`
   - **Mount Path**: `/data`
   - **Size**: 10 GB
4. Save

## 🌐 Access Your Deployed App

After deployment, your app will be available at:

- **Main URL**: `https://voiceforge-ai.onrender.com`
- **API Docs**: `https://voiceforge-ai.onrender.com/docs`
- **Health Check**: `https://voiceforge-ai.onrender.com/health`

## 👤 Default Admin Login

After first deployment:
- **Email**: `admin@voiceforge.ai`
- **Password**: `admin123`

**⚠️ Important**: Change the admin password after first login!

## 🔐 Security Best Practices

### 1. Change Admin Password

Login as admin and immediately change the default password.

### 2. Update JWT Secret

Render automatically generates a JWT secret. You can regenerate it in the dashboard.

### 3. Configure Custom Domain (Optional)

1. Go to Web Service Settings
2. Click **"Custom Domains"**
3. Add your domain
4. Follow DNS configuration instructions

### 4. Enable SSL

Render automatically provides SSL certificates for `.onrender.com` domains and custom domains.

## 💰 Pricing on Render

### Free Tier (Not Recommended for Production)
- Web Service: 512 MB RAM, 0.1 CPU
- Database: Not available
- Disk: Not available
- **Note**: Free tier spins down after 15 minutes of inactivity

### Starter Tier (Recommended for Testing)
- Web Service: $7/month
- Database: $7/month
- Disk: $0.25/GB/month
- Total: ~$15/month

### Standard Tier (Recommended for Production)
- Web Service: $25/month
- Database: $15/month
- Disk: $0.25/GB/month
- Total: ~$42/month

## 🛠️ Troubleshooting

### Issue 1: Build Fails

**Solution**:
```bash
# Check Dockerfile.render exists
cat Dockerfile.render

# Verify requirements-demo.txt exists
cat requirements-demo.txt

# Check render.yaml syntax
# Use online YAML validator
```

### Issue 2: Database Connection Error

**Solution**:
1. Check DATABASE_URL environment variable
2. Verify database is created and running
3. Check database connection string format

### Issue 3: File Upload Fails

**Solution**:
1. Verify disk is mounted at `/data`
2. Check disk permissions
3. Ensure UPLOAD_DIR is set to `/data/uploads`

### Issue 4: Static Files Not Loading

**Solution**:
1. Check static files are in backend/static
2. Verify app.mount in main.py
3. Check network tab in browser dev tools

### Issue 5: API Keys Not Working

**Solution**:
1. Verify API keys are added in Render dashboard
2. Check key format (no extra spaces)
3. Test keys locally first
4. Redeploy after adding keys

## 📊 Monitoring on Render

### 1. Logs

View logs in Render dashboard:
- Build logs
- Runtime logs
- Error logs

### 2. Metrics

Monitor:
- CPU usage
- Memory usage
- Disk usage
- Request metrics

### 3. Alerts

Set up alerts for:
- High CPU usage
- Memory limits
- Disk full
- Service down

## 🔄 Updates and Maintenance

### Update Code

```bash
# Make changes
git add .
git commit -m "Update feature X"
git push origin main

# Render automatically redeploys
```

### Database Migrations

```bash
# Connect to Render PostgreSQL
# Use Render dashboard SQL shell
# Or connect with psql using connection string
```

### Backup Database

1. Go to PostgreSQL dashboard
2. Click **"Backup"**
3. Download backup file
4. Store securely

## 🎭 Demo Mode on Render

To deploy in demo mode (without API keys):

1. Set environment variables:
```bash
DEMO_MODE=true
MOCK_API_CALLS=true
SKIP_EXTERNAL_APIS=true
```

2. Redeploy

The app will work with mock data and pre-generated samples.

## 📞 Support

### Render Support
- [Render Documentation](https://render.com/docs)
- [Render Community](https://community.render.com)
- [Render Status](https://status.render.com)

### VoiceForge AI Support
- Check `PROJECT_DOCUMENTATION.md`
- Review `DEPLOYMENT_GUIDE.md`
- GitHub Issues

## 🎉 Success!

Your VoiceForge AI is now deployed on Render and accessible worldwide!

**Next Steps**:
1. Test all features
2. Add real API keys for production
3. Configure custom domain
4. Set up monitoring and alerts
5. Share with users!

---

**Deploy Status**: ✅ Ready for Render
**Estimated Deploy Time**: 5-10 minutes
**Estimated Cost**: $15-42/month
