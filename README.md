
# YOUR PROJECT 
"Library Management System"
#### Video Demo:  <https://youtu.be/Hl_FEkv7pwg?si=LLArVt8MCRtp7Vi4>

#### Description:

The Library Management System is a Flask-based web application designed for an admin to efficiently manage daily library operations, including handling books, users, and transactions.


1. Database Setup
library_db.py initializes the SQLite database and creates required tables.
Running this script generates library.db, which stores books, authors, publishers, genres,users, and admin data.

2. User Authentication & Admin Management
Register Admin: An admin can register via register_admin.html.
Login: The admin logs in using a username and password. A session ID is used to remember login status.
Admin Dashboard: After logging in, the admin is redirected to a dashboard displaying:
Total books
Registered members
Issued books
Returned books
Deactivate Admin: Admins can deactivate their accounts, allowing a new admin to register.

3. Book Management
View Books: Displays all books with their details. Each book has Edit and Delete options.
Add Books: Requires an author, publisher, genres and other important information before adding a book.
Edit Books: Admin can update book details.
Soft Delete: Instead of permanently deleting a book, it is hidden for record-keeping.
Many-to-Many Relationship: A book can have multiple genres, but only one author and publisher (selected from a list).
ISBN: A book can have a unique identifier isbn number.

4. User Management
Add, View, Edit, and Delete Users
Users are uniquely identified by PA/PSS numbers to prevent duplicate registrations.

5. Book Issuing & Returning
Issue Book: Admin selects a user and book title to issue a book.
If copies are available, a success message appears.
If unavailable, a message states "This book is unavailable."
Return Book:
Admin updates the book status to "Returned", increasing copies_available and setting the return date.
This is done in view_users_record.

6. Security & Account Management
Change Password: Admins can change their password.
Logout: Clears the session and logs the admin out.
Session-based Authentication: If an admin is logged in, their name appears in the header. Otherwise, a Login button is displayed.

Helper Functions (helper.py)
admin_exists(): Checks if an admin account exists.
login_required(): Ensures only logged-in admins can access restricted pages.
get_db_connection(): Establishes a connection with the database.
These functions are imported in main.py



UI & Frontend
The project uses Bootstrap for a clean and responsive design.
JavaScript is used for interactive elements and form validations.
layout.html serves as a base template with a header, navigation bar, and footer, extended by all other HTML files.
The homepage (index.html) displays famous quotes and an About section.











