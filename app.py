import sqlite3
from datetime import datetime

from flask import Flask, render_template, request, redirect, url_for, flash, session
from passlib.hash import pbkdf2_sha256 as sha256

from db import get_db, init_db_command
from helpers.loginAuth import login_required

app = Flask(__name__)
app.config['DATABASE'] = 'finance_tracker.db'
app.cli.add_command(init_db_command)
app.secret_key = "TEST_SECRET"


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        print("Email is email")
        password = request.form['password']
        name = request.form['name']
        nameL = name.split()
        firstname = nameL[0]
        lastname = nameL.pop()
        db = get_db()
        error = None
        cursor = db.cursor()
        cursor.execute('SELECT * FROM User WHERE Email = ?', (email,))
        emailCheck = cursor.fetchone()
        cursor.execute('SELECT * FROM User WHERE FirstName = ? AND LastName = ? AND Email = ?',
                       (firstname, lastname, email))
        nameEmailCheck = cursor.fetchone()
        if emailCheck:
            error = 'Email already registered.'
            print(error)
        elif nameEmailCheck:
            error = 'A user with the same first name, last name, and email already exists.'
            print(error)
        hashed_password = sha256.hash(password)
        if error is None:
            try:
                cursor.execute('INSERT INTO User (Email, Password, FirstName, LastName) VALUES (?, ?, ?, ?)',
                               (email, hashed_password, firstname, lastname))
                db.commit()
            except sqlite3.IntegrityError as e:
                error = 'An unexpected error occurred. Please try again.'
        if error:
            flash('There was an error registering you. Try again', 'danger')
        return redirect(url_for('dashboard'))
    return render_template('register.html')


@app.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        db = get_db()
        cursor = db.cursor()
        cursor.execute('SELECT * FROM User WHERE Email = ?', (email,))
        user = cursor.fetchone()
        if user is None:
            flash('No user found with that email address.', 'danger')
            return redirect(url_for('login'))
        elif not sha256.verify(password, user['Password']):
            flash('Incorrect password.', 'danger')
            return redirect(url_for('login'))
        else:
            session['loggedin'] = True
            session['userID'] = user['UserID']
            session['firstName'] = user['FirstName']
            session['lastName'] = user['LastName']
            session['email'] = user['Email']
            flash('You were successfully logged in.', 'success')
            return redirect(url_for('dashboard'))
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/home')
def home():
    return redirect(url_for('login'))


@app.route('/dashboard')
@login_required
def dashboard():
    user = {
        'userId': session['userID'],
        'firstName': session['firstName'],
        'email': session['email'],
        'lastName': session['lastName']
    }

    currentdatetime = datetime.now()
    currentMonth = currentdatetime.strftime('%B')
    db = get_db()
    cursor = db.cursor()
    cursor.execute('SELECT SUM(BudgetAmount) AS TotalBudget FROM Budget WHERE Month = ? AND UserID = ?', (currentMonth, user['userId']))
    budget = cursor.fetchone()
    total_budget = budget['TotalBudget']
    print(total_budget)
    return render_template('Authenticated/dashboard.html', user = user)

@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    cursor = db.cursor()

    if request.method == 'POST':
        if 'delete_profile' in request.form:
            user_id = session['userID']
            cursor.execute('DELETE FROM User WHERE UserID = ?', (user_id,))
            db.commit()
            session.clear()
            flash('Your account has been successfully deleted.', 'success')
            return redirect(url_for('register'))

        elif 'save_changes' in request.form:
            firstname = request.form.get('firstName')
            lastname = request.form.get('lastName')
            email = request.form.get('email')
            cursor.execute('UPDATE User SET FirstName = ?, LastName = ?, Email = ? WHERE UserID = ?',
                           (firstname, lastname, email, session['userID']))
            db.commit()
            session['firstName'] = firstname
            session['lastName'] = lastname
            session['email'] = email
            flash('Profile successfully updated.', 'success')
    user = {
        'userId': session['userID'],
        'firstName': session['firstName'],
        'lastName': session['lastName'],
        'email': session['email']
    }
    return render_template('Authenticated/profile.html', user=user)


if __name__ == '__main__':
    app.run()
