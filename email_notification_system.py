"""
Email notification system for lead generation alerts and clinic communications.
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask import Blueprint, current_app
from datetime import datetime
from models import db, Clinic, Lead, Doctor
from sqlalchemy import text
import logging

email_bp = Blueprint('email', __name__)
logger = logging.getLogger(__name__)

# Email configuration
SMTP_SERVER = os.environ.get('SMTP_SERVER', 'smtp.gmail.com')
SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
FROM_EMAIL = os.environ.get('FROM_EMAIL', 'noreply@antidote.com')

def send_email(to_email, subject, html_body, text_body=None):
    """Send email using SMTP configuration."""
    try:
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = FROM_EMAIL
        msg['To'] = to_email
        
        # Add text and HTML parts
        if text_body:
            text_part = MIMEText(text_body, 'plain')
            msg.attach(text_part)
        
        html_part = MIMEText(html_body, 'html')
        msg.attach(html_part)
        
        # Send email
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USERNAME, SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email sent successfully to {to_email}")
        return True
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}: {e}")
        return False

def send_lead_notification_email(lead_id):
    """Send immediate notification to clinic when new lead is generated."""
    try:
        # Get lead and clinic details
        lead_data = db.session.execute(text("""
            SELECT 
                l.*,
                c.name as clinic_name,
                c.email as clinic_email,
                c.contact_number as clinic_phone,
                u.name as user_name,
                u.email as user_email,
                u.phone_number as user_phone,
                p.procedure_name,
                d.name as doctor_name
            FROM leads l
            JOIN clinics c ON l.clinic_id = c.id
            LEFT JOIN users u ON l.user_id = u.id
            LEFT JOIN procedures p ON l.procedure_id = p.id
            LEFT JOIN doctors d ON l.doctor_id = d.id
            WHERE l.id = :lead_id
        """), {"lead_id": lead_id}).fetchone()
        
        if not lead_data or not lead_data.clinic_email:
            logger.warning(f"No clinic email found for lead {lead_id}")
            return False
        
        # Generate email content
        subject = f"🚨 New Lead Alert - {lead_data.action_type.title()} Request"
        
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
                .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background: #f9fafb; }}
                .lead-details {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0; }}
                .urgent {{ background: #fee2e2; border-left: 4px solid #dc2626; padding: 15px; margin: 10px 0; }}
                .action-btn {{ display: inline-block; padding: 12px 24px; background: #4F46E5; color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>New Lead Alert</h1>
                    <p>You have received a new {lead_data.action_type} request</p>
                </div>
                
                <div class="content">
                    <div class="urgent">
                        <strong>⚡ Action Required:</strong> A potential patient wants to {lead_data.action_type} with your clinic.
                        Respond quickly to improve conversion rates!
                    </div>
                    
                    <div class="lead-details">
                        <h3>Lead Details</h3>
                        <p><strong>Patient Name:</strong> {lead_data.user_name or 'Anonymous'}</p>
                        <p><strong>Contact:</strong> {lead_data.contact_info or lead_data.user_phone or 'To be shared after contact'}</p>
                        <p><strong>Interested In:</strong> {lead_data.procedure_name or 'General Consultation'}</p>
                        {f'<p><strong>Preferred Doctor:</strong> {lead_data.doctor_name}</p>' if lead_data.doctor_name else ''}
                        <p><strong>Source:</strong> {lead_data.source_page.replace('_', ' ').title()}</p>
                        <p><strong>Date:</strong> {lead_data.created_at.strftime('%B %d, %Y at %I:%M %p')}</p>
                    </div>
                    
                    <div style="text-align: center;">
                        <a href="https://antidote.com/clinic/leads" class="action-btn">
                            View Lead Dashboard
                        </a>
                    </div>
                    
                    <div style="margin-top: 20px; padding: 15px; background: #e0f2fe; border-radius: 6px;">
                        <h4>💡 Quick Action Tips:</h4>
                        <ul>
                            <li>Respond within 5 minutes for best conversion</li>
                            <li>Have your consultation availability ready</li>
                            <li>Prepare pricing information for the requested procedure</li>
                        </ul>
                    </div>
                </div>
            </div>
        </body>
        </html>
        """
        
        text_body = f"""
        NEW LEAD ALERT - {lead_data.clinic_name}
        
        You have received a new {lead_data.action_type} request!
        
        Patient: {lead_data.user_name or 'Anonymous'}
        Contact: {lead_data.contact_info or lead_data.user_phone or 'To be shared after contact'}
        Procedure: {lead_data.procedure_name or 'General Consultation'}
        Doctor: {lead_data.doctor_name or 'Any available'}
        Date: {lead_data.created_at.strftime('%B %d, %Y at %I:%M %p')}
        
        Visit your clinic dashboard to respond: https://antidote.com/clinic/leads
        """
        
        return send_email(lead_data.clinic_email, subject, html_body, text_body)
        
    except Exception as e:
        logger.error(f"Error sending lead notification email: {e}")
        return False

