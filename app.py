from flask import Flask, render_template, request, redirect, flash, session, url_for
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
import yaml

app = Flask(__name__)
app.config['SECRET_KEY'] = "Never push this line to github public repo"

cred = yaml.load(open('cred.yaml'), Loader=yaml.Loader)
app.config['MYSQL_HOST'] = cred['mysql_host']
app.config['MYSQL_USER'] = cred['mysql_user']
app.config['MYSQL_PASSWORD'] = cred['mysql_password']
app.config['MYSQL_DB'] = cred['mysql_db']
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/reserve', methods=['GET', 'POST'])
def reserve():
    if request.method == 'GET':
        if 'login' in session and session['login'] == True:
            cur = mysql.connection.cursor()
            query = f"Select CURDATE() as date;"
            cur.execute(query)
            date = cur.fetchone()
            cur.close()
            return render_template('reserve.html', date=date)
        else:
            flash('Please log in first.')
            return redirect(url_for('login'))

    elif request.method == 'POST':
        session['d1'] = request.form['booking_loan_date']
        session['d2'] = request.form['booking_return_date']
        return redirect(url_for('model'))

    return render_template('reserve.html')


@app.route('/model/')
def model():
    if 'login' not in session or session['login'] != True:
        flash('Please log in first.')
        return redirect(url_for('login'))
    else:
        cur = mysql.connection.cursor()
        query = f"SELECT m.*, COUNT(c.car_ID) AS available_model_quantity FROM model m LEFT JOIN car c ON m.model_ID = c.model_ID AND c.car_return_date < '{session['d1']}'GROUP BY m.model_ID, m.model_name HAVING available_model_quantity > 0;"
        cur.execute(query)
        models = cur.fetchall()
        cur.close()
        return render_template('model.html', models=models)


# where add-ons are selected
@app.route('/booking/<int:model_id>', methods=['GET', 'POST']) # model id should be passed and made session id here 
def booking(model_id):
    session["model_id"] = model_id
    cur = mysql.connection.cursor()
    query = "SELECT * FROM addons"
    cur.execute(query)
    addons = cur.fetchall()
    cur.close()

    return render_template('booking.html', addons=addons)

#make an entry for booking table
@app.route('/register_booking', methods=['POST'])
def register_booking():
    selected_addons = request.form.getlist('selected_addons[]')
    addons_price = 0

    #get total add on price
    for addon_id in selected_addons:
        cursor = mysql.connection.cursor()
        query = f"SELECT addons_price FROM addons WHERE addons_ID = {addon_id}"
        cursor.execute(query)
        price = cursor.fetchone()
        addons_price += price['addons_price']
        cursor.close()

    # get list of all add ons strings
    addons_list = ''
    for addon_id in selected_addons:
        cursor = mysql.connection.cursor()
        query = f"SELECT addons_name FROM addons WHERE addons_ID = {addon_id}"
        cursor.execute(query)
        result = cursor.fetchone()
        addons_list += ',' + result['addons_name']
        cursor.close()
    modified_string = addons_list[1:]
    # get number of days   
    cursor = mysql.connection.cursor()
    query = f"SELECT DATEDIFF('{session.get('d2')}', '{session.get('d1')}')"
    cursor.execute(query)
    result = cursor.fetchone()
    num_days = result[f"DATEDIFF('{session.get('d2')}', '{session.get('d1')}')"]
    cursor.close()
    
    # get the days' price of the car
    cursor = mysql.connection.cursor()
    query = f"SELECT model_price_per_day FROM model WHERE model_id = {session.get('model_id')}"
    cursor.execute(query)
    price_per_day = cursor.fetchone()
    cursor.close()

    days_price = int(price_per_day['model_price_per_day']) * num_days

    #pick a random car_id from model_id
    cursor = mysql.connection.cursor()
    args = (session.get('d1'), session.get('model_id'))
    cursor.callproc('pick_random_car', args)
    result = cursor.fetchone()
    car_id = result['booked_car_ID']
    cursor.close() 
    #make a new entry in the booking table
    cursor = mysql.connection.cursor()
    cursor.execute(f"INSERT INTO booking (customer_ID, model_ID,car_ID, booking_loan_date, booking_return_date, booking_payment, booking_addons_payment, booking_addons, booking_status) VALUES ({session.get('id')},{session.get('model_id')}, {car_id}, '{session.get('d1')}', '{session.get('d2')}', {days_price}, {addons_price}, '{modified_string}', 'Pending')")
    mysql.connection.commit()
    cursor.close()
    flash("Booking Submitted Successfully.", "success")

    return redirect(url_for('mybookings'))


