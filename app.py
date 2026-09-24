from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
import sqlite3
from datetime import datetime, date
import uuid

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'

# Database initialization
def init_db():
    conn = sqlite3.connect('flight_system.db')
    c = conn.cursor()
    
    # Users table
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  username TEXT UNIQUE NOT NULL,
                  password TEXT NOT NULL,
                  email TEXT NOT NULL,
                  user_type TEXT NOT NULL,
                  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    
    # Airports table
    c.execute('''CREATE TABLE IF NOT EXISTS airports
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  code TEXT UNIQUE NOT NULL,
                  name TEXT NOT NULL,
                  city TEXT NOT NULL,
                  state TEXT NOT NULL)''')
    
    # Flights table
    c.execute('''CREATE TABLE IF NOT EXISTS flights
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  flight_number TEXT UNIQUE NOT NULL,
                  airline TEXT NOT NULL,
                  departure_airport_id INTEGER,
                  arrival_airport_id INTEGER,
                  departure_date DATE NOT NULL,
                  departure_time TIME NOT NULL,
                  arrival_time TIME NOT NULL,
                  price DECIMAL(10,2) NOT NULL,
                  total_seats INTEGER DEFAULT 60,
                  available_seats INTEGER DEFAULT 60,
                  status TEXT DEFAULT 'active',
                  FOREIGN KEY (departure_airport_id) REFERENCES airports (id),
                  FOREIGN KEY (arrival_airport_id) REFERENCES airports (id))''')
    
    # Seats table
    c.execute('''CREATE TABLE IF NOT EXISTS seats
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  flight_id INTEGER,
                  seat_number TEXT NOT NULL,
                  is_booked BOOLEAN DEFAULT 0,
                  FOREIGN KEY (flight_id) REFERENCES flights (id))''')
    
    # Bookings table
    c.execute('''CREATE TABLE IF NOT EXISTS bookings
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  booking_id TEXT UNIQUE NOT NULL,
                  user_id INTEGER,
                  flight_id INTEGER,
                  seat_id INTEGER,
                  passenger_name TEXT NOT NULL,
                  passenger_email TEXT NOT NULL,
                  passenger_phone TEXT NOT NULL,
                  booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  payment_status TEXT DEFAULT 'pending',
                  booking_status TEXT DEFAULT 'pending',
                  amount DECIMAL(10,2) NOT NULL,
                  group_booking_id TEXT,
                  FOREIGN KEY (user_id) REFERENCES users (id),
                  FOREIGN KEY (flight_id) REFERENCES flights (id),
                  FOREIGN KEY (seat_id) REFERENCES seats (id))''')
    
    # Cancellation requests table
    c.execute('''CREATE TABLE IF NOT EXISTS cancellation_requests
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  booking_id INTEGER,
                  user_id INTEGER,
                  reason TEXT NOT NULL,
                  request_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                  status TEXT DEFAULT 'pending',
                  admin_response TEXT,
                  processed_date TIMESTAMP,
                  FOREIGN KEY (booking_id) REFERENCES bookings (id),
                  FOREIGN KEY (user_id) REFERENCES users (id))''')
    
    # Insert default admin user
    admin_password = generate_password_hash('admin123')
    c.execute("INSERT OR IGNORE INTO users (username, password, email, user_type) VALUES (?, ?, ?, ?)",
              ('admin', admin_password, 'admin@flightbooking.com', 'admin'))
    
    # Insert some default airports
    default_airports = [
        ('DEL', 'Indira Gandhi International Airport', 'Delhi', 'Delhi'),
        ('BOM', 'Chhatrapati Shivaji Maharaj International Airport', 'Mumbai', 'Maharashtra'),
        ('BLR', 'Kempegowda International Airport', 'Bengaluru', 'Karnataka'),
        ('MAA', 'Chennai International Airport', 'Chennai', 'Tamil Nadu'),
        ('CCU', 'Netaji Subhash Chandra Bose International Airport', 'Kolkata', 'West Bengal'),
        ('HYD', 'Rajiv Gandhi International Airport', 'Hyderabad', 'Telangana'),
        ('AMD', 'Sardar Vallabhbhai Patel International Airport', 'Ahmedabad', 'Gujarat'),
        ('COK', 'Cochin International Airport', 'Kochi', 'Kerala'),
        ('JAI', 'Jaipur International Airport', 'Jaipur', 'Rajasthan'),
        ('GOI', 'Dabolim Airport', 'Goa', 'Goa')
    ]
    
    c.executemany("INSERT OR IGNORE INTO airports (code, name, city, state) VALUES (?, ?, ?, ?)", default_airports)
    
    # Insert starter flights
    starter_flights = [
        # Delhi Routes
        ('AI101', 'Air India', 1, 2, '2024-12-01', '06:00', '08:30', 8500.00),
        ('6E201', 'IndiGo', 1, 2, '2024-12-01', '09:15', '11:45', 7800.00),
        ('SG301', 'SpiceJet', 1, 2, '2024-12-01', '14:20', '16:50', 7200.00),
        ('AI102', 'Air India', 1, 3, '2024-12-01', '07:30', '10:15', 9200.00),
        ('6E202', 'IndiGo', 1, 3, '2024-12-01', '12:00', '14:45', 8800.00),
        ('UK401', 'Vistara', 1, 4, '2024-12-01', '08:45', '11:20', 8900.00),
        ('AI103', 'Air India', 1, 5, '2024-12-01', '16:30', '18:45', 7600.00),
        ('6E203', 'IndiGo', 1, 6, '2024-12-01', '11:15', '13:30', 9100.00),
        
        # Mumbai Routes
        ('AI201', 'Air India', 2, 1, '2024-12-01', '05:45', '08:15', 8500.00),
        ('6E301', 'IndiGo', 2, 1, '2024-12-01', '13:30', '16:00', 7800.00),
        ('SG401', 'SpiceJet', 2, 1, '2024-12-01', '19:10', '21:40', 7200.00),
        ('AI202', 'Air India', 2, 3, '2024-12-01', '10:20', '11:50', 6800.00),
        ('6E302', 'IndiGo', 2, 3, '2024-12-01', '17:45', '19:15', 6200.00),
        ('UK501', 'Vistara', 2, 4, '2024-12-01', '15:15', '17:30', 7100.00),
        ('AI203', 'Air India', 2, 10, '2024-12-01', '09:00', '10:15', 5800.00),
        
        # Bangalore Routes
        ('AI301', 'Air India', 3, 1, '2024-12-01', '06:15', '08:45', 9200.00),
        ('6E401', 'IndiGo', 3, 1, '2024-12-01', '20:30', '23:00', 8800.00),
        ('SG501', 'SpiceJet', 3, 2, '2024-12-01', '12:45', '14:15', 6800.00),
        ('AI302', 'Air India', 3, 2, '2024-12-01', '18:20', '19:50', 6200.00),
        ('6E402', 'IndiGo', 3, 4, '2024-12-01', '14:30', '16:45', 7200.00),
        ('UK601', 'Vistara', 3, 6, '2024-12-01', '07:45', '09:00', 8100.00),
        ('AI303', 'Air India', 3, 8, '2024-12-01', '11:30', '12:45', 6900.00),
        
        # Chennai Routes
        ('AI401', 'Air India', 4, 1, '2024-12-01', '05:30', '08:00', 8900.00),
        ('6E501', 'IndiGo', 4, 2, '2024-12-01', '16:15', '18:30', 7100.00),
        ('SG601', 'SpiceJet', 4, 3, '2024-12-01', '13:20', '15:35', 7200.00),
        ('AI402', 'Air India', 4, 5, '2024-12-01', '09:45', '11:30', 6400.00),
        ('6E502', 'IndiGo', 4, 6, '2024-12-01', '21:00', '22:15', 7800.00),
        
        # Kolkata Routes
        ('AI501', 'Air India', 5, 1, '2024-12-01', '07:00', '09:15', 7600.00),
        ('6E601', 'IndiGo', 5, 2, '2024-12-01', '15:45', '18:15', 8200.00),
        ('SG701', 'SpiceJet', 5, 3, '2024-12-01', '10:30', '13:15', 8600.00),
        ('AI502', 'Air India', 5, 4, '2024-12-01', '19:30', '21:15', 6400.00),
        
        # Hyderabad Routes
        ('AI601', 'Air India', 6, 1, '2024-12-01', '06:45', '09:30', 8700.00),
        ('6E701', 'IndiGo', 6, 2, '2024-12-01', '14:15', '16:45', 7900.00),
        ('SG801', 'SpiceJet', 6, 3, '2024-12-01', '11:20', '12:50', 7300.00),
        ('UK701', 'Vistara', 6, 4, '2024-12-01', '17:30', '19:45', 7500.00),
        
        # Ahmedabad Routes
        ('AI701', 'Air India', 7, 1, '2024-12-01', '08:30', '10:45', 6800.00),
        ('6E801', 'IndiGo', 7, 2, '2024-12-01', '16:45', '18:30', 6200.00),
        ('SG901', 'SpiceJet', 7, 3, '2024-12-01', '12:15', '15:00', 7800.00),
        
        # Kochi Routes  
        ('AI801', 'Air India', 8, 2, '2024-12-01', '09:15', '11:45', 7400.00),
        ('6E901', 'IndiGo', 8, 3, '2024-12-01', '18:20', '19:35', 6900.00),
        ('SG1001', 'SpiceJet', 8, 4, '2024-12-01', '14:30', '16:45', 7100.00),
        
        # Jaipur Routes
        ('AI901', 'Air India', 9, 1, '2024-12-01', '07:15', '08:30', 5200.00),
        ('6E1001', 'IndiGo', 9, 2, '2024-12-01', '13:45', '17:15', 8100.00),
        ('SG1101', 'SpiceJet', 9, 3, '2024-12-01', '20:00', '22:45', 8500.00),
        
        # Goa Routes
        ('AI1001', 'Air India', 10, 2, '2024-12-01', '10:30', '11:45', 5800.00),
        ('6E1101', 'IndiGo', 10, 3, '2024-12-01', '15:20', '16:35', 6300.00),
        ('SG1201', 'SpiceJet', 10, 1, '2024-12-01', '21:15', '23:30', 7700.00),
        
        # Additional Popular Routes for Dec 2nd
        ('AI104', 'Air India', 1, 2, '2024-12-02', '07:00', '09:30', 8500.00),
        ('6E204', 'IndiGo', 1, 2, '2024-12-02', '15:15', '17:45', 7800.00),
        ('AI204', 'Air India', 2, 1, '2024-12-02', '06:30', '09:00', 8500.00),
        ('6E304', 'IndiGo', 2, 1, '2024-12-02', '18:20', '20:50', 7800.00),
        ('AI304', 'Air India', 3, 1, '2024-12-02', '08:15', '10:45', 9200.00),
        ('6E404', 'IndiGo', 3, 2, '2024-12-02', '16:30', '18:00', 6800.00)
    ]
    
    # Insert flights if they don't exist
    for flight_data in starter_flights:
        existing_flight = c.execute('SELECT id FROM flights WHERE flight_number = ?', (flight_data[0],)).fetchone()
        if not existing_flight:
            cursor = c.execute('''INSERT INTO flights 
                        (flight_number, airline, departure_airport_id, arrival_airport_id, 
                         departure_date, departure_time, arrival_time, price)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?)''', flight_data)
            
            flight_id = cursor.lastrowid
            
            # Generate seats for each flight (60 seats total)
            seats = []
            for row in range(1, 11):  # 10 rows
                for seat in ['A', 'B', 'C', 'D', 'E', 'F']:  # 6 seats per row
                    seat_number = f"{row}{seat}"
                    seats.append((flight_id, seat_number))
            
            c.executemany('INSERT INTO seats (flight_id, seat_number) VALUES (?, ?)', seats)
    
    conn.commit()
    conn.close()