def send_clinic_approval_email(clinic):
    """Send approval notification to clinic."""
    if not clinic.email:
        return False
    
    subject = f"🎉 Clinic Approved - Welcome to Antidote!"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
            .header {{ background: #10b981; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9fafb; }}
            .success-box {{ background: #d1fae5; border-left: 4px solid #10b981; padding: 15px; margin: 10px 0; }}
            .action-btn {{ display: inline-block; padding: 12px 24px; background: #10b981; color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Congratulations!</h1>
                <p>Your clinic has been approved</p>
            </div>
            
            <div class="content">
                <div class="success-box">
                    <strong>🎉 Great News!</strong> {clinic.name} has been approved and is now live on Antidote.
                </div>
                
                <h3>What's Next?</h3>
                <ul>
                    <li>✅ Your clinic profile is now visible to patients</li>
                    <li>💰 Purchase credits to start receiving leads</li>
                    <li>📊 Access your clinic dashboard for analytics</li>
                    <li>👩‍⚕️ Add your doctors and treatment packages</li>
                </ul>
                
                <div style="text-align: center;">
                    <a href="https://antidote.com/clinic/dashboard" class="action-btn">
                        Access Dashboard
                    </a>
                </div>
                
                <p>Need help getting started? Contact our support team at support@antidote.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(clinic.email, subject, html_body)

def send_clinic_rejection_email(clinic, reason):
    """Send rejection notification to clinic."""
    if not clinic.email:
        return False
    
    subject = f"Clinic Application Update - {clinic.name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
            .header {{ background: #dc2626; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9fafb; }}
            .warning-box {{ background: #fef2f2; border-left: 4px solid #dc2626; padding: 15px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Application Status Update</h1>
            </div>
            
            <div class="content">
                <div class="warning-box">
                    <strong>Application Update:</strong> We've reviewed your clinic application for {clinic.name}.
                </div>
                
                <h3>Reason for Review:</h3>
                <p>{reason}</p>
                
                <h3>Next Steps:</h3>
                <ul>
                    <li>Review the feedback provided above</li>
                    <li>Make necessary updates to your clinic information</li>
                    <li>Resubmit your application when ready</li>
                </ul>
                
                <p>If you have questions, please contact our team at support@antidote.com</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(clinic.email, subject, html_body)

def send_low_credit_warning(clinic_id):
    """Send warning when clinic credits are running low."""
    clinic_data = db.session.execute(text("""
        SELECT 
            c.*,
            COALESCE(credits.balance, 0) as credit_balance
        FROM clinics c
        LEFT JOIN (
            SELECT 
                clinic_id,
                SUM(CASE WHEN transaction_type = 'credit' THEN amount ELSE -amount END) as balance
            FROM credit_transactions
            GROUP BY clinic_id
        ) credits ON c.id = credits.clinic_id
        WHERE c.id = :clinic_id
    """), {"clinic_id": clinic_id}).fetchone()
    
    if not clinic_data or not clinic_data.email:
        return False
    
    subject = f"⚠️ Low Credit Balance Alert - {clinic_data.name}"
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
            .header {{ background: #f59e0b; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9fafb; }}
            .warning-box {{ background: #fef3c7; border-left: 4px solid #f59e0b; padding: 15px; margin: 10px 0; }}
            .action-btn {{ display: inline-block; padding: 12px 24px; background: #f59e0b; color: white; text-decoration: none; border-radius: 6px; margin: 10px 0; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Credit Balance Alert</h1>
            </div>
            
            <div class="content">
                <div class="warning-box">
                    <strong>⚠️ Low Balance Warning:</strong> Your credit balance is running low.
                </div>
                
                <p>Current Balance: <strong>{clinic_data.credit_balance} credits</strong></p>
                
                <p>To continue receiving leads, please top up your credit balance.</p>
                
                <div style="text-align: center;">
                    <a href="https://antidote.com/clinic/billing" class="action-btn">
                        Purchase Credits
                    </a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(clinic_data.email, subject, html_body)

def send_clinic_approval_email(email, clinic_name, contact_person, login_email, password, dashboard_url):
    """Send clinic approval email with login credentials."""
    subject = f"🎉 {clinic_name} - Application Approved! Welcome to Antidote"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Clinic Application Approved</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; background-color: #f8f9fa;">
        <div style="background: linear-gradient(135deg, #00A0B0 0%, #007A8C 100%); color: white; padding: 2rem; text-align: center;">
            <h1 style="margin: 0; font-size: 2rem;">Congratulations!</h1>
            <p style="margin: 0.5rem 0 0 0; font-size: 1.1rem;">Your clinic application has been approved</p>
        </div>
        
        <div style="background: white; padding: 2rem; margin: 0;">
            <div style="background: #e8f8f9; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <h2 style="color: #00A0B0; margin-top: 0;">Welcome to Antidote, {contact_person}!</h2>
                <p>We're excited to have <strong>{clinic_name}</strong> join India's premier medical aesthetic network.</p>
            </div>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 1.5rem; border-radius: 8px; margin-bottom: 1.5rem;">
                <h3 style="color: #856404; margin-top: 0;">🔐 Your Login Credentials</h3>
                <p><strong>Login Email:</strong> {login_email}</p>
                <p><strong>Password:</strong> <code style="background: #f8f9fa; padding: 0.2rem 0.5rem; border-radius: 4px;">{password}</code></p>
                <p style="color: #856404; font-size: 0.9rem;"><em>Please change your password after first login for security.</em></p>
            </div>
            
            <div style="text-align: center; margin: 2rem 0;">
                <a href="{dashboard_url}" style="background: linear-gradient(135deg, #00A0B0 0%, #007A8C 100%); color: white; padding: 1rem 2rem; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block;">
                    Access Your Dashboard
                </a>
            </div>
            
            <div style="border-top: 2px solid #e5e7eb; padding-top: 1.5rem; margin-top: 2rem;">
                <h3 style="color: #00A0B0;">Next Steps:</h3>
                <ul style="list-style: none; padding: 0;">
                   <li style="margin-bottom: 0.5rem;">✅ Complete your clinic profile</li>
                   <li style="margin-bottom: 0.5rem;">👩‍⚕️ Add your doctors and specialists</li>
                   <li style="margin-bottom: 0.5rem;">📦 Create treatment packages</li>
                   <li style="margin-bottom: 0.5rem;">🎯 Start connecting with people who like to get treatment</li>
                </ul>
            </div>
            
            <div style="background: #f8f9fa; padding: 1rem; border-radius: 8px; margin-top: 1.5rem;">
                <p><strong>Starting Credits:</strong> You've been given 100 free credits to get started!</p>
                <p style="font-size: 0.9rem; color: #666;">Credits are used for premium features and enhanced visibility.</p>
            </div>
            
            <div style="text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
                <p>Need help? Contact our support team:</p>
                <p><a href="mailto:clinics@antidote.fit" style="color: #00A0B0;">clinics@antidote.fit</a> | 8897432584</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(email, subject, html_content)

def send_clinic_rejection_email(email, clinic_name, contact_person, reason):
    """Send clinic rejection email with reason."""
    subject = f"Re: {clinic_name} - Application Update"
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Clinic Application Update</title>
    </head>
    <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; background-color: #f8f9fa;">
        <div style="background: #6c757d; color: white; padding: 2rem; text-align: center;">
            <h1 style="margin: 0; font-size: 1.8rem;">Application Update</h1>
            <p style="margin: 0.5rem 0 0 0;">Thank you for your interest in joining Antidote</p>
        </div>
        
        <div style="background: white; padding: 2rem; margin: 0;">
            <h2 style="color: #495057;">Dear {contact_person},</h2>
            
            <p>Thank you for submitting your application for <strong>{clinic_name}</strong> to join the Antidote network.</p>
            
            <p>After careful review, we are unable to approve your application at this time.</p>
            
            <div style="background: #fff3cd; border: 1px solid #ffeaa7; padding: 1.5rem; border-radius: 8px; margin: 1.5rem 0;">
                <h3 style="color: #856404; margin-top: 0;">Reason for Decision:</h3>
                <p style="margin-bottom: 0;">{reason}</p>
            </div>
            
            <p>We encourage you to address these concerns and reapply in the future. Our team is committed to maintaining the highest standards for all network partners.</p>
            
            <div style="background: #e8f4f8; padding: 1.5rem; border-radius: 8px; margin: 1.5rem 0;">
                <h3 style="color: #00A0B0; margin-top: 0;">Future Applications</h3>
                <p>You may submit a new application once you've addressed the feedback provided. We're always looking to work with qualified medical professionals.</p>
            </div>
            
            <div style="text-align: center; margin-top: 2rem; padding-top: 1rem; border-top: 1px solid #e5e7eb;">
                <p>Questions about this decision?</p>
                <p><a href="mailto:clinics@antidote.fit" style="color: #00A0B0;">clinics@antidote.fit</a> | 8897432584</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(email, subject, html_content)

def send_daily_lead_summary(clinic_id):
    """Send daily summary of leads to clinic."""
    # Get today's leads
    today_leads = db.session.execute(text("""
        SELECT 
            l.*,
            p.procedure_name,
            d.name as doctor_name
        FROM leads l
        LEFT JOIN procedures p ON l.procedure_id = p.id
        LEFT JOIN doctors d ON l.doctor_id = d.id
        WHERE l.clinic_id = :clinic_id 
        AND DATE(l.created_at) = CURRENT_DATE
        ORDER BY l.created_at DESC
    """), {"clinic_id": clinic_id}).fetchall()
    
    if not today_leads:
        return True  # No leads to report
    
    clinic = Clinic.query.get(clinic_id)
    if not clinic or not clinic.email:
        return False
    
    subject = f"📊 Daily Lead Summary - {len(today_leads)} new leads"
    
    leads_html = ""
    for lead in today_leads:
        leads_html += f"""
        <tr>
            <td>{lead.created_at.strftime('%I:%M %p')}</td>
            <td>{lead.action_type.title()}</td>
            <td>{lead.procedure_name or 'General'}</td>
            <td>{lead.status.title()}</td>
        </tr>
        """
    
    html_body = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <style>
            .email-container {{ max-width: 600px; margin: 0 auto; font-family: Arial, sans-serif; }}
            .header {{ background: #4F46E5; color: white; padding: 20px; text-align: center; }}
            .content {{ padding: 20px; background: #f9fafb; }}
            .stats-table {{ width: 100%; border-collapse: collapse; margin: 15px 0; }}
            .stats-table th, .stats-table td {{ padding: 10px; border: 1px solid #ddd; text-align: left; }}
            .stats-table th {{ background: #f3f4f6; }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <h1>Daily Lead Summary</h1>
                <p>{datetime.now().strftime('%B %d, %Y')}</p>
            </div>
            
            <div class="content">
                <h3>Today's Performance</h3>
                <p>You received <strong>{len(today_leads)} new leads</strong> today.</p>
                
                <table class="stats-table">
                    <thead>
                        <tr>
                            <th>Time</th>
                            <th>Type</th>
                            <th>Procedure</th>
                            <th>Status</th>
                        </tr>
                    </thead>
                    <tbody>
                        {leads_html}
                    </tbody>
                </table>
                
                <p><a href="https://antidote.com/clinic/leads">View all leads →</a></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return send_email(clinic.email, subject, html_body)