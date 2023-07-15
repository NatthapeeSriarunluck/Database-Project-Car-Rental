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

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/signin/', methods=['GET', 'POST'])
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
                    session['gender'] = user['admin_gender']
                    session['Phone_number'] = user['admin_phonenumber']
                    session['address'] = user['admin_address']
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
                    session['gender'] = user['customer_gender']
                    session['Phone_number'] = user['customer_phone_number']
                    session['address'] = user['customer_address']
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
    

if __name__ == '__main__':
    app.run(debug=True)