# import required libraries 
import os
import sqlite3
from flask import Flask, render_template, request, redirect,flash, url_for, session
from flask_session import Session
from werkzeug.security import check_password_hash, generate_password_hash
from helper import get_db_connection, is_delete, admin_exists, login_required, SECRET_KEY
from datetime import datetime, timedelta
import traceback, re



# initilize the Flask application
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "fallback_secret_key")  # Use fallback if env variable fails

app.config["TEMPLATES_AUTO_RELOAD"] = True


conn = get_db_connection()
if conn:
    print("Database connection established in app.py")
else:
    print("Failed to connect to the database in app.py")
    
    
# route to the home page
@app.route('/')
def home():
    return render_template('index.html')


# register admin
@app.route("/register_admin", methods=['GET', 'POST'])
def register_admin():
    if admin_exists():
        flash("Admin already exists. Please deactivate the current admin to register a new one.", 403)
        print(admin_exists())
        return redirect('/')
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        email_id= request.form.get('email_id')
        phone_number = request.form.get('phone_number')
        date_created =  datetime.now()
        
        if password != confirm_password:
            flash("Passwords do not match")
            return redirect('/register_admin')
        else:
            # hash password for security
            hashed_password = generate_password_hash(password)
            
            #insert the new admin
            conn = get_db_connection()
            cursor = conn.cursor()
            try:
                cursor.execute("""
                           INSERT INTO admin (
                               username, password, email_id, phone_number, is_active, date_created)
                               VALUES(?, ?, ?, ?, 1, ?)
                           """ , (username, hashed_password, email_id, phone_number, date_created))
                conn.commit()
                flash("Admin registered successfully!", 'success')
                return redirect('/login')
            except sqlite3.Error as e:
                flash(f"An error occured: {e}", 'danger')
                return redirect('/register_admin')
            finally:
                conn.close()
    return render_template('register_admin.html')

# change password for admin
@app.route('/change_password', methods=['GET','POST'])
def change_password():
     if 'admin_id' not in session:
        flash("You must be logged in to change your password", "danger")
        return redirect(url_for('login'))
    
     if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']
        confirm_password = request.form['confirm_password']

        if new_password != confirm_password:
                    flash("New passwords do not match!", "danger")
                    return redirect(url_for('change_password'))
                
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Fetch current hashed password
        cursor.execute("SELECT password FROM admin WHERE admin_id = ?", (session['admin_id'],))
        admin = cursor.fetchone()

        if admin and check_password_hash(admin['password'], old_password):
            hashed_password = generate_password_hash(new_password)
            cursor.execute("UPDATE admin SET password = ? WHERE admin_id = ?", (hashed_password, session['admin_id']))
            conn.commit()
            flash("Password updated successfully!", "success")
        else:
            flash("Incorrect old password!", "danger")

        cursor.close()
        conn.close()
        return redirect(url_for('admin_dashboard'))

     return render_template('change_password.html')

    

@app.route('/deactivate_admin', methods=['GET','POST'])
def deactivate_admin():   
    print("Inside deactivate_admin route")

    admin_id = session.get('admin_id')  # Ensure session has admin_id

    if not admin_id:
        flash("Admin not logged in.", "error")
        return redirect('/login')
    
    conn = get_db_connection()
    cursor = conn.cursor()

    # Fetch the active admin matching session admin_id
    cursor.execute("SELECT admin_id, username, email_id, phone_number, is_active, date_created FROM admin WHERE admin_id = ? AND is_active = ?", (admin_id, 1))
    admin = cursor.fetchone()

    if not admin:
        flash("No active admin found.", "error")
        return redirect('/')

    if request.method == 'GET':
        return render_template('deactivate_admin.html', admin=admin)

    # Handle POST request for deactivation
    password = request.form.get('password')

    # Verify the password before allowing deactivation
    cursor.execute("SELECT password FROM admin WHERE admin_id = ?", (admin_id,))
    result = cursor.fetchone()
    if not result:
        flash("Admin not found.", "error")
        return redirect('/deactivate_admin')

    if not check_password_hash(result[0], password):
        flash("Incorrect password.", "error")
        return redirect('/deactivate_admin')

    # Update admin status
    cursor.execute("UPDATE admin SET is_active = 0 WHERE admin_id = ?", (admin_id,))
    conn.commit()  # Ensure changes are saved
    print("Rows updated:", cursor.rowcount)  # Debugging output

    conn.close()
    session.pop('admin_id', None) 
    session.clear()  # Clear the session data
    flash("Admin has been deactivated.", "success")
    return redirect('/register_admin')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        # Validate inputs
        if not username:
            flash("Invalid username", "danger")
            return redirect('/login')
        if not password:
            flash("Wrong password!", "danger")
            return redirect('/login')

        # If inputs are valid, proceed with authentication
        conn = get_db_connection()
        cursor = conn.cursor()

        # Query the admin table for the user
        cursor.execute("SELECT * FROM admin WHERE username = ? AND is_active = 1", (username,))
        admin = cursor.fetchone()

        if admin:
            # Check if the password matches
            if check_password_hash(admin['password'], password):
                session['admin_id'] = admin['admin_id']  # Save admin ID in session
                session['admin_username'] = admin['username']
                print(session)
                flash("Login successful!", "success")
                return redirect('/admin_dashboard')
            else:
                flash("Incorrect password", "danger")
        else:
            flash("Admin not found or account deactivated!", "danger")
            conn.close()

    # If login fails, render the login page again with flash messages
    return render_template('login.html')

