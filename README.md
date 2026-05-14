📚 Library Management System (Flask)
🧠 Overview

A Flask-based web application designed to help administrators manage library operations such as books, users, and transactions efficiently. The system supports authentication, book issuing/returning, and full CRUD operations with a SQLite database.

🚀 Features

👤 Admin Management
Admin registration and login system
Session-based authentication
Admin dashboard with statistics
Ability to deactivate admin account

📚 Book Management
Add, edit, delete (soft delete) books
Manage authors, publishers, and genres
Support for multiple genres per book
ISBN tracking system
Track available copies

👥 User Management
Add, edit, delete users
Unique identification using PA/PSS numbers
Prevent duplicate user entries

🔄 Book Transactions
Issue books to users
Return books with automatic updates
Availability tracking system

🔐 Security
Login required decorators
Session handling
Password change functionality
Secure access control for admin routes

🗄️ Database
SQLite database (library.db)
Tables include:
Books
Authors
Publishers
Genres
Users
Admins
Transactions

Database is initialized using:
library_db.py

🛠️ Tech Stack
Python
Flask
SQLite
HTML / CSS (templates)
JavaScript
Jinja2

⚙️ Setup Instructions
pip install flask
python library_db.py
python main.py

📌 Key Concepts Used
CRUD operations
Many-to-many relationships
Session management
Database normalization
Flask routing & decorators
