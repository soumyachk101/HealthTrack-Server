from django import forms
from .models import Medicine, HealthRecord, Prescription, MentalHealthLog, LifestyleLog, InsurancePolicy


class MedicineForm(forms.ModelForm):
    class Meta:
        model = Medicine
        fields = ['name', 'dosage', 'frequency', 'start_date', 'end_date', 'prescribed_by', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'dosage': forms.TextInput(attrs={'class': 'form-control'}),
            'frequency': forms.Select(attrs={'class': 'form-select'}),
            'prescribed_by': forms.TextInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['end_date'].required = False
        self.fields['prescribed_by'].required = False
        self.fields['notes'].required = False


class HealthRecordForm(forms.ModelForm):
    class Meta:
        model = HealthRecord
        fields = ['blood_pressure_systolic', 'blood_pressure_diastolic', 'blood_sugar', 
                  'weight', 'heart_rate', 'temperature', 'oxygen_level', 'notes']
        widgets = {
            'blood_pressure_systolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'mmHg'}),
            'blood_pressure_diastolic': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'mmHg'}),
            'blood_sugar': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'mg/dL'}),
            'weight': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'kg'}),
            'heart_rate': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'bpm'}),
            'temperature': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'placeholder': 'F'}),
            'oxygen_level': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': '%'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ['doctor_name', 'hospital_name', 'diagnosis', 'prescription_date', 'follow_up_date', 'document', 'notes']
        widgets = {
            'doctor_name': forms.TextInput(attrs={'class': 'form-control'}),
            'hospital_name': forms.TextInput(attrs={'class': 'form-control'}),
            'diagnosis': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'prescription_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'follow_up_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['hospital_name'].required = False
        self.fields['follow_up_date'].required = False
        self.fields['document'].required = False
        self.fields['notes'].required = False


class MentalHealthLogForm(forms.ModelForm):
    class Meta:
        model = MentalHealthLog
        fields = ['mood_score', 'stress_level', 'sleep_hours', 'notes']
        widgets = {
            'mood_score': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'stress_level': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'sleep_hours': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.5', 'min': 0, 'max': 24}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }


class LifestyleLogForm(forms.ModelForm):
    class Meta:
        model = LifestyleLog
        fields = ['water_intake', 'exercise_minutes', 'steps_count', 'calories_consumed', 'calories_burned', 'smoking_count', 'alcohol_units', 'notes']
        widgets = {
            'water_intake': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'glasses'}),
            'exercise_minutes': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'minutes'}),
            'steps_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'calories_consumed': forms.NumberInput(attrs={'class': 'form-control'}),
            'calories_burned': forms.NumberInput(attrs={'class': 'form-control'}),
            'smoking_count': forms.NumberInput(attrs={'class': 'form-control'}),
            'alcohol_units': forms.NumberInput(attrs={'class': 'form-control'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].required = False


class InsurancePolicyForm(forms.ModelForm):
    class Meta:
        model = InsurancePolicy
        fields = ['provider_name', 'policy_number', 'policy_type', 'start_date', 'end_date', 
                  'premium_amount', 'coverage_amount', 'document']
        widgets = {
            'provider_name': forms.TextInput(attrs={'class': 'form-control'}),
            'policy_number': forms.TextInput(attrs={'class': 'form-control'}),
            'policy_type': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'premium_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'coverage_amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'document': forms.FileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['document'].required = False
