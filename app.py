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
        password = request.form['password']
        name = request.form['name']
        name_parts = name.split()
        firstname = name_parts[0]
        lastname = name_parts[-1]
        db = get_db()
        error = None
        cursor = db.cursor()
        cursor.execute('SELECT * FROM User WHERE Email = ?', (email,))
        emailCheck = cursor.fetchone()
        cursor.execute('SELECT * FROM User WHERE FirstName = ? AND LastName = ? AND Email = ?',
                       (firstname, lastname, email))
        name_email_check = cursor.fetchone()
        if emailCheck:
            error = 'Email already registered.'
            flash(error, 'danger')
        elif name_email_check:
            error = 'A user with the same first name, last name, and email already exists.'
            flash(error, 'danger')
        hashedPwd = sha256.hash(password)
        if error is None:
            try:
                cursor.execute('INSERT INTO User (Email, Password, FirstName, LastName) VALUES (?, ?, ?, ?)',
                               (email, hashedPwd, firstname, lastname))
                db.commit()
                # Set session variables after successful registration and login
                cursor.execute('SELECT * FROM User WHERE Email = ?', (email,))
                user = cursor.fetchone()
                session['loggedin'] = True
                session['userID'] = user['UserID']
                session['firstName'] = user['FirstName']
                session['lastName'] = user['LastName']
                session['email'] = user['Email']
                flash('Registration successful. You are now logged in.', 'success')
                return redirect(url_for('dashboard'))
            except sqlite3.IntegrityError as e:
                error = 'An unexpected error occurred. Please try again.'
        if error:
            flash('There was an error registering you. Try again', 'danger')
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
    cursor.execute('SELECT SUM(BudgetAmount) AS TotalBudget FROM Budget WHERE Month = ? AND UserID = ?',
                   (currentMonth, user['userId']))
    budget = cursor.fetchone()
    totalBudget = budget['TotalBudget']
    return render_template('Authenticated/dashboard.html', user = user)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/profile', methods = ['GET', 'POST'])
@login_required
def profile():
    db = get_db()
    cursor = db.cursor()
    if request.method == 'POST':
        if 'delete_profile' in request.form:
            userID = session['userID']
            deleteQueries = [
                "DELETE FROM ExpensePaymentMethod WHERE ExpenseID IN (SELECT ExpenseID FROM ExpenseItem WHERE UserID = ?)",
                "DELETE FROM ExpenseItem WHERE UserID = ?",
                "DELETE FROM Budget WHERE UserID = ?",
                "DELETE FROM MonthlySummary WHERE UserID = ?",
                "DELETE FROM PaymentMethod WHERE UserID = ?",
                "DELETE FROM User WHERE UserID = ?"
            ]
            for query in deleteQueries:
                cursor.execute(query, (userID,))
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
    return render_template('Authenticated/profile.html', user = user)


@app.route('/expenseform', methods = ['GET', 'POST'])
@login_required
def expenseForm():
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT CategoryID, CategoryName FROM Category')
    categories = cursor.fetchall()
    cursor.execute('SELECT PaymentMethodID, PaymentMethodName FROM PaymentMethod WHERE UserID = ?',
                   (session['userID'],))
    paymentMethods = cursor.fetchall()
    if request.method == 'POST':
        print(request.form)
        item = request.form['item']
        amount = float(request.form['amount'])
        date = request.form['date']
        selectedCategory = request.form['category']
        newCategoryName = request.form.get('new-category', None)
        selectedPaymentMethod = request.form['payment-method-select']
        newPaymentMethodName = request.form.get('new-payment-method', None)
        categoryId = None
        if selectedCategory == 'new-category' and newCategoryName:
            cursor.execute('INSERT INTO Category (CategoryName) VALUES (?)', (newCategoryName,))
            db.commit()
            categoryId = cursor.lastrowid
        elif selectedCategory:
            categoryId = int(selectedCategory)
        paymentMethodId = None
        if selectedPaymentMethod == 'new-method' and newPaymentMethodName:
            cursor.execute('INSERT INTO PaymentMethod (PaymentMethodName, UserID) VALUES (?, ?)',
                           (newPaymentMethodName, session['userID']))
            db.commit()
            paymentMethodId = cursor.lastrowid
        elif selectedPaymentMethod:
            paymentMethodId = int(selectedPaymentMethod)
        if categoryId is not None and paymentMethodId is not None:
            userId = session['userID']
            cursor.execute('INSERT INTO ExpenseItem (UserID, Item, Amount, Date, CategoryID) VALUES (?, ?, ?, ?, ?)',
                           (userId, item, amount, date, categoryId))
            db.commit()
            expenseId = cursor.lastrowid
            cursor.execute('INSERT INTO ExpensePaymentMethod (ExpenseID, PaymentMethodID) VALUES (?, ?)',
                           (expenseId, paymentMethodId))
            db.commit()
            flash('Expense added successfully.', 'success')
        else:
            flash('Please select valid category and payment method.', 'danger')

        return redirect(url_for('dashboard'))

    return render_template('Authenticated/expenseform.html', categories = categories, payment_methods = paymentMethods)


