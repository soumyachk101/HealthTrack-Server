"""
Core models for the HealthTracker application.
Includes models for health records, medicines, prescriptions, and more.
"""
from django.db import models
from django.conf import settings
from django.utils import timezone


class HealthRecord(models.Model):
    """
    Stores daily health metrics for a user including BP, weight, and heart rate.
    """
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='health_records'
    )
    blood_pressure_systolic = models.IntegerField(null=True, blank=True)
    blood_pressure_diastolic = models.IntegerField(null=True, blank=True)
    blood_sugar = models.DecimalField(
        max_digits=6, decimal_places=2, null=True, blank=True
    )
    weight = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True
    )
    heart_rate = models.IntegerField(null=True, blank=True)
    temperature = models.DecimalField(
        max_digits=4, decimal_places=1, null=True, blank=True
    )
    oxygen_level = models.IntegerField(null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']

    def __str__(self):
        return f"{self.user.username} - {self.recorded_at.strftime('%Y-%m-%d')}"

    @property
    def bp_status(self):
        """
        Calculates blood pressure status based on systolic and diastolic values.
        Returns a string indicating the category (Normal, Elevated, High).
        """
        if not self.blood_pressure_systolic or not self.blood_pressure_diastolic:
            return 'Unknown'
        
        sys = self.blood_pressure_systolic
        dia = self.blood_pressure_diastolic

        if sys < 120 and dia < 80:
            return 'Normal'
        elif sys < 130 and dia < 80:
            return 'Elevated'
        elif sys < 140 or dia < 90:
            return 'High (Stage 1)'
        return 'High (Stage 2)'


class Medicine(models.Model):
    """
    Represents a medicine prescribed to or taken by the user.
    """
    FREQUENCY_CHOICES = [
        ('once', 'Once Daily'),
        ('twice', 'Twice Daily'),
        ('thrice', 'Three Times Daily'),
        ('asneeded', 'As Needed'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='medicines')
    name = models.CharField(max_length=200)
    dosage = models.CharField(max_length=100)
    frequency = models.CharField(max_length=20, choices=FREQUENCY_CHOICES)
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    prescribed_by = models.CharField(max_length=200, blank=True)
    notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} - {self.dosage}"


class Prescription(models.Model):
    """
    Stores prescription details including doctor info and digital copies.
    """
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='prescriptions')
    doctor_name = models.CharField(max_length=200)
    hospital_name = models.CharField(max_length=200, blank=True)
    diagnosis = models.TextField()
    prescription_date = models.DateField()
    follow_up_date = models.DateField(null=True, blank=True)
    document = models.FileField(upload_to='prescriptions/', blank=True, null=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-prescription_date']

    def __str__(self):
        return f"{self.user.username} - {self.prescription_date}"


class MentalHealthLog(models.Model):
    """
    Tracks daily mental health metrics like mood, stress, and sleep.
    """
    MOOD_CHOICES = [
        (1, 'Very Low'),
        (2, 'Low'),
        (3, 'Neutral'),
        (4, 'Good'),
        (5, 'Excellent'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='mental_health_logs')
    mood_score = models.IntegerField(choices=MOOD_CHOICES)
    stress_level = models.IntegerField(choices=MOOD_CHOICES)
    sleep_hours = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True)
    sleep_quality = models.IntegerField(choices=MOOD_CHOICES, null=True, blank=True)
    anxiety_level = models.IntegerField(choices=MOOD_CHOICES, null=True, blank=True)
    notes = models.TextField(blank=True)
    recorded_at = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']


class InsurancePolicy(models.Model):
    POLICY_TYPE_CHOICES = [
        ('health', 'Health Insurance'),
        ('life', 'Life Insurance'),
        ('term', 'Term Life Insurance'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='insurance_policies')
    policy_type = models.CharField(max_length=20, choices=POLICY_TYPE_CHOICES)
    provider_name = models.CharField(max_length=200)
    policy_number = models.CharField(max_length=100)
    coverage_amount = models.DecimalField(max_digits=12, decimal_places=2)
    premium_amount = models.DecimalField(max_digits=10, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    document = models.FileField(upload_to='insurance/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.provider_name} - {self.policy_number}"


class LifestyleLog(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lifestyle_logs')
    water_intake = models.IntegerField(default=0, help_text='In glasses')
    exercise_minutes = models.IntegerField(default=0)
    steps_count = models.IntegerField(default=0)
    calories_consumed = models.IntegerField(null=True, blank=True)
    calories_burned = models.IntegerField(null=True, blank=True)
    smoking_count = models.IntegerField(default=0)
    alcohol_units = models.IntegerField(default=0)
    notes = models.TextField(blank=True)
    recorded_at = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-recorded_at']
        unique_together = ['user', 'recorded_at']


class ActivityLog(models.Model):
    """
    Audit log for user activities like adding records or logging in.
    """
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('record_added', 'Health Record Added'),
        ('medicine_added', 'Medicine Added'),
        ('prescription_added', 'Prescription Added'),
        ('profile_updated', 'Profile Updated'),
        ('registration', 'User Registration'),
    ]
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=50, choices=ACTION_CHOICES)
    details = models.TextField(blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.username} - {self.action}"


class SystemSettings(models.Model):
    key = models.CharField(max_length=100, unique=True)
    value = models.TextField()
    description = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'System Settings'

    def __str__(self):
        return self.key
