import os
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_mysqldb import MySQL
from flask_mail import Mail, Message
from itsdangerous import URLSafeTimedSerializer, SignatureExpired, BadSignature
import MySQLdb.cursors
from datetime import datetime, timedelta

# --------------------------
# Flask App Initialization
# --------------------------
app = Flask(__name__)
app.secret_key = 'superbikes_secret_key'

# --------------------------
# MySQL Configuration
# --------------------------
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'Test@123'  
app.config['MYSQL_DB'] = 'superbikes_db'

mysql = MySQL(app)

UPLOAD_FOLDER = 'static/uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure folder exist

# --------------------------
# Flask-Mail Configuration
# --------------------------
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'bikesbay@gmail.com'
app.config['MAIL_PASSWORD'] = 'enwlipwlzwoeirqo'
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_DEFAULT_SENDER'] = ('Bikes Bay', 'your_email@gmail.com')


mail = Mail(app)

# --------------------------
# Token Serializer
# --------------------------
s = URLSafeTimedSerializer(app.secret_key)

# --------------------------
# Forgot Password Route
# --------------------------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']

        cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
        cur.execute("SELECT * FROM users WHERE email=%s", (email,))
        user = cur.fetchone()
        cur.close()

        if user:
            token = s.dumps(email, salt='password-reset-salt')
            reset_link = url_for('reset_password', token=token, _external=True)

            # Prepare email content
            subject = "🔐 Reset Your Password"
            sender_email = "your_email@gmail.com"

            # Plain text version
            text_body = f"""\
You requested a password reset.

Please click the link below to reset your password:

{reset_link}

If you did not request this, you can ignore this email.

Thank you,
-Team Bikes Bay
"""

            msg = Message(subject,
                          sender=sender_email,
                          recipients=[email])
            msg.body = text_body
            # msg.html = html_body  # If using HTML email templates

            mail.send(msg)

            flash("Password reset link sent to your email!", "success")
        else:
            flash("Email not found!", "danger")
        return redirect(url_for('show_login'))

    return render_template('forgot_password.html')



# --------------------------
# Reset Password Route
# --------------------------

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    try:
        email = s.loads(token, salt='password-reset-salt', max_age=3600)  # link valid for 1 hour
    except SignatureExpired:
        return "The reset link has expired."
    except BadSignature:
        return "Invalid reset link."

    if request.method == 'POST':
        new_password = request.form['password']
        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET password=%s WHERE email=%s", (new_password, email))
        mysql.connection.commit()
        cur.close()
        flash("Password updated successfully!", "success")
        return redirect(url_for('show_login'))

    return render_template('reset_password.html', token=token)


# --------------------------
# Authentication Routes
# --------------------------

@app.route('/login', methods=['GET'])
def show_login():
    return render_template('login.html')


@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor(MySQLdb.cursors.DictCursor)
    cur.execute("SELECT * FROM users WHERE email=%s AND password=%s", (email, password))
    user = cur.fetchone()
    cur.close()

    if user:
        session['user_id'] = user['id']
        session['username'] = user['name']
        session['email'] = user['email']
        return redirect(url_for('dashboard'))
    else:
        flash("Invalid credentials. Please try again.", "danger")
        return redirect(url_for('show_login'))


@app.route('/signup', methods=['POST'])
def signup():
    name = request.form['name']
    email = request.form['email']
    password = request.form['password']

    cur = mysql.connection.cursor()

    # 🔍 Check if email already exists
    cur.execute("SELECT * FROM users WHERE email = %s", (email,))
    existing_user = cur.fetchone()

    if existing_user:
        cur.close()
        # Redirect back to signup page with a flag
        return redirect(url_for('show_login', email_exists='true'))

    # 🆕 Insert new user
    cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)", (name, email, password))
    mysql.connection.commit()
    cur.close()

    # 📧 Send confirmation email
    msg = Message(
        subject="Welcome to Bikes Bay!",
        sender=("Bikes Bay", "your_email@gmail.com"),
        recipients=[email],
        body=f"Hello {name},\n\nWelcome to Bikes Bay! Your account has been created successfully.\n\nYou can now log in and start exploring premium bikes.\n\nThank you for joining us!\n\n- Team Bikes Bay"
    )
    mail.send(msg)

    flash("Account created successfully! Please check your email and login.", "success")
    return redirect(url_for('show_login'))




