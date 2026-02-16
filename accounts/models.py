from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta

class User(AbstractUser):
    USER_TYPE_CHOICES = [
        ('patient', 'Patient'),
        ('provider', 'Service Provider'),
        ('admin', 'Administrator'),
    ]
    
    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='patient')
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    profile_image = models.ImageField(upload_to='profiles/', blank=True, null=True)
    emergency_contact = models.CharField(max_length=100, blank=True)
    emergency_phone = models.CharField(max_length=20, blank=True)
    blood_group = models.CharField(max_length=10, blank=True)
    is_approved = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.user_type})"

    @property
    def is_admin_user(self):
        return self.user_type == 'admin' or self.is_superuser

    @property
    def is_provider(self):
        return self.user_type == 'provider'

    @property
    def is_patient(self):
        return self.user_type == 'patient'


class ServiceProvider(models.Model):
    PROVIDER_TYPE_CHOICES = [
        ('hospital', 'Hospital'),
        ('clinic', 'Clinic'),
        ('pharmacy', 'Pharmacy'),
        ('lab', 'Laboratory'),
        ('doctor', 'Doctor'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='provider_profile')
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPE_CHOICES)
    business_name = models.CharField(max_length=200)
    license_number = models.CharField(max_length=100, blank=True)
    specialization = models.CharField(max_length=200, blank=True)
    working_hours = models.CharField(max_length=100, blank=True)
    services_offered = models.TextField(blank=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)

    def __str__(self):
        return self.business_name


class OTP(models.Model):
    OTP_TYPES = [
        ('register', 'Registration'),
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
    ]
    
    email = models.EmailField()
    otp_code = models.CharField(max_length=6)
    otp_type = models.CharField(max_length=20, choices=OTP_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    def __str__(self):
        return f"{self.email} - {self.otp_code}"
    
    @classmethod
    def create_otp(cls, email, otp_type):
        import datetime
        from django.utils import timezone
        
        # Delete any existing unused OTPs for this email and type
        cls.objects.filter(email=email, otp_type=otp_type, is_used=False).delete()
        
        # Create new OTP that expires in 10 minutes
        expires_at = timezone.now() + datetime.timedelta(minutes=10)
        import random
        otp_code = str(random.randint(100000, 999999))
        otp_instance = cls.objects.create(
            email=email,
            otp_code=otp_code,
            otp_type=otp_type,
            expires_at=expires_at
        )
        return otp_instance
    
    @classmethod
    def validate_otp(cls, email, otp_code, otp_type):
        try:
            otp_instance = cls.objects.get(
                email=email,
                otp_code=otp_code,
                otp_type=otp_type,
                is_used=False,
                expires_at__gt=timezone.now()
            )
            otp_instance.is_used = True
            otp_instance.save()
            return otp_instance
        except cls.DoesNotExist:
            return None
