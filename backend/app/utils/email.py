"""
Email service for sending OTP verification emails
"""
import smtplib
import random
import string
from datetime import datetime, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database import User

settings = get_settings()


class EmailService:
    @staticmethod
    def generate_otp(length=6):
        """Generate a random 6-digit OTP code"""
        return ''.join(random.choices(string.digits, k=length))
    
    @staticmethod
    def send_otp_email(to_email: str, otp_code: str, full_name: str = "User"):
        """Send OTP verification email to user"""
        try:
            # For production, use real SMTP credentials from settings
            # For now, we'll print to console in development
            
            smtp_host = getattr(settings, 'smtp_host', None)
            smtp_port = getattr(settings, 'smtp_port', 587)
            smtp_username = getattr(settings, 'smtp_username', None)
            smtp_password = getattr(settings, 'smtp_password', None)
            from_email = getattr(settings, 'from_email', 'noreply@voiceforge.ai')
            
            # If SMTP is not configured, just log to console (development mode)
            if not all([smtp_host, smtp_username, smtp_password]):
                print(f"\n{'='*60}")
                print(f"OTP EMAIL (Development Mode)")
                print(f"{'='*60}")
                print(f"To: {to_email}")
                print(f"Name: {full_name}")
                print(f"OTP Code: {otp_code}")
                print(f"{'='*60}\n")
                return True
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "VoiceForge AI - Email Verification Code"
            message["From"] = from_email
            message["To"] = to_email
            
            # HTML email template
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #6366f1; margin: 0;">VoiceForge AI</h1>
                        <p style="color: #666; margin: 5px 0;">Email Verification</p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px;">Hello <strong>{full_name}</strong>,</p>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        Thank you for signing up with VoiceForge AI. To complete your registration and verify your email address, please use the following verification code:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                        <span style="font-size: 32px; font-weight: bold; color: #6366f1; letter-spacing: 5px;">{otp_code}</span>
                    </div>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        This code will expire in <strong>10 minutes</strong>. Please do not share this code with anyone.
                    </p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center;">
                        <p>If you did not request this verification, please ignore this email.</p>
                        <p>© 2026 VoiceForge AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            # Attach HTML content
            html_part = MIMEText(html, "html")
            message.attach(html_part)
            
            # Send email via SMTP
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(from_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            # In development, still return True so user can see OTP in console
            return True
    
    @staticmethod
    def send_login_otp(to_email: str, otp_code: str, full_name: str = "User"):
        """Send OTP for login verification"""
        try:
            smtp_host = getattr(settings, 'smtp_host', None)
            smtp_port = getattr(settings, 'smtp_port', 587)
            smtp_username = getattr(settings, 'smtp_username', None)
            smtp_password = getattr(settings, 'smtp_password', None)
            from_email = getattr(settings, 'from_email', 'noreply@voiceforge.ai')
            
            # If SMTP is not configured, just log to console (development mode)
            if not all([smtp_host, smtp_username, smtp_password]):
                print(f"\n{'='*60}")
                print(f"LOGIN OTP EMAIL (Development Mode)")
                print(f"{'='*60}")
                print(f"To: {to_email}")
                print(f"Name: {full_name}")
                print(f"OTP Code: {otp_code}")
                print(f"{'='*60}\n")
                return True
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "VoiceForge AI - Login Verification Code"
            message["From"] = from_email
            message["To"] = to_email
            
            # HTML email template
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #6366f1; margin: 0;">VoiceForge AI</h1>
                        <p style="color: #666; margin: 5px 0;">Login Verification</p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px;">Hello <strong>{full_name}</strong>,</p>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        We received a login request for your account. To verify it's you, please use the following code:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0; padding: 20px; background-color: #f8f9fa; border-radius: 8px;">
                        <span style="font-size: 32px; font-weight: bold; color: #6366f1; letter-spacing: 5px;">{otp_code}</span>
                    </div>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        This code will expire in <strong>10 minutes</strong>. If you didn't request this login, please secure your account immediately.
                    </p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center;">
                        <p>© 2026 VoiceForge AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_part = MIMEText(html, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(from_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return True  # Return True in development mode

    @staticmethod
    def generate_reset_token(length=32):
        """Generate a random password reset token"""
        import secrets
        return secrets.token_urlsafe(length)
    
    @staticmethod
    def send_password_reset_email(to_email: str, reset_token: str, full_name: str = "User"):
        """Send password reset email with token"""
        try:
            smtp_host = getattr(settings, 'smtp_host', None)
            smtp_port = getattr(settings, 'smtp_port', 587)
            smtp_username = getattr(settings, 'smtp_username', None)
            smtp_password = getattr(settings, 'smtp_password', None)
            from_email = getattr(settings, 'from_email', 'noreply@voiceforge.ai')
            
            reset_url = f"{settings.frontend_url}/reset-password?token={reset_token}"
            
            # If SMTP is not configured, just log to console (development mode)
            if not all([smtp_host, smtp_username, smtp_password]):
                print(f"\n{'='*60}")
                print(f"PASSWORD RESET EMAIL (Development Mode)")
                print(f"{'='*60}")
                print(f"To: {to_email}")
                print(f"Name: {full_name}")
                print(f"Reset Token: {reset_token}")
                print(f"Reset URL: {reset_url}")
                print(f"{'='*60}\n")
                return True
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = "VoiceForge AI - Password Reset Request"
            message["From"] = from_email
            message["To"] = to_email
            
            # HTML email template
            html = f"""
            <html>
            <body style="font-family: Arial, sans-serif; background-color: #f4f4f4; padding: 20px;">
                <div style="max-width: 600px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 10px; box-shadow: 0 2px 10px rgba(0,0,0,0.1);">
                    <div style="text-align: center; margin-bottom: 30px;">
                        <h1 style="color: #6366f1; margin: 0;">VoiceForge AI</h1>
                        <p style="color: #666; margin: 5px 0;">Password Reset</p>
                    </div>
                    
                    <p style="color: #333; font-size: 16px;">Hello <strong>{full_name}</strong>,</p>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        We received a request to reset your password. Click the button below to reset your password:
                    </p>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{reset_url}" style="display: inline-block; padding: 15px 30px; background-color: #6366f1; color: white; text-decoration: none; border-radius: 8px; font-weight: bold;">Reset Password</a>
                    </div>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        Or copy and paste this link into your browser:<br>
                        <code style="background-color: #f8f9fa; padding: 10px; border-radius: 4px; word-break: break-all;">{reset_url}</code>
                    </p>
                    
                    <p style="color: #555; font-size: 14px; line-height: 1.6;">
                        This link will expire in <strong>1 hour</strong>. If you didn't request this password reset, please ignore this email.
                    </p>
                    
                    <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee; color: #999; font-size: 12px; text-align: center;">
                        <p>© 2026 VoiceForge AI. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            html_part = MIMEText(html, "html")
            message.attach(html_part)
            
            # Send email
            with smtplib.SMTP(smtp_host, smtp_port) as server:
                server.starttls()
                server.login(smtp_username, smtp_password)
                server.sendmail(from_email, to_email, message.as_string())
            
            return True
            
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return True  # Return True in development mode


# Initialize email service
email_service = EmailService()