@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('show_login'))

@app.route('/contactUs', methods=['GET', 'POST'])
def contactUs():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['mail']
        mob = request.form['mob']
        query = request.form['query']

        # Optional: store in DB or send email using Flask-Mail
        # Example (store in DB)
        cur = mysql.connection.cursor()
        cur.execute(
            "INSERT INTO contact_messages (name, email, phone, query ) VALUES (%s, %s, %s, %s)",
            (name, email, mob, query)
        )
        mysql.connection.commit()
        cur.close()

        flash("Your message has been sent successfully!", "success")
        return redirect(url_for('home'))

    # For GET requests
    return render_template('contactUs.html')

# Appointment form page
@app.route('/book-appointment', methods=['GET', 'POST'])
def book_appointment_page():
    if request.method == 'POST':
        # Get form data
        name = request.form['name']
        phone = request.form['phone']
        vehicle = request.form['vehicle']
        date_str = request.form['date']  # 'YYYY-MM-DD'
        time = request.form['time']
        area = request.form['area']
        city = request.form['city']
        state = request.form['state']
        post_code = request.form['post_code']
        driving_license = request.form['driving_license']

        # Backend date validation
        appointment_date = datetime.strptime(date_str, '%Y-%m-%d').date()
        min_date = (datetime.today() + timedelta(days=3)).date()

        if appointment_date < min_date:
            flash(f'You can only book appointments from {min_date} onwards.', 'danger')
            return redirect(url_for('book_appointment_page'))

        try:
            # Insert data into MySQL
            cursor = mysql.connection.cursor()
            query = """
                INSERT INTO appointments 
                (name, phone, vehicle, date, time, area, city, state, post_code, driving_license)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (name, phone, vehicle, date_str, time, area, city, state, post_code, driving_license))
            mysql.connection.commit()
            cursor.close()
            
            flash('Appointment booked successfully!', 'success')
            return redirect(url_for('home'))
        
        except Exception as e:
            print(e)
            flash('Error! Could not book appointment.', 'danger')
            return redirect(url_for('book_appointment_page'))

    # Render template
    return render_template('BookAppointment.html')


@app.route('/sell-bike', methods=['GET', 'POST'])
def sell_bike_page():
    if request.method == 'POST':
        try:
            name = request.form['name']
            email = request.form['email']
            phone = request.form['phone']
            address = request.form['address']
            chassis = request.form['chassis']
            plate = request.form['plate']
            years_used = request.form['years_used']
            owners = request.form['owners']
            rc_image = request.files['rc_image']
            bike_image = request.files['bike_image']

            # Save uploaded images
            rc_path = os.path.join(app.config['UPLOAD_FOLDER'], rc_image.filename)
            bike_path = os.path.join(app.config['UPLOAD_FOLDER'], bike_image.filename)
            rc_image.save(rc_path)
            bike_image.save(bike_path)

            # Insert details into DB
            cursor = mysql.connection.cursor()
            sql = """
                INSERT INTO resale_bikes 
                (name, email, phone, address, chassis, plate, rc_image, bike_image, years_used, owners)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            val = (name, email, phone, address, chassis, plate, rc_path, bike_path, years_used, owners)
            cursor.execute(sql, val)
            mysql.connection.commit()
            cursor.close()

            flash("Your bike details have been submitted successfully!", "success")
            return redirect(url_for('sell_bike_page'))

        except Exception as e:
            print("Error submitting bike:", e)
            flash("Something went wrong. Please try again.", "danger")
            return redirect(url_for('sell_bike_page'))

    return render_template('resale.html')




