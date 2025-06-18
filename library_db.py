import sqlite3
# connect to the sqlite database


conn = sqlite3.connect('library.db')
c = conn.cursor()


# enable foreign key constraints
c.execute("PRAGMA foreign_keys = OFF")


# create the genres table
c.execute("""
        CREATE TABLE IF NOT EXISTS genres(
                genre_id INTEGER PRIMARY KEY AUTOINCREMENT,
                genre_name TEXT NOT NULL
        )
 """)
# create the publishers table


c.execute("""
          CREATE TABLE IF NOT EXISTS publishers(
                  publisher_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  name TEXT  NOT NULL
          )
""")




# create the authors table
c.execute("""
          CREATE TABLE IF NOT EXISTS authors(
            author_id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL      
          )
""")
# create the books table


c.execute("""
          CREATE TABLE IF NOT EXISTS books(
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            isbn TEXT NOT NULL,
            edition INTEGER NOT NULL,
            copies_total INTEGER NOT NULL,
            copies_available INTEGER NOT NULL,
            shelf_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            published_year INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            publisher_id INTEGER NOT NULL,
            genre_id INTEGER NOT NULL,
            FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE,
            FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id) ON DELETE CASCADE,
            FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE
                       
    )
""")


# Create the users table with the new `is_delete` column
c.execute("""
          CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL,
                pa_pss_number TEXT UNIQUE NOT NULL CHECK(pa_pss_number LIKE 'PA%' OR pa_pss_number LIKE 'PSS%'),
                 email_id TEXT NOT NULL,
                 phone_number TEXT NOT NULL,
                address TEXT NOT NULL,
                is_active BOOLEAN NOT NULL DEFAULT 0,
                date_activated DATE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                is_delete BOOLEAN DEFAULT 0
 )
""")




# Create the Users_record table


c.execute("""
          CREATE TABLE IF NOT EXISTS  users_record(
                  users_record_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  issue_date DATE NOT NULL DEFAULT CURRENT_TIMESTAMP,
                  return_date DATE NULL,
                  due_date DATE NOT NULL,
                  is_returned BOOLEAN NOT NULL DEFAULT 0,   --- 0 = Not Returned, 1 = Returned
                  book_id INTEGER NOT NULL,
                  user_id INTEGER NOT NULL,
                  FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
                  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE
          )
""")


# Create the reservation table


c.execute("""
          CREATE  TABLE IF NOT EXISTS reserve_a_book(
                  reserve_a_book_id INTEGER PRIMARY KEY AUTOINCREMENT,
                  reservation_date DATE NOT NULL  DEFAULT CURRENT_TIMESTAMP,
                  expiration_date DATE NOT NULL, --- set based on library policy
                  reservation_status TEXT NOT NULL, 
                  user_id INTEGER NOT NULL,
                  book_id INTEGER NOT NULL,
                  FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE ,
                  FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE
                 
          )
""")




# create admin to manage the library
c.execute("""CREATE TABLE IF NOT EXISTS admin (
    admin_id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    email_id TEXT NOT NULL,
    phone_number TEXT NOT NULL,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    date_created DATE NOT NULL DEFAULT CURRENT_TIMESTAMP
)""")

# Create unique index on isbn
c.execute("CREATE UNIQUE INDEX IF NOT EXISTS idx_isbn ON books(isbn)")
c.execute("DROP TABLE reserve_a_book" )


#alter 'publishers'
c.execute("PRAGMA table_info(publishers);")
columns = c.fetchall()
column_names = [column[1] for column in columns]  # Extracting column names
if "is_deleted" not in column_names:
        c.execute("""ALTER TABLE publishers ADD COLUMN is_deleted BOOLEAN DEFAULT 0;
""")

#alter 'authors'
c.execute("PRAGMA table_info(authors);")
columns = c.fetchall()
column_names = [column[1] for column in columns]  # Extracting column names
if "is_deleted" not in column_names:
        c.execute("""ALTER TABLE authors ADD COLUMN is_deleted BOOLEAN DEFAULT 0;
          """)
#alter genres
c.execute("PRAGMA table_info(genres);")
columns = c.fetchall()
column_names = [column[1] for column in columns]  # Extracting column names
if "is_deleted" not in column_names:
        c.execute("""ALTER TABLE genres ADD COLUMN is_deleted BOOLEAN DEFAULT 0;
          """)
# create table book_genres for many-to-many relationship
c.execute("""CREATE TABLE IF NOT EXISTS book_genres (
    book_id INTEGER,
    genre_id INTEGER,
    FOREIGN KEY (book_id) REFERENCES books(book_id) ON DELETE CASCADE,
    FOREIGN KEY (genre_id) REFERENCES genres(genre_id) ON DELETE CASCADE,
    PRIMARY KEY (book_id, genre_id))
          """)



# create table new_book
c.execute("""
          CREATE TABLE IF NOT EXISTS new_books(
            book_id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            isbn TEXT NOT NULL,
            edition TEXT  NOT NULL,
            copies_total INTEGER NOT NULL,
            copies_available INTEGER NOT NULL,
            shelf_number INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'available',
            published_year INTEGER NOT NULL,
            author_id INTEGER NOT NULL,
            publisher_id INTEGER NOT NULL,
            FOREIGN KEY (author_id) REFERENCES authors(author_id) ON DELETE CASCADE,
            FOREIGN KEY (publisher_id) REFERENCES publishers(publisher_id) ON DELETE CASCADE                
)
        """)
# copy data into new_book
c.execute('''INSERT INTO new_books (book_id, title, ISBN, edition, copies_total, copies_available, shelf_number, status, author_id, publisher_id, published_year)
SELECT book_id, title, ISBN, edition, copies_total, copies_available, shelf_number, status, author_id, publisher_id, published_year
FROM books''')

# drop old table
c.execute('''DROP TABLE books;
          ''')
c.execute('''DROP TRIGGER IF EXISTS update_copies_and_status''')

#Alter new table 
c.execute('''ALTER TABLE new_books RENAME TO books;

          ''')
c.execute('''DROP TABLE IF EXISTS new_users ''')


# commit and close the connection
conn.commit()
conn.close()


   
   
   



