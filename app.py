from flask import Flask, render_template, request, redirect, flash, session
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
    if request.method == 'POST':
        form = request.form
        d1 = form['booking_loan_date']
        d2 = form['booking_return_date']
        
        cur = mysql.connection.cursor()
        query = "SELECT m.*, COUNT(c.car_ID) AS available_model_quantity FROM model m LEFT JOIN car c ON m.model_ID = c.model_ID AND c.car_return_date < %s GROUP BY m.model_ID, m.model_name HAVING available_model_quantity > 0;"
        
        cur.execute(query, (d1,))
        resultValue = cur.rowcount
        print(resultValue)
        
        if resultValue > 0:
            models = cur.fetchall()
            cur.close()
            return render_template('model.html', models=models, form=form)
        
        cur.close()
        return render_template('model.html', form=form)
    
    return render_template('index.html')
    

@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        userDetails = request.form
        
        if userDetails['customer_password'] != userDetails['customer_confirm_password']:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        cur = mysql.connection.cursor()
        p1 = userDetails['customer_firstname']
        p2 = userDetails['customer_lastname']
        p3 = userDetails['customer_dob']
        p4 = userDetails['customer_password']
        p5 = userDetails['customer_email']
        p6 = userDetails['customer_phone_number']

        

        hashed_pw = generate_password_hash(p4)    
        queryStatement = (
            f"INSERT INTO "
            f"customer(customer_firstname,customer_lastname, customer_dob, customer_password, customer_email, customer_phone_number) "
            f"VALUES('{p1}', '{p2}', '{p3}','{hashed_pw}','{p5}','{p6}')"
        )
        print(queryStatement)
    
        cur.execute(queryStatement)
        mysql.connection.commit()
        cur.close()
        flash("Form Submitted Successfully.", "success")
        return redirect('/login/')    
    return render_template('register.html')



@app.route('/login/', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    elif request.method == 'POST':
        loginForm = request.form
        user = loginForm['customer_email']
        if ("@admin.co.th" in user):
            cur = mysql.connection.cursor()
            queryStatement = f"SELECT * FROM admin WHERE admin_email = '{user}'"
            numRow = cur.execute(queryStatement)
            if numRow > 0:
                user =  cur.fetchone()
                if check_password_hash(user['admin_password'], loginForm['customer_password']):

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
            numRow = cur.execute(queryStatement)
            if numRow > 0:
                user =  cur.fetchone()
                if check_password_hash(user['customer_password'], loginForm['customer_password']):

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
    return render_template('register.html')


@app.route('/model/', methods = ['GET', 'POST'])
def model():
    booking_loan_date = None
    booking_return_date = None
    if request.method == 'POST':
        booking_loan_date = request.form.get('booking_loan_date')
        booking_return_date = request.form.get('booking_return_date')
        cur = mysql.connection.cursor()
        query = "SELECT m.*, COUNT(c.car_ID) AS available_model_quantity FROM model m LEFT JOIN car c ON m.model_ID = c.model_ID AND c.car_return_date < '{booking_loan_date}'GROUP BY m.model_ID, m.model_name HAVING available_model_quantity > 0;"
        resultValue = cur.execute(query)
        print(resultValue)
        if resultValue > 0:
            models = cur.fetchall()
            cur.close()
            return render_template('model.html', models=models)
        cur.close()
        return render_template('model.html')
    else:
        return render_template('model.html')

@app.route('/mybookings/', methods=['GET', 'POST'])
def mybookings():
    try:
        user = session['login']
    except:
        flash('Please sign in first', 'danger')
        return redirect('/login')
    
    if session['login'] != True:
        return redirect('/register')
    else:
        cur = mysql.connection.cursor()
        query = f"SELECT * FROM booking WHERE customer_ID = '{session['id']}'"
        cur.execute(query)
        resultValue = cur.rowcount
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
    return render_template('payment.html')

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

@app.route('/logout')
def logout():
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)