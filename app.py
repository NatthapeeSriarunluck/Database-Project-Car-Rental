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


@app.route('/about/')
def about():
    return render_template('about.html')

@app.route('/blogs/<int:id>/')
def blogs(id):
    return render_template('blogs.html', blog_id = id)
@app.route('/register/', methods=['GET', 'POST'])
def register():
    if request.method == 'GET':
        return render_template('register.html')
    elif request.method == 'POST':
        userDetails = request.form
        
        if userDetails['customer_password'] != userDetails['customer_confirm_password']:
            flash('Passwords do not match!', 'danger')
            return render_template('register.html')
        
        p1 = userDetails['customer_firstname']
        p2 = userDetails['customer_lastname']
        p3 = userDetails['customer_dob']
        p4 = userDetails['customer_password']
        p6 = userDetails['customer_email']
        p7 = userDetails['customer_phone_number']
        p9 = userDetails['customer_identification_number']
        p10 = userDetails['customer_passport']
        

        hashed_pw = generate_password_hash(p4)    
        queryStatement = (
            f"INSERT INTO "
            f"customer(customer_firstname,customer_lastname, customer_dob, customer_password, customer_email, customer_phone_number,customer_identification_number, customer_passport, customer_payment_type, customer_payment_card_number, customer_payment_card_cvc, customer_payment_card_expiry_date) "
            f"VALUES('{p1}', '{p2}', '{p3}','{hashed_pw}','{p6}','{p7},'{p9}','{p10}')"
        )
        print(queryStatement)
        cur = mysql.connection.cursor()
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

@app.route('/write-blog/', methods=['GET', 'POST'])
def write_blog():
    return render_template('write-blog.html')

@app.route('/my-blogs/')
def my_blogs():
    return render_template('my-blogs.html')

@app.route('/edit-blog/<int:id>/', methods=['GET', 'POST'])
def edit_blog(id):
    return render_template('edit-blog.html')

@app.route('/delete-blog/<int:id>/', methods=['POST'])
def delete_blog(id):
    return 'success'

@app.route('/logout')
def logout():
    return render_template('logout.html')

if __name__ == '__main__':
    app.run(debug=True)


if __name__ == '__main__':
    app.run(debug=True)