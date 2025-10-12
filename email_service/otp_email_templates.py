"""
Professional OTP Email Templates for The Santris Application
"""

def get_otp_email_template(otp_code, user_name=None, is_password_reset=False, expires_in_minutes=10):
    """
    Generate a professional OTP email template
    
    Args:
        otp_code (str): The 6-digit OTP code
        user_name (str): User's name (optional)
        is_password_reset (bool): Whether this is for password reset
        expires_in_minutes (int): OTP expiration time in minutes
        
    Returns:
        str: HTML email content
    """
    
    # Determine email type and content
    if is_password_reset:
        email_type = "Password Reset"
        action_text = "reset your password"
        subject_context = "password reset"
    else:
        email_type = "Account Verification"
        action_text = "verify your account"
        subject_context = "account verification"
    
    # Greeting with or without name
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>The Santris - {email_type}</title>
        <style>
            /* Reset and base styles */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8fafc;
                margin: 0;
                padding: 20px 0;
            }}
            
            /* Container */
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                overflow: hidden;
            }}
            
            /* Header */
            .header {{
                background: linear-gradient(135deg, #1e3a8a 0%, #1f3d8f 100%);
                padding: 40px 30px;
                text-align: center;
                color: white;
            }}
            
            .logo {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
                letter-spacing: -0.5px;
            }}
            
            .subtitle {{
                font-size: 16px;
                opacity: 0.9;
                font-weight: 400;
            }}
            
            /* Content */
            .content {{
                padding: 40px 30px;
            }}
            
            .greeting {{
                font-size: 18px;
                margin-bottom: 20px;
                color: #1f2937;
            }}
            
            .message {{
                font-size: 16px;
                color: #4b5563;
                margin-bottom: 30px;
                line-height: 1.7;
            }}
            
            /* OTP Code Box */
            .otp-container {{
                text-align: center;
                margin: 30px 0;
            }}
            
            .otp-label {{
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 600;
            }}
            
            .otp-code {{
                font-size: 32px;
                font-weight: 700;
                color: #1e3a8a;
                background: #f1f5f9;
                padding: 20px;
                border-radius: 8px;
                letter-spacing: 8px;
                border: 2px solid #e2e8f0;
                font-family: 'Courier New', monospace;
            }}
            
            /* Important Info */
            .important-info {{
                background: #fef3c7;
                border: 1px solid #f59e0b;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
            }}
            
            .important-info h3 {{
                color: #92400e;
                font-size: 16px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .important-info p {{
                color: #92400e;
                font-size: 14px;
                margin: 0;
            }}
            
            .warning-icon {{
                width: 20px;
                height: 20px;
                fill: #f59e0b;
            }}
            
            /* Footer */
            .footer {{
                background: #f8fafc;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #e2e8f0;
            }}
            
            .footer-text {{
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 15px;
            }}
            
            .footer-links {{
                margin-top: 20px;
            }}
            
            .footer-links a {{
                color: #1e3a8a;
                text-decoration: none;
                margin: 0 10px;
                font-size: 14px;
            }}
            
            .footer-links a:hover {{
                text-decoration: underline;
            }}
            
            /* Responsive */
            @media (max-width: 600px) {{
                .email-container {{
                    margin: 10px;
                    border-radius: 8px;
                }}
                
                .header, .content, .footer {{
                    padding: 20px;
                }}
                
                .otp-code {{
                    font-size: 24px;
                    letter-spacing: 4px;
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- Header -->
            <div class="header">
                <div class="logo">The Santris</div>
                <div class="subtitle">Premium Lottery Management Platform</div>
            </div>
            
            <!-- Content -->
            <div class="content">
                <div class="greeting">{greeting}</div>
                
                <div class="message">
                    We received a request to {action_text} for your The Santris account. 
                    To proceed, please use the verification code below:
                </div>
                
                <!-- OTP Code -->
                <div class="otp-container">
                    <div class="otp-label">Verification Code</div>
                    <div class="otp-code">{otp_code}</div>
                </div>
                
                <!-- Important Information -->
                <div class="important-info">
                    <h3>
                        <svg class="warning-icon" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                        Important Information
                    </h3>
                    <p>• This code will expire in <strong>{expires_in_minutes} minutes</strong></p>
                    <p>• Never share this code with anyone</p>
                    <p>• If you didn't request this code, please ignore this email</p>
                </div>
                
                <div class="message">
                    If you have any questions or need assistance, please don't hesitate to contact our support team.
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <div class="footer-text">
                    © 2025 The Santris. All rights reserved.
                </div>
                <div class="footer-links">
                    <a href="https://thesantris.com/privacy">Privacy Policy</a>
                    <a href="https://thesantris.com/terms">Terms of Service</a>
                    <a href="https://thesantris.com/support">Support</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """


def get_otp_plain_text(otp_code, user_name=None, is_password_reset=False, expires_in_minutes=10):
    """
    Generate plain text version of OTP email for email clients that don't support HTML
    
    Args:
        otp_code (str): The 6-digit OTP code
        user_name (str): User's name (optional)
        is_password_reset (bool): Whether this is for password reset
        expires_in_minutes (int): OTP expiration time in minutes
        
    Returns:
        str: Plain text email content
    """
    
    # Determine email type and content
    if is_password_reset:
        email_type = "Password Reset"
        action_text = "reset your password"
    else:
        email_type = "Account Verification"
        action_text = "verify your account"
    
    # Greeting with or without name
    greeting = f"Hello {user_name}," if user_name else "Hello,"
    
    return f"""{greeting}

We received a request to {action_text} for your The Santris account.

VERIFICATION CODE: {otp_code}

IMPORTANT INFORMATION:
- This code will expire in {expires_in_minutes} minutes
- Never share this code with anyone
- If you didn't request this code, please ignore this email

If you have any questions or need assistance, please contact our support team.

Best regards,
The Santris Team

---
© 2025 The Santris. All rights reserved.
Support: https://thesantris.com/support
"""


def get_welcome_otp_template(otp_code, user_name, expires_in_minutes=10):
    """
    Generate a welcome OTP email template for new user registration
    
    Args:
        otp_code (str): The 6-digit OTP code
        user_name (str): User's name
        expires_in_minutes (int): OTP expiration time in minutes
        
    Returns:
        str: HTML email content
    """
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>The Santris - Welcome & Verification</title>
        <style>
            /* Reset and base styles */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8fafc;
                margin: 0;
                padding: 20px 0;
            }}
            
            /* Container */
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                overflow: hidden;
            }}
            
            /* Header */
            .header {{
                background: linear-gradient(135deg, #1e3a8a 0%, #1f3d8f 100%);
                padding: 40px 30px;
                text-align: center;
                color: white;
            }}
            
            .logo {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
                letter-spacing: -0.5px;
            }}
            
            .subtitle {{
                font-size: 16px;
                opacity: 0.9;
                font-weight: 400;
            }}
            
            /* Content */
            .content {{
                padding: 40px 30px;
            }}
            
            .greeting {{
                font-size: 18px;
                margin-bottom: 20px;
                color: #1f2937;
            }}
            
            .welcome-message {{
                font-size: 16px;
                color: #4b5563;
                margin-bottom: 30px;
                line-height: 1.7;
            }}
            
            .welcome-highlight {{
                background: #ecfdf5;
                border: 1px solid #10b981;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
            }}
            
            .welcome-highlight h3 {{
                color: #065f46;
                font-size: 16px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .welcome-highlight p {{
                color: #065f46;
                font-size: 14px;
                margin: 0;
            }}
            
            .check-icon {{
                width: 20px;
                height: 20px;
                fill: #10b981;
            }}
            
            /* OTP Code Box */
            .otp-container {{
                text-align: center;
                margin: 30px 0;
            }}
            
            .otp-label {{
                font-size: 14px;
                color: #6b7280;
                margin-bottom: 15px;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                font-weight: 600;
            }}
            
            .otp-code {{
                font-size: 32px;
                font-weight: 700;
                color: #1e3a8a;
                background: #f1f5f9;
                padding: 20px;
                border-radius: 8px;
                letter-spacing: 8px;
                border: 2px solid #e2e8f0;
                font-family: 'Courier New', monospace;
            }}
            
            /* Important Info */
            .important-info {{
                background: #fef3c7;
                border: 1px solid #f59e0b;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
            }}
            
            .important-info h3 {{
                color: #92400e;
                font-size: 16px;
                margin-bottom: 10px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .important-info p {{
                color: #92400e;
                font-size: 14px;
                margin: 0;
            }}
            
            .warning-icon {{
                width: 20px;
                height: 20px;
                fill: #f59e0b;
            }}
            
            /* Footer */
            .footer {{
                background: #f8fafc;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #e2e8f0;
            }}
            
            .footer-text {{
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 15px;
            }}
            
            .footer-links {{
                margin-top: 20px;
            }}
            
            .footer-links a {{
                color: #1e3a8a;
                text-decoration: none;
                margin: 0 10px;
                font-size: 14px;
            }}
            
            .footer-links a:hover {{
                text-decoration: underline;
            }}
            
            /* Responsive */
            @media (max-width: 600px) {{
                .email-container {{
                    margin: 10px;
                    border-radius: 8px;
                }}
                
                .header, .content, .footer {{
                    padding: 20px;
                }}
                
                .otp-code {{
                    font-size: 24px;
                    letter-spacing: 4px;
                    padding: 15px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- Header -->
            <div class="header">
                <div class="logo">The Santris</div>
                <div class="subtitle">Premium Lottery Management Platform</div>
            </div>
            
            <!-- Content -->
            <div class="content">
                <div class="greeting">Welcome to The Santris, {user_name}!</div>
                
                <div class="welcome-message">
                    Thank you for joining The Santris! We're excited to have you as part of our community. 
                    To complete your registration and start using our premium lottery management features, 
                    please verify your email address using the code below:
                </div>
                
                <!-- Welcome Highlight -->
                <div class="welcome-highlight">
                    <h3>
                        <svg class="check-icon" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                        What You'll Get
                    </h3>
                    <p>• Advanced ticket scanning and management</p>
                    <p>• Real-time lottery results and notifications</p>
                    <p>• Premium analytics and insights</p>
                    <p>• Secure and reliable platform</p>
                </div>
                
                <!-- OTP Code -->
                <div class="otp-container">
                    <div class="otp-label">Verification Code</div>
                    <div class="otp-code">{otp_code}</div>
                </div>
                
                <!-- Important Information -->
                <div class="important-info">
                    <h3>
                        <svg class="warning-icon" viewBox="0 0 24 24">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                        </svg>
                        Important Information
                    </h3>
                    <p>• This code will expire in <strong>{expires_in_minutes} minutes</strong></p>
                    <p>• Never share this code with anyone</p>
                    <p>• Enter the code exactly as shown above</p>
                </div>
                
                <div class="welcome-message">
                    Once verified, you'll have full access to all The Santris features. 
                    We're here to help you make the most of your lottery experience!
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <div class="footer-text">
                    © 2025 The Santris. All rights reserved.
                </div>
                <div class="footer-links">
                    <a href="https://thesantris.com/privacy">Privacy Policy</a>
                    <a href="https://thesantris.com/terms">Terms of Service</a>
                    <a href="https://thesantris.com/support">Support</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """

def get_welcome_registration_template(user_name, email):
    """
    Generate welcome email template for new user after successful OTP verification
    
    Args:
        user_name (str): User's name
        email (str): User's email address
        
    Returns:
        str: HTML email content
    """
    from datetime import datetime
    
    return f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Welcome to Lotto Command Center!</title>
        <style>
            /* Reset and base styles */
            * {{
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }}
            
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f8fafc;
                margin: 0;
                padding: 20px 0;
            }}
            
            /* Container */
            .email-container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                border-radius: 12px;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
                overflow: hidden;
            }}
            
            /* Header */
            .header {{
                background-image: linear-gradient(195deg, #667eea 0%, #764ba2 100%) !important;
                padding: 20px;
                display: flex;
                align-items: center;
                gap: 15px;
                color: #ffffff;
                flex-direction: column;
                text-align: center;
            }}
            
            .logo {{
                font-size: 28px;
                font-weight: 700;
                margin-bottom: 10px;
                letter-spacing: -0.5px;
            }}
            
            .subtitle {{
                font-size: 16px;
                opacity: 0.9;
                font-weight: 400;
            }}
            
            /* Content */
            .content {{
                padding: 40px 30px;
            }}
            
            .greeting {{
                font-size: 22px;
                margin-bottom: 20px;
                color: #1f2937;
                font-weight: 600;
            }}
            
            .welcome-message {{
                font-size: 16px;
                color: #4b5563;
                margin-bottom: 30px;
                line-height: 1.7;
            }}
            
            .success-badge {{
                background: #ecfdf5;
                border: 2px solid #10b981;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
                text-align: center;
            }}
            
            .success-badge h2 {{
                color: #065f46;
                font-size: 24px;
                margin: 10px 0;
            }}
            
            .check-icon {{
                font-size: 48px;
            }}
            
            .welcome-highlight {{
                background: #f9fafb;
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
                margin: 30px 0;
            }}
            
            .welcome-highlight h3 {{
                color: #1f2937;
                font-size: 16px;
                margin-bottom: 15px;
                display: flex;
                align-items: center;
                gap: 8px;
            }}
            
            .welcome-highlight p {{
                color: #4b5563;
                font-size: 14px;
                margin: 8px 0;
                padding-left: 24px;
            }}
            
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, #10b981 0%, #059669 100%);
                color: white;
                padding: 15px 40px;
                text-decoration: none;
                border-radius: 8px;
                font-weight: 600;
                font-size: 16px;
                margin: 10px 5px;
            }}
            
            .promo-box {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border-radius: 8px;
                padding: 25px;
                margin: 30px 0;
                text-align: center;
            }}
            
            .promo-box h3 {{
                color: white;
                font-size: 20px;
                margin-bottom: 10px;
            }}
            
            .promo-price {{
                font-size: 36px;
                font-weight: 700;
                color: #fbbf24;
                margin: 10px 0;
            }}
            
            .account-details {{
                background: #f9fafb;
                border-left: 4px solid #10b981;
                padding: 15px;
                margin: 20px 0;
                font-size: 14px;
                color: #4b5563;
            }}
            
            /* Footer */
            .footer {{
                background: #f8fafc;
                padding: 30px;
                text-align: center;
                border-top: 1px solid #e2e8f0;
            }}
            
            .footer-text {{
                color: #6b7280;
                font-size: 14px;
                margin-bottom: 15px;
            }}
            
            .footer-links a {{
                color: #10b981;
                text-decoration: none;
                margin: 0 10px;
                font-size: 14px;
            }}
            
            /* Responsive */
            @media (max-width: 600px) {{
                .email-container {{
                    margin: 10px;
                    border-radius: 8px;
                }}
                
                .header, .content, .footer {{
                    padding: 20px;
                }}
                
                .greeting {{
                    font-size: 20px;
                }}
                
                .cta-button {{
                    display: block;
                    margin: 10px 0;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <!-- Header -->
            <div class="header">
                <div class="logo">🎉 Lotto Command Center</div>
                <div class="subtitle">Your Lottery Journey Starts Now!</div>
            </div>
            
            <!-- Content -->
            <div class="content">
                <div class="success-badge">
                    <div class="check-icon">✅</div>
                    <h2>Account Successfully Created!</h2>
                </div>
                
                <div class="greeting">Welcome aboard, {user_name}!</div>
                
                <div class="welcome-message">
                    Thank you for joining <strong>Lotto Command Center</strong>! Your account has been successfully verified and activated. 
                    We're thrilled to have you as part of our community where managing your lottery tickets becomes effortless and exciting!
                </div>
                
                <!-- Welcome Highlight -->
                <div class="welcome-highlight">
                    <h3>🚀 What You Can Do Now:</h3>
                    <p>📸 <strong>Scan Tickets</strong> - Use our advanced OCR technology to scan and save your tickets</p>
                    <p>🎯 <strong>Auto-Check Results</strong> - Automatic checking against latest draw results</p>
                    <p>🔔 <strong>Win Notifications</strong> - Get notified immediately when you win!</p>
                    <p>📊 <strong>Results & History</strong> - Access complete draw results and statistics</p>
                    <p>💎 <strong>Premium Features</strong> - Advanced analytics and insights</p>
                </div>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="https://www.thesantris.com/dashboard" class="cta-button">🎮 Go to Dashboard</a>
                </div>
                
                <!-- Promo Box -->
                <div class="promo-box">
                    <h3>🎁 Special Welcome Offer!</h3>
                    <p>Get your first month of Premium for just</p>
                    <div class="promo-price">$1</div>
                    <p style="color: white; opacity: 0.95;">Then only $5/month. Cancel anytime!</p>
                    <div style="margin-top: 15px;">
                        <a href="https://www.thesantris.com/subscription" style="color: white; background: rgba(255,255,255,0.2); padding: 10px 25px; border-radius: 6px; text-decoration: none; display: inline-block; font-weight: 600;">
                            💎 View Premium Plans
                        </a>
                    </div>
                </div>
                
                <div class="welcome-message" style="margin-top: 30px;">
                    <strong>Quick Start Guide:</strong><br>
                    1️⃣ Complete your profile settings<br>
                    2️⃣ Scan your first lottery ticket<br>
                    3️⃣ Enable push notifications<br>
                    4️⃣ Explore draw results and statistics
                </div>
                
                <div class="account-details">
                    <strong>Your Account Details:</strong><br>
                    📧 Email: {email}<br>
                    👤 Username: {user_name}<br>
                    📅 Joined: {datetime.now().strftime('%B %d, %Y')}
                </div>
                
                <div class="welcome-message" style="text-align: center; margin-top: 30px;">
                    Need help? Our support team is here for you!<br>
                    <a href="https://www.thesantris.com/support" style="color: #10b981; text-decoration: none; font-weight: 600;">📧 Contact Support</a>
                </div>
            </div>
            
            <!-- Footer -->
            <div class="footer">
                <div class="footer-text">
                    © 2025 Lotto Command Center. All rights reserved.
                </div>
                <div class="footer-links">
                    <a href="https://thesantris.com/privacy">Privacy Policy</a>
                    <a href="https://thesantris.com/terms">Terms of Service</a>
                    <a href="https://thesantris.com/support">Support</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