@app.route('/mybookings/', methods=['GET', 'POST'])
def mybookings():
    try:
        user = session['login']
    except:
        flash('Please sign in first', 'danger')
        return redirect('/login')
    
    if session['login'] != True:
        return redirect('/login')
    else:
        cur = mysql.connection.cursor()
        print("mybookings: session id - " + str(session['id']))
        query = f"SELECT * FROM booking WHERE customer_ID = '{session['id']}'"
        cur.execute(query)
        resultValue = cur.rowcount
        print("mybookings: result value session - " + str(resultValue))
        if resultValue > 0:
            bookings = cur.fetchall()
            cur.close()
            return render_template('mybookings.html', booking=bookings)
        else:
            cur.close()
            return render_template('mybookings.html')

# customer confirm booking
@app.route('/confirm_booking/<int:id>', methods=['GET'])
def confirm_booking(id):
    return render_template('payment.html', bookingID=id)

# customer cancel booking
@app.route('/cancel_booking/<int:id>', methods=['GET'])
def cancel_booking(id):
    cur = mysql.connection.cursor()

    query = f"DELETE FROM booking WHERE booking_ID = {id}"
    cur.execute(query) 
    mysql.connection.commit()
    cur.close()

    flash("You have successfully cancelled your booking.", "success")
    return redirect('/mybookings')

@app.route('/payment/<int:bookingID>', methods=['GET', 'POST']) 
def payment(bookingID):
    cur = mysql.connection.cursor()

    query = f"SELECT * FROM booking WHERE booking_ID = {bookingID}"
    cur.execute(query)
    booking = cur.fetchone()
    cur.close()

    rental_period_price = booking['booking_payment']
    addon_price = booking['booking_addons_payment']
    total_price = rental_period_price + addon_price

    flash("Payment Successful. Thank you for your patronage.")
    return render_template('payment.html', rental_period_price=rental_period_price, addon_price=addon_price, total_price=total_price)

@app.route('/thankyou', methods=['GET'])
def thankyou():
    return render_template('thankyou.html')

@app.route('/logout')
def logout():
    session.clear()
    session['login'] = False
    flash("You have been logged out", 'info')
    return redirect('/')

@app.route('/adminIndex', methods=['GET', 'POST'])
def adminIndex():
    if request.method == 'GET':
        return render_template('adminSide/adminIndex.html')
    elif request.method == 'POST':
        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM booking")
        today = cur.fetchall()
        cur.close()
        return render_template('adminSide/adminIndex.html', today=today)
    else:
        return render_template('adminSide/adminIndex.html')
    
@app.route('/adminBooking', methods=['GET', 'POST'])
def adminBooking():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM booking")
    booking = cur.fetchall()
    cur.close()
    return render_template('adminSide/adBooking.html', booking=booking)
    
@app.route('/adminCustomer', methods = ['GET', 'POST'])
def adminCustomer():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM customer")
    val = cur.fetchall()
    cur.close()
    return render_template('adminSide/adCustomer.html', customer=val)

@app.route('/adminCarModel', methods = ['GET', 'POST'])
def adminCarModel():
    cur = mysql.connection.cursor()
    query = f"SELECT m.*, COUNT(c.car_ID) AS available_model_quantity FROM model m LEFT JOIN car c ON m.model_ID = c.model_ID AND c.car_return_date < '2023-07-21'  GROUP BY m.model_ID, m.model_name HAVING available_model_quantity > 0;"
    cur.execute(query)
    val = cur.fetchall()
    cur.close()
    return render_template('adminSide/adCarModel.html', model=val)

@app.route('/adminCar', methods = ['GET', 'POST'])
def adminCar():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM car")
    val = cur.fetchall()
    cur.close()
    return render_template('adminSide/adCar.html', car=val)
    
@app.route('/adminAdmin', methods = ['GET', 'POST'])
def adminAdmin():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM admin")
    val = cur.fetchall()
    cur.close()
    return render_template('adminSide/adAdmin.html', admin=val)

@app.route('/adminReview', methods = ['GET', 'POST'])
def adminReview():
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM review")
    val = cur.fetchall()
    cur.close()
    return render_template('adminSide/adReview.html', review=val)

