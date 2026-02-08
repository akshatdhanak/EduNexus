# Timetable Management Guide

## Overview
The attendance system now includes comprehensive timetable management for all semesters across departments.

## Features Implemented

### 1. **Admin Timetable Management**
- Navigate to: Admin Dashboard → Manage Timetable
- View timetables by department and semester
- Add, edit, or delete timetable entries
- Link: http://127.0.0.1:8000/admin_app/admin_dashboard/manage_timetable

### 2. **Student Timetable View**
- Students can view their semester-wise timetable
- Navigate to: Student Dashboard → Timetable
- Automatically shows timetable for student's department and selected semester

### 3. **Django Admin Panel**
- Full CRUD operations for timetable entries
- Link: http://127.0.0.1:8000/admin/admin_app/timetable/

## How to Assign Faculty to Subjects

### Method 1: Through Faculty Management
1. Go to Django Admin: http://127.0.0.1:8000/admin/
2. Navigate to **Admin_app → Faculties**
3. Click on a faculty member to edit
4. In the **Subject** field, select multiple subjects using Ctrl/Cmd + Click
5. Save the faculty record

### Method 2: When Creating Timetable Entries
1. Go to **Admin → Timetables**
2. Click **Add Timetable**
3. Fill in the details:
   - **Department**: Select CE (Computer Engineering) or others
   - **Semester**: 1-8
   - **Day**: Monday-Saturday
   - **Subject**: Select from available subjects
   - **Faculty**: Select the faculty member to teach this slot
   - **Slot Type**: Theory/Practical/Tutorial
   - **Start Time & End Time**: Set the time slot
   - **Room Number**: Optional classroom/lab number
4. Click **Save**

## Pre-populated Data

All semesters (1-8) for Computer Engineering have been pre-populated with:
- All subjects from the syllabus
- Sample timetable structure with 4-5 lectures per day
- Theory and practical sessions
- Proper time slots (8:30 AM - 5:30 PM)

### Timetable Structure
- **Monday-Saturday**: Classes scheduled
- **Recess**: 12:45 PM - 1:30 PM (implied, no slots during this time)
- **Morning Sessions**: 8:30 AM - 12:45 PM
- **Afternoon Sessions**: 1:30 PM onwards

## Customization

### To Update Timetable for a Specific Semester:
1. Navigate to Admin Dashboard → Manage Timetable
2. Select Department and Semester
3. Click **Edit** on any slot to modify
4. Or click **Add Entry** to create new slots

### To Change Faculty Assignment:
1. Go to the timetable entry
2. Change the **Faculty** field to the desired faculty member
3. Ensure that faculty member has the subject assigned in their profile
4. Save changes

### To Add New Subjects:
1. Go to Django Admin → Subjects
2. Click **Add Subject**
3. Enter subject name
4. The subject will now be available for timetable entries

## Management Command

A Django management command is available to reset and repopulate timetables:

```bash
python manage.py populate_timetable
```

This command will:
- Clear existing Computer Engineering timetables
- Create all subjects from the syllabus
- Generate sample timetable entries for all 8 semesters
- Use the first available faculty member (or prompt to add faculty)

## Notes

- All timetable entries require at least one faculty member in the database
- Faculty can be assigned to multiple subjects
- Each timetable slot is unique per department/semester/day/start_time
- Room numbers are optional but recommended for better organization
- Students automatically see their department's timetable based on their profile

## Troubleshooting

**Problem**: No timetable showing for students
**Solution**: 
1. Check if timetable entries exist for that department/semester
2. Verify student's department and semester fields are set correctly
3. Run populate_timetable command if starting fresh

**Problem**: Faculty not appearing in timetable dropdown
**Solution**: 
1. Ensure faculty members exist in the Faculty table
2. Check that faculty user accounts have role='faculty'

**Problem**: Subject not available
**Solution**: Add the subject through Django Admin → Subjects

## Access Points

- **Admin Dashboard**: http://127.0.0.1:8000/admin_app/admin_dashboard/
- **Manage Timetable**: http://127.0.0.1:8000/admin_app/admin_dashboard/manage_timetable
- **Django Admin**: http://127.0.0.1:8000/admin/
- **Student Timetable**: http://127.0.0.1:8000/student_app/view_timetable/
