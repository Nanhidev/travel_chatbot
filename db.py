import sqlite3
import uuid


def execute_db_query(query, params=(), fetch=True):
  
    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()
    try:
        cursor.execute(query, params)
        if fetch:
            return cursor.fetchall()
        else:
            conn.commit()
            return cursor.rowcount  
    except sqlite3.Error as e:
        print(f"Database error: {e}")
        return None
    finally:
        conn.close()





def save_booking(booking_id, departure, destination, date, time, preferred_airline, payment_method):
    """Save booking details in the database."""
    query = '''INSERT INTO bookings (booking_id, departure, destination, date, time, preferred_airline, payment_method)
               VALUES (?, ?, ?, ?, ?, ?, ?)'''
    execute_db_query(query, (booking_id, departure, destination, date, time, preferred_airline, payment_method), fetch=False)


def save_passenger(booking_id, name, age):
    query = '''INSERT INTO passengers (booking_id, name, age) VALUES (?, ?, ?)'''
    execute_db_query(query, (booking_id, name, age), fetch=False)


def generate_id():
    return str(uuid.uuid4())[:4]


def init_db():
    """Create the required database tables if they don't exist."""
    conn = sqlite3.connect("bookings.db")
    cursor = conn.cursor()

    cursor.execute('''CREATE TABLE IF NOT EXISTS bookings (
        booking_id TEXT PRIMARY KEY,
        departure TEXT,
        destination TEXT,
        date TEXT,
        time TEXT,
        preferred_airline TEXT,
        payment_method TEXT
    )''')

    cursor.execute('''CREATE TABLE IF NOT EXISTS passengers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        booking_id TEXT,
        name TEXT,
        age INTEGER,
        FOREIGN KEY (booking_id) REFERENCES bookings(booking_id)
    )''')

    conn.commit()
    conn.close()


def fetch_booking_details(booking_id: str):
    query = """
    SELECT booking_id, departure, destination, date, time, preferred_airline, payment_method 
    FROM bookings 
    WHERE booking_id = ?
    """
    result = execute_db_query(query, (booking_id,), fetch=True)
    print(result,booking_id)
    if result:
        return result[0]  
    return None


init_db()


# booking_id =  "6543"
# details = fetch_booking_details(booking_id)

# print("Booking Details:", details)
