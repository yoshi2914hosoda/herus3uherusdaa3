
# Flask App

This is a simple Flask app that includes user registration, user and health check listing, and a mock menu API.

## Setup and run

1. Install the dependencies:
   ```
   pip install -r requirements.txt
   ```
2. Run the app:
   ```
   python app.py
   ```
3. Visit http://127.0.0.1:5000/ in your web browser.

## API endpoints

- `/register`: User registration page. Accepts GET for the registration form and POST with 'username' and 'password' form data for registering a new user.
- `/`: Home page. Requires HTTP Basic Auth.
- `/user`: User listing page. Requires HTTP Basic Auth.
- `/healthcheck`: Health check listing page. Requires HTTP Basic Auth.
- `/menu/<int:user_id>`: Mock menu API. Requires HTTP Basic Auth.