def get_db_connection():
    conn = sqlite3.connect('flight_system.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        conn.close()
        
        if user and check_password_hash(user['password'], password):
            session['user_id'] = user['id']
            session['username'] = user['username']
            session['user_type'] = user['user_type']
            
            if user['user_type'] == 'admin':
                return redirect(url_for('admin_dashboard'))
            else:
                return redirect(url_for('user_dashboard'))
        else:
            flash('Invalid username or password')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        email = request.form['email']
        
        conn = get_db_connection()
        
        # Check if username already exists
        existing_user = conn.execute('SELECT * FROM users WHERE username = ?', (username,)).fetchone()
        if existing_user:
            flash('Username already exists')
            conn.close()
            return render_template('register.html')
        
        # Create new user
        hashed_password = generate_password_hash(password)
        conn.execute('INSERT INTO users (username, password, email, user_type) VALUES (?, ?, ?, ?)',
                     (username, hashed_password, email, 'user'))
        conn.commit()
        conn.close()
        
        flash('Registration successful! Please login.')
        return redirect(url_for('login'))
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

# Admin routes
@app.route('/admin/dashboard')
def admin_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        flash('Access denied. Admin login required.')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get statistics
    total_flights = conn.execute('SELECT COUNT(*) as count FROM flights WHERE status = "active"').fetchone()['count']
    total_bookings = conn.execute('SELECT COUNT(*) as count FROM bookings').fetchone()['count']
    pending_bookings = conn.execute('SELECT COUNT(*) as count FROM bookings WHERE booking_status = "pending"').fetchone()['count']
    total_airports = conn.execute('SELECT COUNT(*) as count FROM airports').fetchone()['count']
    
    # Get recent bookings
    recent_bookings = conn.execute('''
        SELECT b.*, f.flight_number, f.airline, 
               dep.city as departure_city, arr.city as arrival_city,
               u.username, s.seat_number
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports dep ON f.departure_airport_id = dep.id
        JOIN airports arr ON f.arrival_airport_id = arr.id
        JOIN users u ON b.user_id = u.id
        JOIN seats s ON b.seat_id = s.id
        ORDER BY b.booking_date DESC
        LIMIT 10
    ''').fetchall()
    
    conn.close()
    
    return render_template('admin_dashboard.html', 
                         total_flights=total_flights,
                         total_bookings=total_bookings,
                         pending_bookings=pending_bookings,
                         total_airports=total_airports,
                         recent_bookings=recent_bookings)

@app.route('/admin/flights')
def admin_flights():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    flights = conn.execute('''
        SELECT f.*, dep.name as departure_airport, arr.name as arrival_airport,
               dep.city as departure_city, arr.city as arrival_city
        FROM flights f
        JOIN airports dep ON f.departure_airport_id = dep.id
        JOIN airports arr ON f.arrival_airport_id = arr.id
        ORDER BY f.departure_date DESC
    ''').fetchall()
    
    airports = conn.execute('SELECT * FROM airports ORDER BY city').fetchall()
    conn.close()
    
    return render_template('admin_flights.html', flights=flights, airports=airports)

@app.route('/admin/add_flight', methods=['POST'])
def add_flight():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    flight_number = request.form['flight_number']
    airline = request.form['airline']
    departure_airport = request.form['departure_airport']
    arrival_airport = request.form['arrival_airport']
    departure_date = request.form['departure_date']
    departure_time = request.form['departure_time']
    arrival_time = request.form['arrival_time']
    price = request.form['price']
    
    conn = get_db_connection()
    
    # Check if flight number already exists
    existing_flight = conn.execute('SELECT * FROM flights WHERE flight_number = ?', (flight_number,)).fetchone()
    if existing_flight:
        flash('Flight number already exists')
        conn.close()
        return redirect(url_for('admin_flights'))
    
    # Add flight
    cursor = conn.execute('''INSERT INTO flights 
                    (flight_number, airline, departure_airport_id, arrival_airport_id, 
                     departure_date, departure_time, arrival_time, price)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                 (flight_number, airline, departure_airport, arrival_airport,
                  departure_date, departure_time, arrival_time, price))
    
    flight_id = cursor.lastrowid
    
    # Generate seats for the flight (60 seats total)
    seats = []
    for row in range(1, 11):  # 10 rows
        for seat in ['A', 'B', 'C', 'D', 'E', 'F']:  # 6 seats per row
            seat_number = f"{row}{seat}"
            seats.append((flight_id, seat_number))
    
    conn.executemany('INSERT INTO seats (flight_id, seat_number) VALUES (?, ?)', seats)
    
    conn.commit()
    conn.close()
    
    flash('Flight added successfully!')
    return redirect(url_for('admin_flights'))

@app.route('/admin/remove_flight/<int:flight_id>')
def remove_flight(flight_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('UPDATE flights SET status = "cancelled" WHERE id = ?', (flight_id,))
    conn.commit()
    conn.close()
    
    flash('Flight cancelled successfully!')
    return redirect(url_for('admin_flights'))

@app.route('/admin/bookings')
def admin_bookings():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    bookings = conn.execute('''
        SELECT b.*, f.flight_number, f.airline, f.departure_date,
               dep.city as departure_city, arr.city as arrival_city,
               u.username, s.seat_number
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports dep ON f.departure_airport_id = dep.id
        JOIN airports arr ON f.arrival_airport_id = arr.id
        JOIN users u ON b.user_id = u.id
        JOIN seats s ON b.seat_id = s.id
        ORDER BY b.booking_date DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin_bookings.html', bookings=bookings)

@app.route('/admin/approve_booking/<int:booking_id>')
def approve_booking(booking_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    conn.execute('UPDATE bookings SET booking_status = "approved" WHERE id = ?', (booking_id,))
    conn.commit()
    conn.close()
    
    flash('Booking approved successfully!')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/deny_booking/<int:booking_id>')
def deny_booking(booking_id):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    # Get booking details to free up the seat
    booking = conn.execute('SELECT * FROM bookings WHERE id = ?', (booking_id,)).fetchone()
    if booking:
        conn.execute('UPDATE seats SET is_booked = 0 WHERE id = ?', (booking['seat_id'],))
        conn.execute('UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?', (booking['flight_id'],))
        conn.execute('UPDATE bookings SET booking_status = "denied" WHERE id = ?', (booking_id,))
    
    conn.commit()
    conn.close()
    
    flash('Booking denied successfully!')
    return redirect(url_for('admin_bookings'))

@app.route('/admin/airports')
def admin_airports():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    airports = conn.execute('SELECT * FROM airports ORDER BY city').fetchall()
    conn.close()
    
    return render_template('admin_airports.html', airports=airports)

@app.route('/admin/add_airport', methods=['POST'])
def add_airport():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    code = request.form['code'].upper()
    name = request.form['name']
    city = request.form['city']
    state = request.form['state']
    
    conn = get_db_connection()
    
    # Check if airport code already exists
    existing_airport = conn.execute('SELECT * FROM airports WHERE code = ?', (code,)).fetchone()
    if existing_airport:
        flash('Airport code already exists')
        conn.close()
        return redirect(url_for('admin_airports'))
    
    conn.execute('INSERT INTO airports (code, name, city, state) VALUES (?, ?, ?, ?)',
                 (code, name, city, state))
    conn.commit()
    conn.close()
    
    flash('Airport added successfully!')
    return redirect(url_for('admin_airports'))

@app.route('/admin/cancellations')
def admin_cancellations():
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    cancellations = conn.execute('''
        SELECT cr.*, b.booking_id, b.passenger_name, b.passenger_email, b.booking_date,
               f.flight_number, f.airline, f.departure_date,
               dep.city as departure_city, arr.city as arrival_city,
               s.seat_number, u.username
        FROM cancellation_requests cr
        JOIN bookings b ON cr.booking_id = b.id
        JOIN flights f ON b.flight_id = f.id
        JOIN airports dep ON f.departure_airport_id = dep.id
        JOIN airports arr ON f.arrival_airport_id = arr.id
        JOIN seats s ON b.seat_id = s.id
        JOIN users u ON cr.user_id = u.id
        ORDER BY cr.request_date DESC
    ''').fetchall()
    conn.close()
    
    return render_template('admin_cancellations.html', cancellations=cancellations)

@app.route('/admin/process_cancellation/<int:request_id>/<action>')
def process_cancellation(request_id, action):
    if 'user_id' not in session or session.get('user_type') != 'admin':
        return redirect(url_for('login'))
    
    if action not in ['approve', 'deny']:
        flash('Invalid action')
        return redirect(url_for('admin_cancellations'))
    
    conn = get_db_connection()
    
    # Get cancellation request details
    cancellation = conn.execute('''
        SELECT cr.*, b.* FROM cancellation_requests cr
        JOIN bookings b ON cr.booking_id = b.id
        WHERE cr.id = ?
    ''', (request_id,)).fetchone()
    
    if not cancellation:
        flash('Cancellation request not found')
        conn.close()
        return redirect(url_for('admin_cancellations'))
    
    if action == 'approve':
        # Update booking status to cancelled
        conn.execute('UPDATE bookings SET booking_status = "cancelled" WHERE id = ?', 
                     (cancellation['booking_id'],))
        
        # Free up the seat
        conn.execute('UPDATE seats SET is_booked = 0 WHERE id = ?', 
                     (cancellation['seat_id'],))
        
        # Increase available seats
        conn.execute('UPDATE flights SET available_seats = available_seats + 1 WHERE id = ?', 
                     (cancellation['flight_id'],))
        
        # Update cancellation request
        conn.execute('UPDATE cancellation_requests SET status = "approved", processed_date = CURRENT_TIMESTAMP WHERE id = ?', 
                     (request_id,))
        
        flash('Cancellation approved successfully!')
    
    elif action == 'deny':
        # Update cancellation request
        conn.execute('UPDATE cancellation_requests SET status = "denied", processed_date = CURRENT_TIMESTAMP WHERE id = ?', 
                     (request_id,))
        
        flash('Cancellation request denied!')
    
    conn.commit()
    conn.close()
    
    return redirect(url_for('admin_cancellations'))

# User routes
@app.route('/user/dashboard')
def user_dashboard():
    if 'user_id' not in session or session.get('user_type') != 'user':
        flash('Please login to access user dashboard.')
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Get user's bookings
    user_bookings = conn.execute('''
        SELECT b.*, f.flight_number, f.airline, f.departure_date, f.departure_time,
               dep.city as departure_city, arr.city as arrival_city,
               s.seat_number
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports dep ON f.departure_airport_id = dep.id
        JOIN airports arr ON f.arrival_airport_id = arr.id
        JOIN seats s ON b.seat_id = s.id
        WHERE b.user_id = ?
        ORDER BY b.booking_date DESC
    ''', (session['user_id'],)).fetchall()
    
    conn.close()
    
    return render_template('user_dashboard.html', bookings=user_bookings)

@app.route('/search_flights')
def search_flights():
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    airports = conn.execute('SELECT * FROM airports ORDER BY city').fetchall()
    conn.close()
    
    return render_template('search_flights.html', airports=airports)

@app.route('/flight_results')
def flight_results():
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    departure_city = request.args.get('departure_city')
    arrival_city = request.args.get('arrival_city')
    departure_date = request.args.get('departure_date')
    
    conn = get_db_connection()
    flights = conn.execute('''
        SELECT f.*, dep.city as departure_city, arr.city as arrival_city,
               dep.name as departure_airport, arr.name as arrival_airport
        FROM flights f
        JOIN airports dep ON f.departure_airport_id = dep.id
        JOIN airports arr ON f.arrival_airport_id = arr.id
        WHERE dep.id = ? AND arr.id = ? AND f.departure_date = ? AND f.status = "active" AND f.available_seats > 0
        ORDER BY f.departure_time
    ''', (departure_city, arrival_city, departure_date)).fetchall()
    
    conn.close()
    
    return render_template('flight_results.html', flights=flights, 
                         departure_date=departure_date)

@app.route('/select_seat/<int:flight_id>')
def select_seat(flight_id):
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    flight = conn.execute('''
        SELECT f.*, dep.city as departure_city, arr.city as arrival_city,
               dep.name as departure_airport, arr.name as arrival_airport
        FROM flights f
        JOIN airports dep ON f.departure_airport_id = dep.id
        JOIN airports arr ON f.arrival_airport_id = arr.id
        WHERE f.id = ?
    ''', (flight_id,)).fetchone()
    
    seats = conn.execute('SELECT * FROM seats WHERE flight_id = ? ORDER BY seat_number', (flight_id,)).fetchall()
    
    conn.close()
    
    return render_template('select_seat.html', flight=flight, seats=seats)

@app.route('/book_seat', methods=['POST'])
def book_seat():
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    flight_id = request.form['flight_id']
    seat_ids = request.form.getlist('seat_ids[]')
    passenger_names = request.form.getlist('passenger_names[]')
    passenger_ages = request.form.getlist('passenger_ages[]')
    passenger_emails = request.form.getlist('passenger_emails[]')
    passenger_phones = request.form.getlist('passenger_phones[]')
    
    if len(seat_ids) != len(passenger_names) or len(seat_ids) == 0:
        flash('Invalid booking data. Please try again.')
        return redirect(url_for('select_seat', flight_id=flight_id))
    
    conn = get_db_connection()
    
    # Check if all seats are still available
    for seat_id in seat_ids:
        seat = conn.execute('SELECT * FROM seats WHERE id = ? AND is_booked = 0', (seat_id,)).fetchone()
        if not seat:
            flash('One or more selected seats are no longer available')
            conn.close()
            return redirect(url_for('select_seat', flight_id=flight_id))
    
    # Get flight price
    flight = conn.execute('SELECT price FROM flights WHERE id = ?', (flight_id,)).fetchone()
    
    # Create group booking ID for multiple seats
    group_booking_id = str(uuid.uuid4())[:12].upper()
    total_amount = len(seat_ids) * flight['price']
    
    # Create individual bookings for each passenger/seat
    for i in range(len(seat_ids)):
        booking_id = str(uuid.uuid4())[:8].upper()
        
        conn.execute('''INSERT INTO bookings 
                        (booking_id, user_id, flight_id, seat_id, passenger_name, 
                         passenger_email, passenger_phone, amount, group_booking_id)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                     (booking_id, session['user_id'], flight_id, seat_ids[i],
                      passenger_names[i], passenger_emails[i], passenger_phones[i], 
                      flight['price'], group_booking_id))
        
        # Mark seat as booked
        conn.execute('UPDATE seats SET is_booked = 1 WHERE id = ?', (seat_ids[i],))
    
    # Decrease available seats
    conn.execute('UPDATE flights SET available_seats = available_seats - ? WHERE id = ?', 
                 (len(seat_ids), flight_id))
    
    conn.commit()
    conn.close()
    
    # Redirect to payment with group booking ID
    return redirect(url_for('payment', booking_id=group_booking_id))

@app.route('/payment/<booking_id>')
def payment(booking_id):
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    conn = get_db_connection()
    
    # Check if it's a group booking or individual booking
    group_bookings = conn.execute('''
        SELECT b.*, f.flight_number, f.airline, f.departure_date, f.departure_time,
               dep.city as departure_city, arr.city as arrival_city,
               s.seat_number
        FROM bookings b
        JOIN flights f ON b.flight_id = f.id
        JOIN airports dep ON f.departure_airport_id = dep.id
        JOIN airports arr ON f.arrival_airport_id = arr.id
        JOIN seats s ON b.seat_id = s.id
        WHERE b.group_booking_id = ? AND b.user_id = ?
    ''', (booking_id, session['user_id'])).fetchall()
    
    if not group_bookings:
        # Try individual booking
        booking = conn.execute('''
            SELECT b.*, f.flight_number, f.airline, f.departure_date, f.departure_time,
                   dep.city as departure_city, arr.city as arrival_city,
                   s.seat_number
            FROM bookings b
            JOIN flights f ON b.flight_id = f.id
            JOIN airports dep ON f.departure_airport_id = dep.id
            JOIN airports arr ON f.arrival_airport_id = arr.id
            JOIN seats s ON b.seat_id = s.id
            WHERE b.booking_id = ? AND b.user_id = ?
        ''', (booking_id, session['user_id'])).fetchone()
        
        if not booking:
            flash('Booking not found')
            conn.close()
            return redirect(url_for('user_dashboard'))
        
        conn.close()
        return render_template('payment.html', booking=booking, is_group=False)
    
    # Calculate total amount for group booking
    total_amount = sum(booking['amount'] for booking in group_bookings)
    
    conn.close()
    
    return render_template('payment.html', bookings=group_bookings, 
                         total_amount=total_amount, group_booking_id=booking_id, is_group=True)

@app.route('/process_payment', methods=['POST'])
def process_payment():
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    booking_id = request.form['booking_id']
    is_group = request.form.get('is_group') == 'true'
    
    # Dummy payment processing - automatically approve
    conn = get_db_connection()
    
    if is_group:
        # Update all bookings in the group
        conn.execute('UPDATE bookings SET payment_status = "completed" WHERE group_booking_id = ? AND user_id = ?',
                     (booking_id, session['user_id']))
    else:
        # Update individual booking
        conn.execute('UPDATE bookings SET payment_status = "completed" WHERE booking_id = ? AND user_id = ?',
                     (booking_id, session['user_id']))
    
    conn.commit()
    conn.close()
    
    flash('Payment successful! Your booking is confirmed.')
    return redirect(url_for('user_dashboard'))

@app.route('/request_cancellation', methods=['POST'])
def request_cancellation():
    if 'user_id' not in session or session.get('user_type') != 'user':
        return redirect(url_for('login'))
    
    booking_id = request.form['booking_id']
    reason = request.form['reason']
    
    conn = get_db_connection()
    
    # Check if booking exists and belongs to user
    booking = conn.execute('SELECT * FROM bookings WHERE id = ? AND user_id = ?', 
                          (booking_id, session['user_id'])).fetchone()
    
    if not booking:
        flash('Booking not found')
        conn.close()
        return redirect(url_for('user_dashboard'))
    
    if booking['booking_status'] != 'approved':
        flash('Only confirmed bookings can be cancelled')
        conn.close()
        return redirect(url_for('user_dashboard'))
    
    # Check if cancellation request already exists
    existing_request = conn.execute('SELECT * FROM cancellation_requests WHERE booking_id = ?', 
                                   (booking_id,)).fetchone()
    
    if existing_request:
        flash('Cancellation request already submitted')
        conn.close()
        return redirect(url_for('user_dashboard'))
    
    # Create cancellation request
    conn.execute('''INSERT INTO cancellation_requests 
                    (booking_id, user_id, reason) 
                    VALUES (?, ?, ?)''',
                 (booking_id, session['user_id'], reason))
    
    conn.commit()
    conn.close()
    
    flash('Cancellation request submitted successfully. Admin will review your request.')
    return redirect(url_for('user_dashboard'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)