# --------------------------
# Dashboard
# --------------------------

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('show_login'))

    cur = mysql.connection.cursor()
    cur.execute("SELECT id, bike_name, bike_image, bike_link FROM wishlist WHERE user_email=%s", (session['email'],))
    wishlist_items = cur.fetchall()
    cur.close()

    wishlist = [{'id': item[0], 'bike_name': item[1], 'bike_image': item[2], 'bike_link': item[3]} for item in wishlist_items]
    return render_template('dashboard.html', username=session['username'], wishlist=wishlist)


# --------------------------
# Wishlist AJAX Routes
# --------------------------

@app.route('/add_to_wishlist', methods=['POST'])
def add_to_wishlist():
    if 'email' not in session:
        return jsonify({'status': 'error', 'message': 'Please login first'})

    data = request.get_json()
    bike_name = data.get('bike_name')
    bike_image = data.get('bike_image')
    bike_link = data.get('bike_link')

    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM wishlist WHERE user_email=%s AND bike_name=%s", (session['email'], bike_name))
    exists = cur.fetchone()

    if exists:
        cur.close()
        return jsonify({'status': 'exists', 'message': 'Already in wishlist'})

    cur.execute("INSERT INTO wishlist (user_email, bike_name, bike_image, bike_link) VALUES (%s, %s, %s, %s)",
                (session['email'], bike_name, bike_image, bike_link))
    mysql.connection.commit()
    cur.close()

    return jsonify({'status': 'success', 'message': 'Added to wishlist'})


@app.route('/remove_from_wishlist', methods=['POST'])
def remove_from_wishlist():
    if 'email' not in session:
        return jsonify({"status": "error", "message": "User not logged in"}), 401

    data = request.get_json()
    bike_id = data.get("bike_id")

    if not bike_id:
        return jsonify({"status": "error", "message": "No bike ID provided"}), 400

    try:
        cur = mysql.connection.cursor()
        cur.execute("DELETE FROM wishlist WHERE id=%s AND user_email=%s", (bike_id, session['email']))
        mysql.connection.commit()
        cur.close()
        return jsonify({"status": "success", "message": "Bike removed successfully"})
    except Exception as e:
        print("Error removing bike:", e)
        return jsonify({"status": "error", "message": "Database error"}), 500


# --------------------------
# Static Pages
# --------------------------

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/about')
def about():
    return render_template("about.html")


@app.route('/sportsbike')
def sportsbike():
    return render_template('SportsBike.html')


@app.route('/Naked')
def nacked():
    return render_template('Naked.html')


@app.route('/trourer')
def trourer():
    return render_template('trourer.html')


# --------------------------
# Bike Models Pages
# --------------------------

@app.route('/ApacheRR310')
def apache_rr310():
    return render_template('Apache RR310.html')


@app.route('/aprillia')
def aprillia():
    return render_template('aprillia.html')


@app.route('/Benelli')
def benelli():
    return render_template('Benelli.html')


@app.route('/BMWS1000RR')
def bmws1000rr():
    return render_template('BMWS1000RR.html')


@app.route('/Ducati916')
def ducati916():
    return render_template('Ducati916.html')


@app.route('/Hayabusa')
def hayabusa():
    return render_template('Hayabusa.html')


@app.route('/Kawasaki')
def kawasaki():
    return render_template('Kawasaki.html')


@app.route('/Ktm')
def ktm():
    return render_template('Ktm.html')


@app.route('/KTM2')
def ktm2():
    return render_template('KTM2.html')


@app.route('/re')
def re():
    return render_template('re.html')


@app.route('/Triumph')
def triumph():
    return render_template('Triumph.html')


@app.route('/YamahaMT07')
def yamaha_mt07():
    return render_template('YamahaMT07.html')


# --------------------------
# Run Flask App
# --------------------------

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)