# Create the logout route
@app.route('/logout')
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect('/')

# Create the admin_dashboard route
@app.route('/admin_dashboard', methods=['GET'])
@login_required
def admin_dashboard():

    if request.method == 'GET':
        # Check if admin session exists before fetching data
        if 'admin_id' not in session or 'admin_username' not in session:
            flash("You must log in first", "danger")
            return redirect('/login')  # Redirect to login if session is missing
        
        conn = get_db_connection()
        cursor = conn.cursor()

        try:
            # Fetch total number of books in the library
            cursor.execute("SELECT COUNT(*) AS total_books FROM books")
            total_books = cursor.fetchone()['total_books']

            # Fetch number of issued books
            cursor.execute("SELECT COUNT(*) AS books_issued FROM users_record WHERE is_returned = 0")
            books_issued = cursor.fetchone()['books_issued']

            # Fetch number of returned books
            cursor.execute("SELECT COUNT(*) AS books_returned FROM users_record WHERE is_returned = 1")
            books_returned = cursor.fetchone()['books_returned']

            # Fetch total number of users
            cursor.execute("SELECT COUNT(*) AS members FROM users")
            members = cursor.fetchone()['members']

        except Exception as e:
            flash(f'An error occurred while fetching dashboard data: {e}', 'danger')
            return redirect('/login')

        finally:
            conn.close()

        # Pass the data to the template
        dashboard_data = {
            "total_books": total_books,
            "books_issued": books_issued,
            "books_returned": books_returned,
            "members": members,
            "date_today": datetime.now().strftime('%d %B %Y (%A) %H:%M:%S'),
        }

        return render_template('admin_dashboard.html', data=dashboard_data)



# Manage Books(like view, add, edit or delete books)

# View all books or search for books
@app.route('/books')
def books():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = request.args.get('query', '')  # Get the search query from the request
    if query:   
        cursor.execute("""
            SELECT books.book_id, books.title,books.isbn, books.edition, books.copies_total, books.status, books.shelf_number, books.copies_available,
            authors.name AS author, publishers.name AS publishers, GROUP_CONCAT(genres.genre_name, ', ') AS genres, books.published_year
            FROM books
            JOIN authors ON books.author_id = authors.author_id
            JOIN publishers ON books.publisher_id = publishers.publisher_id
            LEFT JOIN book_genres ON books.book_id = book_genres.book_id
            LEFT JOIN genres ON book_genres.genre_id = genres.genre_id
            WHERE books.title LIKE ? OR authors.name LIKE ? OR genres.genre_name LIKE ?
            GROUP BY books.book_id
        """, ('%' + query + '%', '%' + query + '%', '%' + query + '%'))
        
    else:
        cursor.execute("""
            SELECT books.book_id,books.isbn, books.edition, books.copies_total ,books.shelf_number,books.status,books.copies_available,
            books.title, authors.name AS author, publishers.name AS publishers, GROUP_CONCAT(genres.genre_name, ', ') AS genres, books.published_year
            FROM books
            JOIN authors ON books.author_id = authors.author_id
            JOIN publishers ON books.publisher_id = publishers.publisher_id
            LEFT JOIN book_genres ON books.book_id = book_genres.book_id
            LEFT JOIN genres ON book_genres.genre_id = genres.genre_id
            GROUP BY books.book_id
        """)    

    books = cursor.fetchall()
    conn.close()
    return render_template('books.html', books=books)

