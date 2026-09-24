# Flight Reservation System - India Domestic Flights

A comprehensive flight booking system for domestic flights in India with separate admin and user interfaces.

## Features

### Admin Features
- **Dashboard**: Overview of flights, bookings, and system statistics
- **Flight Management**: Add/remove flight schedules, set rates
- **Airport Management**: Add new airports as they are built
- **Booking Management**: View all reservations, approve/deny booking requests
- **Seat Management**: View which seats are reserved for each flight

### User Features
- **Flight Search**: Search flights by cities and dates
- **Seat Selection**: Interactive seat map for choosing preferred seats
- **Booking Management**: View all booked flights and seat information
- **Payment System**: Dummy payment window with automatic approval
- **City Selection**: Easy selection of departure and arrival cities

## Setup Instructions

1. **Install Python Dependencies**
   ```bash
   pip install Flask==2.3.3 Werkzeug==2.3.7
   ```

2. **Run the Application**
   ```bash
   python app.py
   ```

3. **Access the Application**
   - Open your browser and go to: `http://localhost:5000`

## Default Login Credentials

### Admin Account
- **Username**: admin
- **Password**: admin123

### User Account
- Create a new user account by registering on the website

## Pre-loaded Data

The system comes with:
- **10 major Indian airports** (Delhi, Mumbai, Bengaluru, Chennai, Kolkata, Hyderabad, Ahmedabad, Kochi, Jaipur, Goa)
- **Default admin account**
- **Empty flight and booking tables** (ready for admin to add flights)

## Database

The system uses SQLite database (`flight_system.db`) which will be automatically created when you first run the application.

## File Structure

```
aeroplane/
├── app.py                 # Main Flask application
├── requirements.txt       # Python dependencies
├── flight_system.db      # SQLite database (created automatically)
├── templates/            # HTML templates
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── admin_flights.html
│   ├── admin_bookings.html
│   ├── admin_airports.html
│   ├── user_dashboard.html
│   ├── search_flights.html
│   ├── flight_results.html
│   ├── select_seat.html
│   └── payment.html
└── static/
    └── css/
        └── style.css     # Custom CSS styling
```

## How to Use

### As Admin:
1. Login with admin credentials
2. Add flights using the "Manage Flights" section
3. Add new airports if needed
4. Monitor bookings and approve/deny requests
5. View system statistics on the dashboard

### As User:
1. Register a new account or login
2. Search for flights by selecting cities and date
3. Select a seat from the interactive seat map
4. Fill passenger details and proceed to payment
5. Complete dummy payment (automatically approved)
6. View booking status in "My Dashboard"

## Notes

- **No Virtual Environment**: The system is designed to run without virtual environments as requested
- **Dummy Payment**: All payments are automatically approved for demo purposes
- **Domestic Only**: System is configured for Indian domestic flights only
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Seat availability updates in real-time

## Security Features

- Password hashing for user accounts
- Session management for login/logout
- Input validation and sanitization
- SQL injection protection using parameterized queries

## Browser Compatibility

Works with all modern browsers including:
- Chrome
- Firefox  
- Safari
- Edge