@app.route('/editexpense/<int:expenseID>', methods = ['GET', 'POST'])
@login_required
def editExpense(expenseID):
    db = get_db()
    cursor = db.cursor()
    if request.method == 'GET':
        cursor.execute('SELECT * FROM ExpenseItem WHERE UserID = ?', (session['userID'],))
        expense = cursor.fetchone()
        if expense is None:
            return redirect(url_for('expenseForm'))
        cursor.execute('SELECT CategoryID, CategoryName FROM Category')
        categories = cursor.fetchall()
        cursor.execute('SELECT PaymentMethodID, PaymentMethodName FROM PaymentMethod WHERE UserID = ?',
                       (session['userID'],))
        paymentMethods = cursor.fetchall()
        return render_template('Authenticated/editexpenses.html', expense = expense, categories = categories,
                               payment_methods = paymentMethods)
    if request.method == 'POST':
        item = request.form.get('item')
        amount = request.form.get('amount')
        date = request.form.get('date')
        categoryId = request.form.get('category')
        newCategory = request.form.get('new-category')
        paymentMethodId = request.form.get('payment-method-select')
        newPaymentMethod = request.form.get('new-payment-method')
        if newCategory:
            cursor.execute('INSERT INTO Category (CategoryName) VALUES (?)', (newCategory,))
            db.commit()
            categoryId = cursor.lastrowid
        if newPaymentMethod:
            cursor.execute('INSERT INTO PaymentMethod (PaymentMethodName, UserID) VALUES (?, ?)',
                           (newPaymentMethod, session['userID']))
            db.commit()
            paymentMethodId = cursor.lastrowid
        cursor.execute('''
            UPDATE ExpenseItem
            SET Item = ?, Amount = ?, Date = ?, CategoryID = ?
            WHERE ExpenseID = ? AND UserID = ?
        ''', (item, amount, date, categoryId, expenseID, session['userID']))
        db.commit()
        cursor.execute('''
            UPDATE ExpensePaymentMethod
            SET PaymentMethodID = ?
            WHERE ExpenseID = ?
        ''', (paymentMethodId, expenseID))
        db.commit()
        return redirect(url_for('dashboard'))


@app.route('/managepayments', methods = ['GET', 'POST'])
@login_required
def managePayments():
    db = get_db()
    cursor = db.cursor()
    id = session['userID']
    paymentMethodInUse = False
    if 'delete' in request.form:
        paymentMethodIdToDelete = request.form['paymentMethodId']
        cursor.execute(
            '''SELECT ExpenseID, Item, Amount, Date FROM ExpenseItem 
               WHERE ExpenseID IN (SELECT ExpenseID FROM ExpensePaymentMethod WHERE PaymentMethodID = ?)
               AND UserID = ?''',
            (paymentMethodIdToDelete, id))
        expenseItems = cursor.fetchall()
        if expenseItems:
            paymentMethodInUse = True
            replacementMethod = request.form.get('replacementMethod', None)
            newPaymentMethodName = request.form.get('newPaymentMethodName', None)
            if replacementMethod == 'new' and newPaymentMethodName:
                cursor.execute('INSERT INTO PaymentMethod (PaymentMethodName, UserID) VALUES (?, ?)',
                               (newPaymentMethodName, id))
                db.commit()
                replacementMethod = cursor.lastrowid
            if replacementMethod and replacementMethod != 'new':
                cursor.execute(
                    'UPDATE ExpensePaymentMethod SET PaymentMethodID = ? WHERE PaymentMethodID = ? AND ExpenseID IN ('
                    'SELECT ExpenseID FROM ExpenseItem WHERE UserID = ?)',
                    (replacementMethod, paymentMethodIdToDelete, id))
                db.commit()
        if not paymentMethodInUse:
            cursor.execute('DELETE FROM PaymentMethod WHERE PaymentMethodID = ? AND UserID = ?',
                           (paymentMethodIdToDelete, id))
            db.commit()
            flash('Payment method deleted successfully.', 'success')
    elif "add" in request.form:
        paymentMethodName = request.form['paymentMethodName']
        cursor.execute('SELECT * FROM PaymentMethod WHERE PaymentMethodName = ? AND UserID = ?',
                       (paymentMethodName, id))
        if cursor.fetchone():
            flash("Payment method already exists", 'danger')
        else:
            cursor.execute('INSERT INTO PaymentMethod (UserID, PaymentMethodName) VALUES (?, ?)',
                           (id, paymentMethodName))
            db.commit()
            flash('Payment method added successfully.', 'success')
    cursor.execute('SELECT * FROM PaymentMethod WHERE UserID = ?', (id,))
    paymentMethods = cursor.fetchall()
    return render_template('Authenticated/managepayments.html', paymentMethods = paymentMethods,
                           paymentMethodInUse = paymentMethodInUse)

@app.route('/budget', methods=['GET', 'POST'])
@login_required
def budget():
    db = get_db()
    cursor = db.cursor()

    cursor.execute('SELECT CategoryID, CategoryName FROM Category')
    categories = cursor.fetchall()

    if request.method == 'POST':
        budget_amount = float(request.form['budgetAmount'])
        budget_category = request.form['budgetCategory']

        if budget_category == 'new-category':
            new_category_name = request.form['newCategoryName'].strip()

            if new_category_name:
                try:
                    cursor.execute('INSERT INTO Category (CategoryName) VALUES (?)', (new_category_name,))
                    db.commit()

                    cursor.execute('SELECT last_insert_rowid()')
                    new_category_id = cursor.fetchone()[0]

                    cursor.execute('INSERT INTO Budget (UserID, CategoryID, Month, BudgetAmount) VALUES (?, ?, ?, ?)',
                                   (session['userID'], new_category_id, 'current_month', budget_amount))
                    db.commit()

                    flash('Monthly budget set successfully.', 'success')
                except Exception as e:
                    print(e)
                    flash('Something went wrong, please try again!', 'danger')
            else:
                flash('Please enter a valid new category name.', 'danger')
        else:
            try:
                flash('Monthly budget set successfully.', 'success')
            except Exception as e:
                print(e)
                flash('Something went wrong, please try again!', 'danger')

        return redirect(url_for('dashboard'))

    return render_template('Authenticated/budget.html', categories=categories)


if __name__ == '__main__':
    app.run()