# Add a new book 
@app.route('/add_book', methods=['GET', 'POST'])
def add_book():
    conn = get_db_connection()
    c = conn.cursor()
   

    # Fetch authors, publishers, and genres for dropdowns
    c.execute("SELECT author_id, name FROM authors")
    authors = c.fetchall()
    c.execute("SELECT publisher_id, name FROM publishers")
    publishers = c.fetchall()
    c.execute("SELECT genre_id, genre_name FROM genres")
    genres = c.fetchall()
    
  

    if request.method == 'POST':
        # Collect form data
        title = request.form['title']
        isbn = request.form['isbn']
        edition = request.form['edition']
        copies_total = request.form['copies_total']
        shelf_number = request.form['shelf_number']
        author_id = request.form['author_id']
        publisher_id = request.form['publisher_id']
        genre_ids = request.form.getlist('genre_id[]')  # for multiple genres
        year = request.form['published_year']

        # Convert necessary fields to integers
        try:
            copies_total = int(copies_total)
            author_id = int(author_id)
            publisher_id = int(publisher_id)
            year = int(year)
        except ValueError:
            flash('Invalid input! Make sure numerical fields are entered correctly.')
            return render_template('add_update_book.html', authors=authors, publishers=publishers, genres=genres, book=None)

        # Basic validation
        if not title or not isbn or not edition or not shelf_number:
            flash('Please fill in all required fields.')
            return render_template('add_update_book.html', authors=authors, publishers=publishers, genres=genres, book=None)
        
        # Set copies_available to copies_total
        copies_available = copies_total

        # Set status based on copies_available
        status = 'available' if copies_available > 0 else 'unavailable'


        c.execute('''INSERT INTO books (title, isbn, edition, copies_total, copies_available,
                     shelf_number, status, author_id, publisher_id, published_year)
                     VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (title, isbn, edition, copies_total, copies_available, shelf_number,
                      status, author_id, publisher_id, year))
        
        book_id = c.lastrowid  # Get the last inserted book ID

         # Insert into book_genres table (for multiple genres)
        if genre_ids:
            for genre_id in genre_ids:
                try:
                    genre_id = int(genre_id) 
                    c.execute("INSERT INTO book_genres (book_id, genre_id) VALUES (?, ?)", (book_id, genre_id))
                except ValueError:
                    flash('Invalid genre selection.')
        
        conn.commit()
        conn.close()

        flash('Book added successfully!')
        return redirect('/books')

    # Render the form
    return render_template('add_update_book.html', book=None, authors=authors, publishers=publishers, genres=genres)

@app.route('/update_book/<int:book_id>', methods=['GET', 'POST'])
def update_book(book_id):
    conn = get_db_connection()

    if request.method == 'GET':
        # Retrieve book data for pre-filling the form
        book = conn.execute('SELECT * FROM books WHERE book_id = ?', (book_id,)).fetchone()
        authors = conn.execute('SELECT * FROM authors').fetchall()
        publishers = conn.execute('SELECT * FROM publishers').fetchall()
        genres = conn.execute('SELECT * FROM genres').fetchall()
        
        #fetch  exisiting genres for the book
        
        existing_genres = conn.execute(
            "SELECT genre_id FROM book_genres WHERE book_id = ?", (book_id,)
        ).fetchall()
        existing_genre_ids = {genre['genre_id'] for genre in existing_genres}  # Convert to set

        conn.close()

        if book is None:
            print(f"Book with ID {book_id} not found.")
            return "Book not found", 404

        # Render the form with the book's current data
        book = dict(book)  # Convert row to dictionary if needed
        book['genre_ids'] = existing_genre_ids  # Attach genres to book
        return render_template('add_update_book.html', book=book, authors=authors, publishers=publishers, genres=genres, existing_genre_ids=existing_genre_ids)

    if request.method == 'POST':
        # Get the form data
        title = request.form['title']
        isbn = request.form['isbn']
        edition = request.form['edition']
        copies_total = request.form['copies_total']
        shelf_number = request.form['shelf_number']
        year = request.form['published_year']
        genre_ids = request.form.getlist('genre_id[]')
        
         # Automatically set copies_available to copies_total and status
        copies_available = int(copies_total)
        status = 'available' if copies_available > 0 else 'unavailable'

        
        conn = get_db_connection()
        c = conn.cursor()

        # Update the book in the database
        c.execute("""
            UPDATE books
            SET title = ?, isbn = ?, edition = ?, copies_total = ?, copies_available = ?, 
                shelf_number = ?, status = ?, published_year = ?
            WHERE book_id = ?
        """, (title, isbn, edition, copies_total, copies_available, shelf_number, status, year, book_id))
        
         # Update book_genres table
        c.execute("DELETE FROM book_genres WHERE book_id = ?", (book_id,))  # Remove old genres
        for genre_id in genre_ids:
            c.execute("INSERT INTO book_genres (book_id, genre_id) VALUES (?, ?)", (book_id, genre_id))

        conn.commit()
        conn.close()

        # Redirect to the books page
        return redirect('/books')


# Delete books
@app.route('/delete_book/<int:book_id>', methods=['POST'])
def delete_book(book_id):
    # Connect to the database
    conn = get_db_connection()
    
    # Check if the book exists before attempting to delete
    book = conn.execute('SELECT * FROM books WHERE book_id = ?', (book_id,)).fetchone()
    if not book:
        conn.close()
        return("Book not found", 404)  # Return a 404 error if the book doesn't exist

    #delete the book
    conn.execute("DELETE FROM books WHERE book_id = ?", (book_id,))
    conn.commit()
    conn.close()
    flash('Book deleted successfully!', 'success')
    return redirect('/books')  # Redirect to the books listing page after deletion


# Admin Manages Users

# register_user a new user

@app.route('/register_user', methods=['GET', 'POST'])
def register_user():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        pa_pss_number = request.form.get('pa_pss_number')
        email_id = request.form.get('email_id').strip()
        phone_number = request.form.get('phone_number').strip()
        address = request.form.get('address').strip()

        # Input validation
        if not username or  not pa_pss_number or not email_id or not phone_number or not address:
            flash('All fields are required!', 'warning')
            return render_template('register_user.html')
        
        if not any(prefix in pa_pss_number for prefix in ['PA', 'PSS', 'PN']):
            flash('Army Number must be a valid number.', 'danger')
            return render_template('register_user.html', username=username, pa_pss_number=pa_pss_number,
                                   email_id=email_id, phone_number=phone_number,  address=address)

        # Input validation for email format using regular expression
        email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
        if not re.match(email_regex, email_id):
            flash('Invalid email format. Please enter a valid email address.', 'danger')
            return render_template('register_user.html', username=username, pa_pss_number=pa_pss_number,
                                   email_id=email_id, phone_number=phone_number,  address=address)
       
        if not phone_number.isdigit():
            flash('Invalid phone number format', 'danger')
            return render_template('register_user.html', username=username, pa_pss_number=pa_pss_number,
                                   email_id=email_id,  phone_number=phone_number, address=address)

         # Get current datetime for date_activated
        date_activated = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        conn = get_db_connection()
        c = conn.cursor()
        
        # Ensure pa_pss_number and email_id are stripped of extra spaces
        c.execute("SELECT * FROM users WHERE pa_pss_number = ? AND email_id = ? ", (pa_pss_number, email_id))
        existing_user = c.fetchone()

        if existing_user:
                flash(f'{pa_pss_number}  {email_id} already exists!', 'danger')
                return render_template('register_user.html', username=username,  
                                   pa_pss_number=pa_pss_number, email_id=email_id, phone_number=phone_number, address=address)
        else:
        # Database interaction
            try:
                c.execute("""
                    INSERT INTO users (username, pa_pss_number, email_id, phone_number, address, is_active, date_activated)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (username, pa_pss_number, email_id, phone_number, address, 1, date_activated))
                conn.commit()
                flash('User registered successfully!', 'success')
                return redirect("/view_users")
            except Exception as e:
                flash(f'An error occurred: {str(e)}', 'danger')
            finally:
                conn.close()

    return render_template('register_user.html', username='', pa_pss_number='', email_id='', phone_number='', address='')

@app.route('/view_users', methods=['GET', 'POST'])
def view_users():
    conn = get_db_connection()
    c = conn.cursor()

    search_query = request.args.get('search', '')  # Get search term
    try:

        if search_query:
        
         c.execute("""SELECT users.user_id, users.username, users.pa_pss_number, users.email_id, users.phone_number,
                   users.address, users.is_active, users.date_activated
                          FROM users
                          WHERE (users.username LIKE ? OR users.pa_pss_number LIKE ? OR CAST(users.is_active AS TEXT) LIKE ?)
                          AND is_deleted =0
                          """,
                           (f'%{search_query}%', f'%{search_query}%', f'%{search_query}%'))
        else:
        #fetch all users without filtering
            c.execute(""" SELECT users.user_id, users.username, users.pa_pss_number,users.phone_number, users.address, 
                      users.email_id, users.is_active, users.date_activated FROM users where is_deleted = 0 
                       """)

        view_users = c.fetchall()
    
        return render_template('view_users.html', view_users=view_users)
    
    except Exception as e:
        # Log the exception and flash a  message
        print(f"Error: {e}")
        flash("An error occurred while fetching user data.", "danger")
        return redirect('/')
    finally:
        conn.close()

# edit/update users details
@app.route('/edit_user/<int:user_id>', methods=['GET', 'POST'])
def edit_user(user_id):
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch user details to pre-fill the form
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    
    if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('view_users'))

    if request.method == 'POST':
        # Get the updated user details
        username = request.form.get('username')
        pa_pss_number = request.form.get('pa_pss_number')
        email_id = request.form.get('email_id')
        phone_number = request.form.get('phone_number')
        address = request.form.get('address')
        status = 1 if request.form.get('status') == '1' else 0
        try:
                # Update user in the database
                c.execute("""
                    UPDATE users SET username = ?, pa_pss_number = ?, email_id = ?, phone_number = ?, address = ?, is_active = ?
                    WHERE user_id = ?
                """, (username, pa_pss_number, email_id, phone_number, address, status ,user_id))

                conn.commit()
                flash('User updated successfully!', 'success')
            
        except Exception as e:
            flash(f'An error occurred while updating the user: {str(e)}', 'danger')
            return render_template('edit_user.html', user=user)
        finally:
            conn.close()
        return redirect(url_for('view_users'))

    return render_template('edit_user.html', user=user)
  

# Create the delete_user Route
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def soft_delete_user(user_id):
    try:
        conn = get_db_connection()
        c = conn.cursor()
        c.execute("""UPDATE users SET is_deleted = 1 WHERE user_id = ?""", (user_id,))
        conn.commit()
        flash("User deleted successfully!", "success")
        return redirect('/view_users')

            
    except Exception as e:
        print(f"Error deleting user: {e}")
        print(traceback.format_exc())  
        flash("An unexpected error occurred while trying to delete the user.", "danger")
        
    # Redirect back to the users list
        return redirect("/view_users")
    finally:
        conn.close()


# Issue books to the user
@app.route('/issue_book', methods=['GET', 'POST'])
def issue_book():
    conn = get_db_connection()
    c = conn.cursor()
    
    c.execute("SELECT username FROM users WHERE is_deleted = 0")
    users = c.fetchall()
    c.execute("SELECT title FROM books WHERE copies_available > 0")
    books = c.fetchall()

    if request.method == 'POST':
        username = request.form.get('username')
        book_title = request.form.get('book_title')

        if not username:
            flash("Username required!", 'danger')
            conn.close()
            return redirect("/issue_book")  # Redirect to issue_books
        elif not book_title:
            flash("Book Title required!", 'danger')
            conn.close()
            return redirect("/issue_book")  # Redirect to issue_books

        # Fetch the user_id based on username
        c.execute("SELECT user_id FROM users WHERE username = ?", (username,))
        user = c.fetchone()

        if not user:
            flash("User not found!", 'danger')
            conn.close()
            return redirect("/issue_book")  # Redirect to issue_books

        user_id = user[0]

        # Fetch the book_id and copies_available
        c.execute("SELECT book_id, copies_available  FROM books WHERE title = ?", (book_title,))
        book = c.fetchone()

        if not book:
            flash("Book not found!", 'danger')
            conn.close()
            return redirect("/issue_book")  # Redirect to issue_books


        book_id = book[0]
        copies_available = book[1]
        
        if copies_available == 0:
            flash("This book is currently unavailable.")
            conn.close()
            return redirect("/issue_book")
         # **Check if the user already has this book issued and not returned**
        c.execute("""
            SELECT COUNT(*) FROM users_record 
            WHERE user_id = ? AND book_id = ? AND is_returned = 0
        """, (user_id, book_id))

        if c.fetchone()[0] > 0:
            flash("This user already has this book issued and has not returned it!", 'warning')
            conn.close()
            return redirect("/issue_book")

        # Calculate the due date (30 days from now)
        issue_date = datetime.now()
        due_date = issue_date + timedelta(days=30)
        return_date = '%Y-%m-%d'

        try:

            # Insert the record into users_record table
            c.execute("""
                INSERT INTO users_record (user_id, book_id, issue_date, due_date, is_returned, return_date)
                VALUES (?, ?, ?, ?, 0, ?)
            """, (user_id, book_id, issue_date, due_date,return_date))
            conn.commit()


                    # Update book's copies_available and status
            c.execute("""
                UPDATE books
                SET copies_available = copies_available - 1, 
                    status = CASE WHEN copies_available - 1 = 0 THEN 'unavailable' ELSE status END
                WHERE book_id = ?
            """, (book_id,))
            conn.commit()
            
            flash("Book issued successfully!")
            conn.close()
            return redirect("/view_users_record")  # Redirect to the view_users_record page
        except sqlite3.Error as e:
                conn.rollback()
                flash(f"Database error: {e}")
                return redirect("/issue_book")
    
    conn.close()  # Close the connection for GET request
    return render_template('issue_book.html', users=users, books=books)


@app.route('/return_book/<int:users_record_id>', methods=['POST'])
def return_book(users_record_id):
    conn = get_db_connection()
    c = conn.cursor()

    # Fetch the user_record and related book details
    c.execute("""
        SELECT users_record.book_id, books.copies_available
        FROM users_record
        JOIN books ON books.book_id = users_record.book_id
        WHERE users_record.users_record_id = ?
    """, (users_record_id,))
    record = c.fetchone()

    if not record:
        flash("Record not found!")
        conn.close()
        return redirect("/view_users_record")

    book_id, copies_available = record
    
    # Update users_record to mark the book as returned
    return_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    # Update users_record to mark the book as returned
    c.execute("""
        UPDATE users_record
        SET is_returned = 1, return_date = ?
        WHERE users_record_id = ?
    """, (return_date, users_record_id))
    conn.commit()

    # Update the book's copies_available and status
    new_copies_available = copies_available + 1
    c.execute("""
        UPDATE books
        SET copies_available = ?, 
            status = CASE WHEN ? > 0 THEN 'available' ELSE status END
        WHERE book_id = ?
    """, (new_copies_available, new_copies_available, book_id))
    conn.commit()

    flash("Book returned successfully!")
    conn.close()
    return redirect("/view_users_record")



@app.route("/view_users_record", methods=['GET'])
def view_users_record():
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    search_query = request.args.get('search', '')  # Get search term
    
    try:

        if search_query:
        
         cursor.execute("""
                        SELECT users_record.users_record_id, users_record.issue_date, users_record.return_date, users_record.due_date,users_record.is_returned,
                        books.title, users.username
                        FROM users_record
                        JOIN
                        books ON books.book_id=users_record.book_id
                        JOIN
                        users ON users.user_id=users_record.user_id
                        WHERE users.username LIKE ? OR users.pa_pss_number LIKE ? OR books.title LIKE ? """, ( '%' + search_query + '%', '%' + search_query + '%', '%' + search_query + '%'))
        else:
        #fetch all users_record without filtering
            cursor.execute(""" SELECT users_record.users_record_id, users_record.issue_date, users_record.return_date, users_record.due_date, users_record.is_returned,
                       books.title, users.username
                      FROM users_record 
                     JOIN books books ON books.book_id = users_record.book_id
                     JOIN users ON users.user_id = users_record.user_id
                       """)

        view_users_record = cursor.fetchall()
        return render_template('view_users_record.html', view_users_record=view_users_record)
    except sqlite3.Error as e:
        flash(f"Database error: {e}", 'danger')
        return redirect("/view_users_record")  # Redirect back to the records page
    finally:
        conn.close()
        
        
@app.route("/add_author", methods=['GET', 'POST'])
def add_author():
    conn = get_db_connection()
    c = conn.cursor()
    
    # Fetch all authors first (so authors variable is always assigned)
    c.execute("SELECT * FROM authors ORDER BY author_id DESC")
    authors = c.fetchall()
    
    if request.method == 'POST':
        name = request.form.get('name')
         # Basic validation for empty input
        if not name:
            flash("Author name cannot be empty.")
            return render_template("add_update_author.html", authors=authors)


        c.execute("SELECT COUNT(*) FROM authors WHERE name = ?", (name,))
        if c.fetchone()[0] > 0:
                flash("Author already exists!")
                return render_template("add_update_author.html", authors=authors)

        c.execute("""INSERT INTO authors (name)
                        VALUES (?)""", (name,))
        conn.commit()
            
            # Redirect to the authors list page
        flash("Author added successfully!", "success")
        

        
        conn.close()
        return redirect("/authors")
    
    return render_template("add_update_author.html", authors=authors)

# Update author
@app.route('/update_author/<int:author_id>', methods=['GET','POST'])
def update_author(author_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
            name = request.form.get('name')
            if not name:
                flash("Name cannot be empty!")
                return redirect (f"/update_author/{author_id}")
            if name:  # If  name exists, update the author
        
                c.execute(""" UPDATE authors SET name = ? WHERE author_id = ?
             """, (name, author_id))
            conn.commit()
            conn.close()
            flash("Author updated successfully!")
            return redirect('/authors')
    else: # 

    # If GET request, fetch author details to show in form
        c.execute("SELECT * FROM authors WHERE author_id = ?", (author_id,))
        author = c.fetchone()
        
        
        c.execute("SELECT * FROM authors WHERE is_deleted = 0 ORDER BY author_id DESC")
    authors = c.fetchall()
    conn.close()

    if author:
        return render_template("add_update_author.html", author=author, authors=authors)  # Show form with existing data
    return "Author not found", 404
    
# view all author
@app.route('/authors', methods=['GET'])
def authors():
    search_query = request.args.get('search', '').strip()
    conn = get_db_connection()
    c = conn.cursor()   

    if search_query:
        c.execute("SELECT author_id, name FROM authors WHERE is_deleted = 0 AND name LIKE ?", ('%' + search_query + '%',))
    else:
        c.execute("SELECT author_id, name FROM authors WHERE is_deleted = 0 ORDER BY author_id DESC")

    authors = c.fetchall()
    conn.close()
    return render_template("authors.html", authors=authors, search_query=search_query)


#soft delete author
@app.route('/delete_author<int:author_id>', methods=['POST'])
def soft_delete_author(author_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""UPDATE authors SET is_deleted = 1 WHERE author_id = ?""", (author_id,))
    conn.commit()
    conn.close()
    flash("Author deleted successfully!", "success")
    return redirect('/authors')
    


# view publishers
@app.route('/publishers', methods=['GET'])
def publishers():
   
    search_query = request.args.get('search', '').strip()
    conn = get_db_connection()
    c = conn.cursor()   

    if search_query:
        c.execute("SELECT publisher_id, name FROM publishers WHERE is_deleted = 0 AND name LIKE ?", ('%' + search_query + '%',))
    else:
        c.execute("SELECT publisher_id, name FROM publishers WHERE is_deleted = 0 ORDER BY publisher_id DESC")

    publishers = c.fetchall()
    conn.close()
    return render_template("publishers.html", publishers=publishers, search_query=search_query)


# add new publishers
@app.route('/add_publisher', methods=['GET', 'POST'])
def add_publisher():
     conn = get_db_connection()
     c = conn.cursor()
    
    # Fetch all publishers first 
     c.execute("SELECT * FROM publishers WHERE is_deleted = 0 ORDER BY publisher_id DESC")
     publishers = c.fetchall()
     if request.method == 'POST':
         name = request.form.get('name')
         if not name:
             flash("Name field is required!")
             return redirect('/add_publisher', publishers=publishers)  # Fixed redirect
        
         conn = get_db_connection()
         c = conn.cursor()  # Fixed cursor usage
         c.execute("SELECT * FROM publishers WHERE name = ?", (name,))
         existing_publisher = c.fetchone()

         if existing_publisher:
             flash("Publisher already exists!", "warning")
         else:
             c.execute("INSERT INTO publishers(name) VALUES(?)", (name,))
             conn.commit()
             flash("Publisher added successfully!", "success")

         conn.close()
         return redirect("/publishers")  

     return render_template("add_update_publisher.html", publishers=publishers)  

# update publisher
@app.route('/update_publisher/<int:publisher_id>', methods=['GET', 'POST'])
def update_publisher(publisher_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    if request.method == 'POST':
            name = request.form.get('name')
            if not name:
                flash("Name cannot be empty!")
                return redirect (f"/update_publisher/{publisher_id}")
            if name:  # If  name exists, update the author
        
                c.execute(""" UPDATE publishers SET name = ? WHERE publisher_id = ?
             """, (name, publisher_id))
            conn.commit()
            conn.close()
            flash("Pubisher updated successfully!")
            return redirect('/publishers')
    else: # 

    # If GET request, fetch author details to show in form
        c.execute("SELECT * FROM publishers WHERE publisher_id = ?", (publisher_id,))
        publisher = c.fetchone()
        
        
    c.execute("SELECT * FROM publishers WHERE is_deleted = 0 ORDER BY publisher_id DESC")
    publishers = c.fetchall()
    conn.close()
    if publisher:
        return render_template("add_update_publisher.html", publisher=publisher, publishers=publishers)  # Show form with existing data
    return "Publisher not found", 404
    
#soft delete publisher
@app.route("/delete_publisher<int:publisher_id>", methods=['POST'])
def soft_delete_publisher(publisher_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("UPDATE publishers SET is_deleted = 1 WHERE publisher_id = ?", (publisher_id,))
    conn.commit()
    conn.close()
    
    flash("Publisher deleted successfully!", "success")
    return redirect('/publishers')
    
    
    
# view genres
@app.route('/genres', methods=['GET'])
def genres():
   search_query = request.args.get('search', '').strip()
   conn = get_db_connection()
   c = conn.cursor()   

   if search_query:
        c.execute("SELECT genre_id, genre_name FROM genres WHERE is_deleted = 0 AND  genre_name LIKE ?", ('%' + search_query + '%',))
   else:
        c.execute("SELECT genre_id, genre_name FROM genres WHERE is_deleted = 0 ORDER BY genre_id DESC")

   genres = c.fetchall()
   conn.close()
   return render_template("genres.html", genres=genres, search_query=search_query)

   

# add new genres
@app.route('/add_genre', methods=['GET', 'POST'])
def add_genre():
     conn = get_db_connection()
     c = conn.cursor()
    
    # Fetch all genres first 
     c.execute("SELECT * FROM genres  WHERE is_deleted = 0 ORDER BY genre_id DESC")
     genres = c.fetchall()
     
     if request.method == 'POST':
        genre_name = request.form.get('genre_name')
        
        if not genre_name:
            flash("Name field is required!")
            return redirect('/add_genre')  # Fixed redirect
         
                # Check if genre already exists
        c.execute("SELECT COUNT(*) FROM genres WHERE genre_name = ?", (genre_name,))
        if c.fetchone()[0] > 0:
            flash("Genre already exists!")
            return redirect('/add_genre', genres=genres)
        
        c.execute("INSERT INTO genres(genre_name) VALUES(?)", (genre_name,))
        conn.commit()  # Fixed commit usage
        flash("Genre added successfully!")
        return redirect("/genres")  # Redirecting to genres list

     return render_template("add_update_genre.html", genres=genres)  # Fixed template name

# update genre
@app.route('/update_genre/<int:genre_id>', methods=['GET', 'POST'])
def update_genre(genre_id):
    conn = get_db_connection()
    c = conn.cursor()
    
    # fetch all genres
    c.execute("SELECT * FROM genres  WHERE is_deleted = 0 ORDER BY genre_id DESC")
    genres = c.fetchall()
    
    if request.method == 'GET':
        c.execute("SELECT * FROM genres WHERE genre_id = ?", (genre_id,))
        genre = c.fetchone()
        conn.close()

        if not genre:
            flash("Genre not found!")
            return redirect('/genres')

        return render_template('add_update_genre.html', genre=genre, genres=genres)

    elif request.method == "POST":
        genre_name = request.form.get('genre_name')
        if not genre_name:
            flash("Name field is required!")
            return redirect(f"/update_genre/{genre_id}")
        c.execute("""
             UPDATE genres
            SET genre_name = ? WHERE genre_id = ?
             """, (genre_name, genre_id))
        conn.commit()
        conn.close()
        flash("Genre updated successfully!")
        return redirect("/genres")
    
 #soft delete genre  
@app.route('/delete_genre,<int:genre_id>', methods=['POST'])
def soft_delete_genre(genre_id):
    conn = get_db_connection()
    c = conn.cursor()
    c.execute("""UPDATE genres SET is_deleted = 1 WHERE genre_id = ?""",(genre_id,))
    conn.commit()
    conn.close()
    flash("Genre deleted successfully", "success")
    return redirect('/genres')


if __name__ == '__main__':
    app.run(debug=True)
 
