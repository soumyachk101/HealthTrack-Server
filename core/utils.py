import uuid
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

def send_otp_email(email, otp, first_name=None):
    """
    Sends an OTP code to the user's email address.
    """
    subject = 'Your HealthTrack+ Verification Code'
    message = f"""Hi {first_name or 'there'},

Your verification code for HealthTrack+ is:

    {otp}

This code will expire in 10 minutes.

If you did not request this code, please ignore this email.

Best regards,
The HealthTrack+ Team
"""
    
    # Get the from email - use EMAIL_HOST_USER as the sender
    from_email = settings.EMAIL_HOST_USER
    
    if not from_email:
        print("ERROR: EMAIL_HOST_USER is not configured!")
        return False
    
    try:
        print(f"Sending OTP email to {email} from {from_email}...")
        result = send_mail(
            subject,
            message,
            from_email,
            [email],
            fail_silently=False,
        )
        print(f"Email sent successfully! Result: {result}")
        return True
    except Exception as e:
        print(f"Error sending OTP email: {type(e).__name__}: {e}")
        import traceback
        traceback.print_exc()
        return False

def send_verification_email(user, request):
    """
    Generates a verification token and sends an email to the user.
    """
    token = str(uuid.uuid4())
    user.verification_token = token
    user.save()
    
    try:
        verify_url = request.build_absolute_uri(
            reverse('verify_email', args=[token])
        )
    except Exception:
        verify_url = f"/accounts/verify-email/{token}/"
    
    subject = 'Verify your email for HealthTrack+'
    message = f"""Hi {user.first_name or user.username},

Welcome to HealthTrack+!

Please click the link below to verify your email address and activate your account:
{verify_url}

If you did not register for this account, please ignore this email.

Best regards,
The HealthTrack+ Team
"""
    
    try:
        send_mail(
            subject,
            message,
            getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@healthtrack.plus'),
            [user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False

