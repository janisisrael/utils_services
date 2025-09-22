"""
Professional Email Templates for Utils_services Email Service
Copied and adapted from Phase1 email templates
"""

from datetime import datetime
from typing import Dict, Any, Optional

def get_base_template():
    """
    Returns the base HTML template for all emails
    """
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <title>{title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                background-color: #f9f9f9;
                margin: 0;
                padding: 0;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                padding: 20px;
                border-radius: 5px;
                box-shadow: 0 0 10px rgba(0,0,0,0.1);
            }}
            .header {{
                text-align: center;
                padding: 10px 0;
                border-bottom: 1px solid #eee;
            }}
            .header img {{
                max-height: 80px;
            }}
            .content {{
                padding: 20px 0;
            }}
            .footer {{
                text-align: center;
                padding: 15px 0;
                font-size: 0.8em;
                color: #777;
                border-top: 1px solid #eee;
            }}
            .button {{
                display: inline-block;
                background-color: #4CAF50;
                color: white;
                text-align: center;
                padding: 10px 20px;
                text-decoration: none;
                border-radius: 4px;
                font-weight: bold;
                margin: 20px 0;
            }}
            .highlight {{
                background-color: #fff9c4;
                padding: 10px;
                border-radius: 5px;
                margin: 15px 0;
            }}
            .highlight.success {{
                background-color: #d4edda;
                border: 1px solid #c3e6cb;
                color: #155724;
            }}
            .highlight.warning {{
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                color: #856404;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 15px 0;
            }}
            table, th, td {{
                border: 1px solid #ddd;
            }}
            th, td {{
                text-align: left;
                padding: 12px;
            }}
            th {{
                background-color: #f2f2f2;
            }}
            .text-center {{
                text-align: center;
            }}
            .text-success {{
                color: #4CAF50;
            }}
            .text-warning {{
                color: #ff9800;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <img src="https://www.thesantris.com/logo.png" alt="Lotto Command Center">
                <h1>{header}</h1>
            </div>
            <div class="content">
                {content}
            </div>
            <div class="footer">
                <p>© {year} The Santris - Lotto Command Center. All rights reserved.</p>
                <p>If you have questions, please contact our <a href="mailto:support@thesantris.com">support team</a>.</p>
                <p>
                    <a href="{unsubscribe_link}">Manage notification preferences</a> |
                    <a href="{privacy_link}">Privacy Policy</a>
                </p>
            </div>
        </div>
    </body>
    </html>
    """

def get_winning_notification_template(user_name: str, game: str, draw_date: str, 
                                     ticket_number: str, matched_numbers: list, 
                                     prize_amount: str, ticket_id: str, 
                                     frontend_url: str = "https://www.thesantris.com") -> str:
    """
    Generate an email template for winning ticket notification
    
    Args:
        user_name: User's name
        game: Game name
        draw_date: Draw date
        ticket_number: Ticket number
        matched_numbers: List of matched numbers
        prize_amount: Prize amount
        ticket_id: Ticket ID
        frontend_url: Frontend URL for links
        
    Returns:
        HTML email content
    """
    base = get_base_template()
    
    # Format the matched numbers as a comma-separated string
    matched_str = ", ".join(map(str, matched_numbers)) if matched_numbers else "None"
    match_count = len(matched_numbers) if matched_numbers else 0
    
    # Create content for winning notification
    content = f"""
    <h2>🎉 Congratulations {user_name}!</h2>
    
    <div class="highlight success">
        <h3 class="text-success">You've won in {game}!</h3>
        <p>Your ticket matched <strong>{match_count} numbers</strong> in the {draw_date} draw.</p>
    </div>
    
    <h3>🏆 Winning Details:</h3>
    <table>
        <tr>
            <th>Game</th>
            <td>{game}</td>
        </tr>
        <tr>
            <th>Draw Date</th>
            <td>{draw_date}</td>
        </tr>
        <tr>
            <th>Ticket Number</th>
            <td><strong>{ticket_number}</strong></td>
        </tr>
        <tr>
            <th>Matched Numbers</th>
            <td><strong>{matched_str}</strong></td>
        </tr>
        <tr>
            <th>Prize Amount</th>
            <td class="text-success"><strong>{prize_amount}</strong></td>
        </tr>
    </table>
    
    <p class="text-center">
        <a href="{frontend_url}/tickets/{ticket_id}" class="button">🎫 View Your Winning Ticket</a>
    </p>
    
    <p>🎯 <strong>Next Steps:</strong></p>
    <ul>
        <li>Login to your account to view full details</li>
        <li>Follow the claim instructions for your prize</li>
        <li>Contact support if you need assistance</li>
    </ul>
    
    <p>Thank you for playing with Lotto Command Center!</p>
    """
    
    current_year = datetime.now().year
    
    return base.format(
        title=f"🎉 You've Won in {game}!",
        header="🏆 Winning Ticket Alert",
        content=content,
        year=current_year,
        unsubscribe_link=f"{frontend_url}/preferences",
        privacy_link=f"{frontend_url}/privacy"
    )

def get_subscription_expiry_template(user_name: str, expiry_date: str, 
                                   days_remaining: int, subscription_type: str,
                                   frontend_url: str = "https://www.thesantris.com") -> str:
    """
    Generate an email template for subscription expiry notification
    """
    base = get_base_template()
    
    urgency_class = "warning" if days_remaining <= 7 else ""
    urgency_emoji = "⚠️" if days_remaining <= 7 else "📅"
    
    content = f"""
    <h2>Hello {user_name},</h2>
    
    <div class="highlight {urgency_class}">
        <h3>{urgency_emoji} Your {subscription_type} Subscription is Expiring Soon</h3>
        <p>Your subscription will expire on <strong>{expiry_date}</strong> 
           (<strong>{days_remaining} days remaining</strong>).</p>
    </div>
    
    <h3>📋 Subscription Details:</h3>
    <table>
        <tr>
            <th>Subscription Type</th>
            <td>{subscription_type}</td>
        </tr>
        <tr>
            <th>Expiry Date</th>
            <td>{expiry_date}</td>
        </tr>
        <tr>
            <th>Days Remaining</th>
            <td><strong>{days_remaining}</strong></td>
        </tr>
    </table>
    
    <p class="text-center">
        <a href="{frontend_url}/subscription/renew" class="button">🔄 Renew Now</a>
    </p>
    
    <p>💎 <strong>Don't miss out on premium features:</strong></p>
    <ul>
        <li>Advanced lottery analytics</li>
        <li>Winner notifications</li>
        <li>Priority customer support</li>
        <li>Exclusive draws and promotions</li>
    </ul>
    
    <p>Renew today to maintain uninterrupted access to all premium features!</p>
    """
    
    current_year = datetime.now().year
    
    return base.format(
        title="Your Subscription is Expiring Soon",
        header="📅 Subscription Renewal Notice",
        content=content,
        year=current_year,
        unsubscribe_link=f"{frontend_url}/preferences",
        privacy_link=f"{frontend_url}/privacy"
    )

def get_new_draw_results_template(user_name: str, game: str, draw_date: str, 
                                 winning_numbers: str, jackpot_amount: str,
                                 frontend_url: str = "https://www.thesantris.com") -> str:
    """
    Generate an email template for new draw results notification
    """
    base = get_base_template()
    
    content = f"""
    <h2>Hello {user_name},</h2>
    
    <div class="highlight">
        <h3>🎲 New {game} Results Available</h3>
        <p>The results for the <strong>{draw_date}</strong> draw have been announced.</p>
    </div>
    
    <h3>📊 Draw Details:</h3>
    <table>
        <tr>
            <th>Game</th>
            <td>{game}</td>
        </tr>
        <tr>
            <th>Draw Date</th>
            <td>{draw_date}</td>
        </tr>
        <tr>
            <th>Winning Numbers</th>
            <td><strong style="font-size: 1.2em; color: #4CAF50;">{winning_numbers}</strong></td>
        </tr>
        <tr>
            <th>Jackpot Amount</th>
            <td class="text-success"><strong>{jackpot_amount}</strong></td>
        </tr>
    </table>
    
    <p class="text-center">
        <a href="{frontend_url}/results" class="button">🔍 View All Results</a>
    </p>
    
    <p>🎯 <strong>Check Your Tickets:</strong></p>
    <p>Login to your account to see if any of your tickets match these winning numbers!</p>
    
    <p class="text-center">
        <a href="{frontend_url}/tickets" class="button" style="background-color: #2196F3;">🎫 Check My Tickets</a>
    </p>
    """
    
    current_year = datetime.now().year
    
    return base.format(
        title=f"New {game} Results Available",
        header="🎲 Lottery Results Update",
        content=content,
        year=current_year,
        unsubscribe_link=f"{frontend_url}/preferences",
        privacy_link=f"{frontend_url}/privacy"
    )

# Template registry for easy access
EMAIL_TEMPLATES = {
    'winner_notification': {
        'function': get_winning_notification_template,
        'required_fields': ['user_name', 'game', 'draw_date', 'ticket_number', 'matched_numbers', 'prize_amount', 'ticket_id'],
        'optional_fields': ['frontend_url']
    },
    'subscription_expiry': {
        'function': get_subscription_expiry_template,
        'required_fields': ['user_name', 'expiry_date', 'days_remaining', 'subscription_type'],
        'optional_fields': ['frontend_url']
    },
    'draw_results': {
        'function': get_new_draw_results_template,
        'required_fields': ['user_name', 'game', 'draw_date', 'winning_numbers', 'jackpot_amount'],
        'optional_fields': ['frontend_url']
    }
}

def render_template(template_name: str, data: Dict[str, Any]) -> Optional[str]:
    """
    Render an email template with provided data
    
    Args:
        template_name: Name of the template to render
        data: Data to populate the template
        
    Returns:
        Rendered HTML email content or None if error
    """
    template_info = EMAIL_TEMPLATES.get(template_name)
    if not template_info:
        return None
    
    # Check required fields
    required_fields = template_info['required_fields']
    missing_fields = [field for field in required_fields if field not in data]
    if missing_fields:
        raise ValueError(f"Missing required fields: {', '.join(missing_fields)}")
    
    # Set default values for optional fields
    if 'frontend_url' not in data:
        data['frontend_url'] = 'https://www.thesantris.com'
    
    # Render template
    template_function = template_info['function']
    return template_function(**data)

def get_template_info() -> Dict[str, Dict[str, Any]]:
    """Get information about all available templates"""
    return {
        name: {
            'required_fields': info['required_fields'],
            'optional_fields': info['optional_fields']
        }
        for name, info in EMAIL_TEMPLATES.items()
    }
