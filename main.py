import os
import base64
import json
import mysql.connector
from flask import Flask, send_file, request, redirect, url_for, render_template, flash, jsonify, session

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Database configuration
db_config = {
    'user': 'root',
    'password': '6304G.Vik@s',
    'host': 'localhost',
    'database': 'voter_registration'
}

# ✅ Test MySQL Connection
try:
    conn = mysql.connector.connect(**db_config)
    conn.close()
    print("✅ Database connection successful!")
except mysql.connector.Error as err:
    print(f"❌ Database connection failed: {err}")

# ✅ Ensure JSON Files Exist
for file in ["users.json", "profile.json"]:
    if not os.path.exists(file):
        with open(file, "w") as f:
            json.dump([], f, indent=4)

@app.route("/")
def home():
    return send_file('src/index.html')

@app.route("/login")
def login():
    return send_file('src/login.html')

@app.route("/signup")
def signup():
    return send_file('src/signup.html')

@app.route("/vportal", methods=["GET", "POST"])
def vportal():
    voter = None
    if request.method == "POST":
        aadhar = request.form["aadhar"]
        try:
            conn = mysql.connector.connect(**db_config)
            cursor = conn.cursor(dictionary=True)
            cursor.execute("SELECT * FROM voters WHERE aadhar = %s", (aadhar,))
            voter = cursor.fetchone()
            cursor.close()
            conn.close()

            if voter:
                # Encode binary data to Base64
                voter["fingerprint"] = base64.b64encode(voter["fingerprint"]).decode("utf-8") if voter["fingerprint"] else None
                voter["face"] = base64.b64encode(voter["face"]).decode("utf-8") if voter["face"] else None
            else:
                flash("❌ No voter found with this Aadhar number.", "danger")

        except mysql.connector.Error as err:
            flash(f"❌ Database error: {err}", "danger")

    return render_template("vportal.html", voter=voter)

@app.route("/qrportal")
def qrportal():
    return send_file('src/qrportal.html') 

@app.route("/faportal")
def faportal():
    return send_file('src/faportal.html') 

@app.route("/registration")
def registration():
    return send_file('src/registration.html') 

@app.route("/profile")
def profile():
    return send_file('src/profile.html')

@app.route("/submit", methods=["POST"])
def submit():
    username = request.form["username"]
    password = request.form["password"]

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = []

    for user in users:
        if user["username"] == username and user["password"] == password:
            session['logged_in'] = True
            return redirect(url_for("home"))

    return '❌ Invalid credentials'

@app.route("/signup-submit", methods=["POST"])
def signup_submit():
    username = request.form["username"]
    email = request.form["email"]
    password = request.form["password"]

    new_user = {"username": username, "email": email, "password": password}

    try:
        with open("users.json", "r") as f:
            users = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        users = []

    if any(user['username'] == username or user['email'] == email for user in users):
        return render_template("signup.html", errorMessage='❌ Username or email already exists')

    users.append(new_user)
    with open("users.json", "w") as f:
        json.dump(users, f, indent=4)

    return redirect(url_for("login"))

@app.route("/profile-submit", methods=["POST"])
def profile_submit():
    name = request.form["name"]
    mobile = request.form["mobile"]
    photo = request.files["photo"]

    # Save profile photo
    photo_filename = os.path.join("src/uploads", photo.filename)
    photo.save(photo_filename)

    # Save profile data
    profile_data = {"name": name, "mobile": mobile, "photo": photo_filename}
    with open("profile.json", "w") as f:
        json.dump(profile_data, f, indent=4)

    return redirect(url_for("profile"))

@app.route("/register", methods=["POST"])
def register():
    name = request.form["name"]
    phone = request.form["phone"]
    aadhar = request.form["aadhar"]
    house_no = request.form["house_no"]
    street = request.form["street"]
    landmark = request.form["landmark"]
    district = request.form["district"]
    state = request.form["state"]
    postal_pin = request.form["postal_pin"]
    fingerprint = request.files["fingerprint"].read()
    face = request.files["face"].read()

    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor()

    try:
        cursor.execute("""
            INSERT INTO voters (name, phone, aadhar, house_no, street, landmark, district, state, postal_pin, fingerprint, face)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (name, phone, aadhar, house_no, street, landmark, district, state, postal_pin, fingerprint, face))
        conn.commit()
        flash('Registration successful!', 'success')
    except mysql.connector.Error as err:
        flash(f'Error: {err}', 'danger')
    finally:
        cursor.close()
        conn.close()

    return redirect(url_for("registration"))

@app.route('/scan-fingerprint', methods=['POST'])
def scan_fingerprint():
    # Use the fingerprint scanner SDK to capture the fingerprint
    # This is a placeholder for the actual fingerprint scanning logic
    fingerprint_data = capture_fingerprint()

    # Verify the fingerprint with the database
    is_verified = verify_fingerprint(fingerprint_data)

    if is_verified:
        return jsonify(success=True, message='Fingerprint verified successfully')
    else:
        return jsonify(success=False, message='Fingerprint verification failed')

def capture_fingerprint():
    # Placeholder function to capture fingerprint using the scanner SDK
    # Replace this with actual SDK integration code
    return 'sampleFingerprintData'

def verify_fingerprint(fingerprint_data):
    # Placeholder function to verify fingerprint with the database
    # Replace this with actual verification logic
    return True

@app.route('/check-login-status')
def check_login_status():
    is_logged_in = 'logged_in' in session
    return jsonify(isLoggedIn=is_logged_in)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('home'))

def main():
    app.run(port=int(os.environ.get('PORT', 5000)))

if __name__ == "__main__":
    main()
