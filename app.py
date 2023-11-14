from flask import Flask, render_template, request, redirect, url_for, flash, session
import sqlite3

from passlib.hash import pbkdf2_sha256 as sha256

from db import get_db, init_db_command

app = Flask(__name__)
app.config['DATABASE'] = 'finance_tracker.db'
app.cli.add_command(init_db_command)
app.secret_key = "TEST_SECRET"


@app.route('/')
def hello_world():
    return "Hello"


@app.route('/test')
def hello_world1():
    return "Failure!"


@app.route('/register', methods = ['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        firstname = request.form['firstname']
        lastname = request.form['lastname']

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
            return redirect(url_for('hello_world1'))
        return redirect('https://www.google.com')
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
            flash('No user found with that email address.')
            return redirect(url_for('login'))
        elif not sha256.verify(password, user['Password']):
            flash('Incorrect password.')
            return redirect(url_for('login'))
        else:
            session['loggedin'] = True
            session['userID'] = user['UserID']
            session['firstName'] = user['FirstName']
            flash('You were successfully logged in.')
            return redirect(url_for('home'))

    return render_template('login.html')


@app.route('/logout')
def logout():
    session.pop('id', None)
    session.pop('loggedin', None)
    flash('You have been logged out.')
    return redirect(url_for('login'))


@app.route('/home')
def home():
    if 'loggedin' in session:
        return render_template('home.html', user_id = session['userID'], first_name = session['firstName'])
    return redirect(url_for('login'))


if __name__ == '__main__':
    app.run()