@app.route('/adminToday', methods = ['GET', 'POST'])
def adminToday():
    if request.method == 'GET':
        cur = mysql.connection.cursor()
        
        query = f"SELECT * FROM booking WHERE booking_loan_date <= CURDATE() AND booking_return_date >= CURDATE();"
        cur.execute(query)
        today = cur.fetchall()
        
        query = f"SELECT m.*, COUNT(c.car_ID) AS available_model_quantity FROM model m LEFT JOIN car c ON m.model_ID = c.model_ID AND c.car_return_date < CURDATE()  GROUP BY m.model_ID, m.model_name HAVING available_model_quantity > 0;"
        cur.execute(query)
        model = cur.fetchall()
        
        query = f"SELECT * FROM car WHERE car_loan_date <= CURDATE() AND car_return_date >= CURDATE();"
        cur.execute(query)
        car = cur.fetchall()
        
        cur.close()
        return render_template('adminSide/adToday.html', today=today, model=model, car=car)
    elif request.method == 'POST':
        cur = mysql.connection.cursor()
        query = f"SELECT * FROM booking WHERE booking_loan_date <= CURDATE() AND booking_return_date >= CURDATE();"
        cur.execute(query)
        today = cur.fetchall()
        cur.close()
        return render_template('adminSide/adToday.html', today=today)
    else:
        return render_template('adminSide/adToday.html')


@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        form = request.form
        if form['formType'] == '1':
            return log(form)
        elif form['formType'] == '2':
            return regis(form)

def log(form):
    loginForm = form
    user = loginForm['signin_email']
    if ("@admin.co.th" in user):
        cur = mysql.connection.cursor()
        queryStatement = f"SELECT * FROM admin WHERE admin_email = '{user}'"
        numRow = cur.execute(queryStatement)
        if numRow > 0:
            user =  cur.fetchone()
            if check_password_hash(user['admin_password'], loginForm['signin_password']):

            # Record session information
                session['login'] = True
                session['email'] = user['admin_email']
                session['firstName'] = user['admin_firstname']
                session['lastName'] = user['admin_lastname']
                session['dob'] = user['admin_dob']
                session['Phone_number'] = user['admin_phone_number']
                session['id'] = user['admin_ID']
                flash('Welcome ' + session['firstName'], 'success')
            #flash("Log In successful",'success')
                return render_template('adminSide/adminIndex.html')
            else:
                cur.close()
                flash("Password doesn't not match", 'danger')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('login.html')
    else:
        cur = mysql.connection.cursor()
        queryStatement = f"SELECT * FROM customer WHERE customer_email = '{user}'"
        cur.execute(queryStatement)
        numRow = cur.rowcount
        if numRow > 0:
            user =  cur.fetchone()
            if check_password_hash(user['customer_password'], loginForm['signin_password']):

                # Record session information
                session['login'] = True
                session['email'] = user['customer_email']
                session['firstName'] = user['customer_firstname']
                session['lastName'] = user['customer_lastname']
                session['dob'] = user['customer_dob']
                session['Phone_number'] = user['customer_phone_number']
                session['id'] = user['customer_ID']
                flash('Welcome ' + session['firstName'], 'success')
                #flash("Log In successful",'success')
                return redirect('/')
            else:
                cur.close()
                flash("Password doesn't not match", 'danger')
        else:
            cur.close()
            flash('User not found', 'danger')
            return render_template('login.html')
        cur.close()
        return redirect('/')
    

def regis(form):
    userDetails = form    
    if userDetails['signup_password'] != userDetails['signup_confirm_password']:
        flash('Passwords do not match!', 'danger')
        return render_template('login.html')
    
    cur = mysql.connection.cursor()
    p1 = userDetails['signup_firstname']
    p2 = userDetails['signup_lastname']
    p3 = userDetails['signup_dob']
    p4 = userDetails['signup_password']
    p5 = userDetails['signup_email']
    p6 = userDetails['signup_phone_number']

    

    hashed_pw = generate_password_hash(p4)    
    queryStatement = (
        f"INSERT INTO "
        f"customer(customer_firstname,customer_lastname, customer_dob, customer_password, customer_email, customer_phone_number) "
        f"VALUES('{p1}', '{p2}', '{p3}','{hashed_pw}','{p5}','{p6}')"
    )
    print("regis: query statement")
    print(queryStatement)

    cur.execute(queryStatement)
    mysql.connection.commit()
    cur.close()
    flash("Form Submitted Successfully.", "success")
    return redirect('/')

@app.route('/test', methods=['GET', 'POST'])
def test():
    return render_template('test.html')

@app.route('/test2', methods=['GET', 'POST'])
def test2():
    return render_template('test2.html')

if __name__ == '__main__':
    app.run(
        debug=True
    )
