from django import forms
from django.contrib.auth.hashers import make_password
from .models import Attendance, Faculty, LeaveRequest, Student, Subject, Notification, Lecture, Department, DegreeProgram
from registration.models import CustomUser

# Student Registration Form
class StudentForm(forms.ModelForm):
    DIVISION_CHOICES = [
        ("", "Select division"),
        ("A", "A"),
        ("B", "B"),
        ("C", "C"),
        ("D", "D"),
        ("E", "E"),
    ]
    BATCH_SUFFIXES = ["1", "2", "3", "4"]

    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    # # role = forms.ChoiceField(choices=CustomUser.ROLE_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    division = forms.ChoiceField(choices=DIVISION_CHOICES, widget=forms.Select(attrs={'class': 'form-control'}))
    batch = forms.ChoiceField(choices=[("", "Select batch")], widget=forms.Select(attrs={'class': 'form-control'}))
    department = forms.ModelChoiceField(queryset=Department.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    degree_program = forms.ModelChoiceField(queryset=DegreeProgram.objects.all(), required=False, widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Student
        fields = ["username", "email", "password", "name", "image", "phone", "semester", "division", "batch", "degree_program", "date_of_birth"]
        widgets = {
            'username': forms.Select(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'division': forms.Select(attrs={'class': 'form-control'}),
            'batch': forms.Select(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            if self.instance.degree_program:
                self.fields['degree_program'].initial = self.instance.degree_program
                self.fields['department'].initial = self.instance.degree_program.department

        division_value = None
        if self.data.get('division'):
            division_value = self.data.get('division')
        elif self.instance and self.instance.pk:
            division_value = self.instance.division

        if division_value:
            batch_choices = [
                (f"{division_value}{suffix}", f"{division_value}{suffix}")
                for suffix in self.BATCH_SUFFIXES
            ]
            self.fields['batch'].choices = [("", "Select batch")] + batch_choices

        # If department is selected in POST data, filter degree programs
        dept_value = None
        if self.data.get('department'):
            dept_value = self.data.get('department')
        elif self.instance and self.instance.pk and self.instance.degree_program:
            dept_value = getattr(self.instance.degree_program.department, 'id', None)

        if dept_value:
            try:
                self.fields['degree_program'].queryset = DegreeProgram.objects.filter(department_id=dept_value).order_by('name')
            except Exception:
                self.fields['degree_program'].queryset = DegreeProgram.objects.none()
        
    def clean_password(self):
        password = self.cleaned_data.get("password")

        # Enforce password requirement only for new users
        if not self.instance.pk and not password:
            raise forms.ValidationError("Password is required for new users.")

        return password

    def clean(self):
        cleaned_data = super().clean()
        division = cleaned_data.get("division")
        batch = cleaned_data.get("batch")

        if division:
            valid_batches = {f"{division}{suffix}" for suffix in self.BATCH_SUFFIXES}
            if not batch:
                self.add_error("batch", "Batch is required for the selected division.")
            elif batch not in valid_batches:
                self.add_error("batch", "Batch must be one of the four batches for the selected division.")

        return cleaned_data
    

    def save(self, commit=True):
        student = super().save(commit=False)

        if hasattr(student, "user") and student.user:
            user = student.user
        else:
            user = CustomUser()

        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        if commit:
            user.save()
            student.user = user
            student.save()
            self.save_m2m()  # Save many-to-many relationships (subjects)
        return student


# Faculty Registration Form
class FacultyForm(forms.ModelForm):
    username = forms.CharField(widget=forms.TextInput(attrs={'class': 'form-control'}))
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control'}), required=False)
    
    # Add subjects field for faculty specialization (optional)
    subjects = forms.ModelMultipleChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Select subjects this faculty can teach (optional - can be configured later via Subject Offerings)"
    )
    
    class Meta:
        model = Faculty
        fields = ["username", "email", "password", "name", "image", "phone", "department", "salary"]
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'image': forms.FileInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'salary': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super(FacultyForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.pk:
            self.fields['username'].initial = self.instance.user.username
            self.fields['email'].initial = self.instance.user.email
            self.fields['subjects'].initial = self.instance.subjects.all()

    def clean_password(self):
        password = self.cleaned_data.get("password")

        # Enforce password requirement only for new users
        if not self.instance.pk and not password:
            raise forms.ValidationError("Password is required for new users.")

        return password
    
    def save(self, commit=True):
        faculty = super().save(commit=False)
        if hasattr(faculty, "user") and faculty.user:
            user = faculty.user
        else:
            user = CustomUser()
        user.username = self.cleaned_data['username']
        user.email = self.cleaned_data['email']
        if self.cleaned_data['password']:
            user.set_password(self.cleaned_data['password'])
        user.role = 'faculty'  # Set role to faculty
        if commit:
            user.save()
            faculty.user = user
            faculty.save()
            faculty.subjects.set(self.cleaned_data.get('subjects', []))
            # Note: Selected subjects are saved for reference but actual teaching assignments
            # should be done through SubjectOffering in Django Admin or Subject Management
        return faculty


class NotificationForm(forms.ModelForm):
    class Meta:
        model = Notification
        fields = ["recipient_role", "title", "message"]
        widgets = {
            'recipient_role': forms.Select(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'message': forms.Textarea(attrs={'class': 'form-control'}),
            }

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["student", "lecture", "status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
            "student": forms.Select(attrs={"class": "form-control"}),
            "lecture": forms.Select(attrs={"class": "form-control"}),
        }

class AttendanceEditForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ["status"]
        widgets = {
            "status": forms.Select(attrs={"class": "form-control"}),
        }

class LeaveForm(forms.ModelForm):
    class Meta:
        model = LeaveRequest
        fields = ["reason", "start_date", "end_date"]
        widgets = {
            "start_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "end_date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "reason": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        }

class LectureForm(forms.ModelForm):
    class Meta:
        model = Lecture
        fields = ["subject_offering", "date", "start_time", "end_time", "lecture_type", "room_number"]
        widgets = {
            "subject_offering": forms.Select(attrs={"class": "form-control"}),
            "date": forms.DateInput(attrs={"type": "date", "class": "form-control"}),
            "start_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "end_time": forms.TimeInput(attrs={"type": "time", "class": "form-control"}),
            "lecture_type": forms.Select(attrs={"class": "form-control"}),
            "room_number": forms.TextInput(attrs={"class": "form-control"}),
        }


class AttendanceFilterForm(forms.Form):
    """Form to filter lectures by subject, session type, and date"""
    
    SUBJECT_CHOICES = [("", "Select a subject")]
    SESSION_CHOICES = [
        ("", "All types"),
        ("theory", "📖 Lecture"),
        ("practical", "🔬 Lab"),
        ("tutorial", "📝 Tutorial"),
    ]
    
    subject = forms.ModelChoiceField(
        queryset=Subject.objects.all(),
        widget=forms.Select(attrs={"class": "form-control"}),
        label="Subject",
        empty_label="Select a subject"
    )
    
    session_type = forms.ChoiceField(
        choices=SESSION_CHOICES,
        widget=forms.RadioSelect(attrs={"class": "form-check-input"}),
        label="Session Type",
        required=False
    )
    
    date = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={"type": "date", "class": "form-control"}),
        label="Date (optional)"
    )

    def __init__(self, *args, faculty=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Only show subjects this faculty teaches (using the M2M relationship)
        if faculty:
            offered_ids = Subject.objects.filter(
                offerings__faculty=faculty
            ).values_list("id", flat=True)
            qualified_ids = faculty.subjects.values_list("id", flat=True)
            subject_ids = set(offered_ids) | set(qualified_ids)
            self.fields["subject"].queryset = Subject.objects.filter(id__in=subject_ids).distinct()


# Subject Management Form
class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['code', 'name', 'credits', 'semester', 'is_elective', 'department']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., CS101'}),
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Subject Name'}),
            'credits': forms.NumberInput(attrs={'class': 'form-control', 'min': '1', 'max': '8'}),
            'semester': forms.Select(attrs={'class': 'form-control'}),
            'is_elective': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }