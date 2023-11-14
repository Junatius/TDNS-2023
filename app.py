from flask import Flask, render_template, request, redirect, url_for
import csv
from datetime import datetime
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret_key'  # Change this to a random secret key

# Replace 'YOUR_API_KEY' with your actual ipstack API key
IPSTACK_API_KEY = '5b63ae7aef14a3efcbd95426f6c4911c'

login_manager = LoginManager(app)
login_manager.login_view = 'login'


class User(UserMixin):
    def __init__(self, id, username, email, password):
        self.id = id
        self.username = username
        self.email = email
        self.password = password


# Replace this with your user data (e.g., from a database)
users = [
    User(1, 'user1', 'user1@example.com', 'password1'),
    User(2, 'user2', 'user2@example.com', 'password2')
]


@login_manager.user_loader
def load_user(user_id):
    return next((user for user in users if user.id == int(user_id)), None)


@app.after_request
def after_request(response):
    try:
        now = datetime.now()
        timestamp = now.strftime("%d/%b/%Y %H:%M:%S")
        user_location = get_user_location()
        username = current_user.username if current_user.is_authenticated else 'Guest'

        log_entry = {
            'IP': request.remote_addr,
            'Timestamp': timestamp,
            'Method': request.method,
            'Path': request.path,
            'Status': response.status_code,
            'Username': username,
            'Location': user_location
        }

        log_file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'log.csv')

        with open(log_file_path, 'a', newline='') as csvfile:
            fieldnames = ['IP', 'Timestamp', 'Method', 'Path', 'Status', 'Username', 'Location']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            if csvfile.tell() == 0:
                writer.writeheader()
            writer.writerow(log_entry)

    except Exception as e:
        print(f"Error logging action: {e}")

    return response


@app.route('/')
def home():
    return 'Welcome to the Flask Login Project!'


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = next((u for u in users if u.email == email and u.password == password), None)
        if user:
            login_user(user)
            return redirect(url_for('profile'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/profile')
@login_required
def profile():
    return f'Hello, {current_user.username}!', 200  # Example: returning a custom status code

def get_user_location():
    try:
        # Get the real user IP address from the headers
        user_ip = request.headers.get('X-Forwarded-For', request.remote_addr)

        # Make the API request using the user's real IP
        response = requests.get(f'http://api.ipstack.com/{user_ip}?access_key={IPSTACK_API_KEY}')
        
        data = response.json()

        # Check if the API response contains valid data
        if 'error' in data:
            raise ValueError(f"IPStack API error: {data['error']['info']}")

        city = data.get('city', 'Unknown City')
        region = data.get('region_name', 'Unknown Region')
        country = data.get('country_name', 'Unknown Country')
        latitude = data.get('latitude', 0.0)
        longitude = data.get('longitude', 0.0)

        user_location = {
            'city': city,
            'region': region,
            'country': country,
            'latitude': latitude,
            'longitude': longitude
        }
    except Exception as e:
        print(f"Error getting user location: {e}")
        user_location = {
            'city': 'Unknown City',
            'region': 'Unknown Region',
            'country': 'Unknown Country',
            'latitude': 0.0,
            'longitude': 0.0
        }

    return user_location



if __name__ == '__main__':
    app.run(debug=True)
