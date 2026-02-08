from django import forms
from admin_app.models import Student
from registration.models import CustomUser


class StudentProfileForm(forms.ModelForm):
    """Form for editing student profile - excludes username/ID"""
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    
    class Meta:
        model = Student
        fields = [
            'name', 'image', 'phone', 'semester', 'division', 'batch',
            'date_of_birth', 'blood_group',
            'address', 'city', 'state', 'pincode',
            'father_name', 'father_contact',
            'mother_name', 'mother_contact',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Full Name'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '10-digit mobile number'}),
            'semester': forms.NumberInput(attrs={'class': 'form-control'}),
            'division': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Division'}),
            'batch': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Batch Year'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'blood_group': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Blood Group'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Full Address'}),
            'city': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'City'}),
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'State'}),
            'pincode': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Pincode'}),
            'father_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Father's Name"}),
            'father_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Father's Contact"}),
            'mother_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Mother's Name"}),
            'mother_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Mother's Contact"}),
        }
    
    def __init__(self, *args, **kwargs):
        # Get the user instance to populate email field
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['email'].initial = user.email
    
    def save(self, commit=True, user=None):
        student = super().save(commit=False)
        if user and self.cleaned_data.get('email'):
            user.email = self.cleaned_data['email']
            if commit:
                user.save()
        if commit:
            student.save()
        return student
