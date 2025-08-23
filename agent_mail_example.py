#!/usr/bin/env python3
"""
Minimal AgentMail email sender
"""
import os
from dotenv import load_dotenv
from agentmail import AgentMail

# Load the API key from the .env file
load_dotenv()
api_key = os.getenv("AGENTMAIL_API_KEY")

def send_email(to_email, subject, message):
    """Send email using AgentMail."""
    client = AgentMail(api_key=api_key)
    
    # Get existing inbox (more reliable than creating new one)
    response = client.inboxes.list()
    if len(response.inboxes) == 0:
        print("❌ No existing inboxes found")
        return None
    
    inbox = response.inboxes[0]  # Use first available inbox
    
    # Send email
    result = client.inboxes.messages.send(
        inbox_id=inbox.inbox_id,
        to=to_email,
        subject=subject,
        text=message
    )
    
    print(f"✅ Email sent from {inbox.inbox_id}")
    print(f"📧 To: {to_email}")
    print(f"📝 Subject: {subject}")
    print(f"🆔 Message ID: {result.message_id}")
    
    return result

if __name__ == "__main__":
    # Example usage
    send_email(
        to_email="antaloaalonso@gmail.com",
        subject="Hello from AgentMail! 🎉",
        message="This is a test email sent using the minimal AgentMail setup."
    )