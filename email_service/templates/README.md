# 📧 Email Templates Directory

This folder contains all HTML email templates used across Phase 1 and Phase 2.

## 📁 Structure

```
templates/
├── README.md                    # This file
├── welcome_email.html          # Welcome email after user registration
├── otp_verification.html       # OTP verification email (future)
├── password_reset.html         # Password reset email (future)
├── ticket_win_notification.html # Winning ticket notification (future)
├── subscription_confirm.html   # Subscription confirmation (future)
└── ...more templates as needed
```

## �� Template Guidelines

### Naming Convention
- Use lowercase with underscores: `template_name.html`
- Be descriptive and specific

### Placeholders
Templates should use simple string placeholders that can be replaced with `.replace()`:
- User names: `Test User` → replaced with actual name
- Emails: `test@email.com` → replaced with actual email
- Other data: Use descriptive placeholder text

### Design Standards
- **Mobile-first**: Responsive design
- **Max width**: 600px for email clients
- **Inline CSS**: Email clients strip `<style>` tags
- **Color scheme**: Match Lotto Command Center branding
- **Accessibility**: Alt text for images, good contrast

## 🔧 Usage

### From API Gateway (Phase 1)
```python
template_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), "..", "..", "Utils_services", 
    "email_service", "templates", "template_name.html"
))

with open(template_path, 'r', encoding='utf-8') as f:
    html_content = f.read()

# Replace placeholders
html_content = html_content.replace('Test User', user_name)
html_content = html_content.replace('test@email.com', email)
```

### From Phase 2
```python
template_path = os.path.join(
    "Utils_services", "email_service", "templates", "template_name.html"
)
# Same replacement logic
```

## 📝 Available Templates

| Template | Purpose | Status | Placeholders |
|----------|---------|--------|--------------|
| `welcome_email.html` | New user registration | ✅ Active | `Test User`, `test@email.com` |
| More coming soon... | | | |

## 🚀 Adding New Templates

1. Create HTML file in this folder
2. Follow design standards above
3. Use clear placeholder text
4. Update this README
5. Test with email microservice

---

**Last Updated:** 2025-10-12  
**Maintained by:** Swordfish Team
