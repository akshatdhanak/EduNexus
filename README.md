# Attendance System with Barcode Scanning

This is a Django-based attendance operations system that allows students to mark attendance using a barcode scanner via a webcam.  
It features user authentication, role-based redirection (admin & student), and a simple Bootstrap UI.

#Features
📷 Camera-based Barcode Scanning
👤 User Authentication (Admin & Students)
🔀 Role-based Redirection (Admin → Dashboard, Student → Attendance Page)
📊 Attendance Reports for Admins
🎨 Bootstrap for Responsive UI

#Installation & Setup
✅ 1. Clone the Repository
git clone https://github.com/Bhargav-611/Attendance-System.git  
 cd attendance-system  
 ✅ 2. Create & Activate a Virtual Environment
python -m venv venv  
 source venv/bin/activate # On Windows: venv\Scripts\activate  
 ✅ 3. Install Dependencies
pip install -r requirements.txt  
 ✅ 4. Apply Migrations & Run Server
python manage.py migrate  
 python manage.py runserver  
 Now, open http://127.0.0.1:8000/ in your browser.

Install django
python -m pip install Django

Required Librarys
pip install django-bootstrap-v5
pip install opencv-python
pip install pyzbar

📂 attendance-system  
│-- 📂 attendance/ # Main Django app  
│-- 📂 templates/ # HTML templates  
│-- 📂 static/ # CSS & JS files  
│-- manage.py # Django entry point  
│-- requirements.txt # Dependencies  
│-- README.md # Project Documentation

#Technologies Used
Django - Backend Framework
OpenCV - Camera Access for Barcode Scanning
Bootstrap - Frontend UI
SQLite - Database
