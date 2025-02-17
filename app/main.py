from flask import Flask, render_template, url_for, flash, redirect, session, request
from functools import wraps
import os
import mysql.connector
import pymongo
from app.lib.init_rdbms import *
from app.lib.mongodb_migration import *
from app.lib.db_operations import *

app = Flask(__name__)

# Set a secret key to protect against attacks
app.config['SECRET_KEY'] = '080654bf4e3db4cbf49c39c8bbd1e9ee'
app.config['ACTIVE_DB'] = ''

# Init an empty MySQL database
mysql_config = {'user': 'user', 'password': 'password', 'host': 'mysql', 'port': '3306', 'database': 'webshop_mysql_db'}
db = mysql.connector.connect(**mysql_config)

# Init an empty MongoDB
mongo_client = pymongo.MongoClient('mongodb://user:password@mongo:27017/')
mongo_db = mongo_client['webshop_mongo_db']
drop_all_collections(mongo_db=mongo_db)

def is_logged_in(f):
    """ Checks if a user is currenty logged in. """
    @wraps(f)
    def wrap(*args, **kwargs):
        if session.get('logged_in'):
            return f(*args, **kwargs)
        else:
            flash(message='Please login first.', category='danger')
            return redirect(url_for('login'))
    return wrap

def is_database_initialized(f):
    """ Checks a database has been initialized yet. """
    @wraps(f)
    def wrap(*args, **kwargs):
        if app.config['ACTIVE_DB'] in ['MySQL', 'MongoDB']:
            return f(*args, **kwargs)
        else:
            flash(message='Unauthorized. Please initialize database.', category='danger')
            return redirect(url_for('reset'))
    return wrap

@app.route('/')
def reset():
    """ Landing page, checks if database has been initialized and if user is logged in. """
    if app.config['ACTIVE_DB'] == '':
        session.clear()
        return render_template('init_db.html')
    elif session.get('logged_in'):
        return redirect(url_for('home'))
    else:
        return redirect(url_for('login'))

@app.route('/reset_db')
def reset_db():
    """ Page that lets users initialize the MySQL database. """
    if not app.config['ACTIVE_DB']:
        app.config['ACTIVE_DB'] = 'MySQL'
        sql_drop_tables(db=db)
        sql_create_tables(db=db)
        sql_fill_all_tables(db=db)
        flash(message="MySQL database successfully initialized.", category='success')
        return redirect(url_for('login'))
    else:
        flash(message="MySQL database has already been initialized.", category='warning')
        return redirect(url_for('home'))

@app.route('/login', methods=['GET', 'POST'])
@is_database_initialized
def login():
    """ Login page needed for user authentication. Only accessible after db is initialized. """
    from app.lib.forms import LoginForm
    form = LoginForm()
    if form.validate_on_submit():
        user = find_user_by_email(db=db, mongo_db=mongo_db, email=form.email.data)
        if user and (user.get('password') == form.password.data):
            session['logged_in'] = True
            session['user_id'] = user.get('user_id') or user.get('_id')
            session['first_name'] = user.get('first_name')
            session['last_name'] = user.get('last_name')
            session['email'] = user.get('email')
            session['date_registered'] = user.get('date_registered')
            session['db_status'] = app.config['ACTIVE_DB']
            flash(message=f'Log in successful!', category='success')
            return redirect(url_for('home'))
        else:
            flash(message="Login Unsuccessful. Please check email and password.", category='danger')
    return render_template('login.html', form=form)    

@app.route('/logout')
def logout():
    """ logout current user by clearing current session and redirect to login page """
    session.clear()
    flash(message='You have been logged out!', category='success')
    return redirect(url_for('login'))

@app.route('/home')
@is_database_initialized
@is_logged_in
def home():
    sidebar = {
        'title': 'Webshop Information:',
        'description': 'Status of MySQL database and MongoDB can be observed below. '
                           + 'To migrate data from MySQL database to MongoDB click the <b>Migrate</b> button.',
        'button': 'migrate',
        'data': {'MySQL tables': len(pd.read_sql_query(sql='SHOW Tables', con=db)),
                     'MongoDB collections': len(mongo_db.list_collection_names())}
    }
    return render_template('home.html', sidebar=sidebar)

@app.route('/profile', methods=['GET', 'POST'])
@is_database_initialized
@is_logged_in
def profile():
    """ Profile page allowing users to view/change personal info. """
    from app.lib.forms import UpdateProfileForm
    form = UpdateProfileForm()

    # Update user profile info (first and/or last name)
    if request.method == 'POST':
        update_user_by_email(db=db, mongo_db=mongo_db, email=session['email'], form=form)
        session['first_name'] = form.first_name.data
        session['last_name'] = form.last_name.data
        flash(message='Profile information updated.', category='success')
    else:
        user = find_user_by_email(db=db, mongo_db=mongo_db, email=session['email'])
        form.first_name.data = str(user.get('first_name'))
        form.last_name.data = str(user.get('last_name'))
        form.date_registered.data = pd.to_datetime(user.get('date_registered'))
        if not all([user.get('first_name'),
                    user.get('last_name')]):
            flash(message='Please enter first and last name!', category='info')

    # Fetch user profile picture
    file_name = convert_email_to_filename(session['email'])        
    user_files = [f for f in os.listdir('app/static/img/users/') if f.startswith(f"{file_name}.")]

    if user_files:
        image_file = url_for('static', filename=f'img/users/{user_files[0]}')
    else:
        image_file = url_for('static', filename='img/users/default.png')

    sidebar = {
        'title': 'DB Information:',
        'description': 'Status of MySQL database and MongoDB can be observed below. '
                           + 'To migrate data from MySQL database to MongoDB click the <b>Migrate</b> button.',
        'button': 'migrate',
        'data': {'MySQL tables': len(pd.read_sql_query(sql='SHOW Tables', con=db)),
                     'MongoDB collections': len(mongo_db.list_collection_names())}
    }
    return render_template('profile.html', image_file=image_file, form=form, sidebar=sidebar)

def convert_email_to_filename(email):
    file_name, domain_name = email.split('@', 1)
    file_name = file_name.replace('.', '_')
    return file_name

@app.route('/report/<string:report_type>', methods=['GET', 'POST'])
@is_database_initialized
@is_logged_in
def report(report_type):
    """ Report page currently only used for unpaid invoices report. """
    if report_type == 'invoices':
        df = report_unpaid_invoices(db=db, mongo_db=mongo_db)
    else:
        return render_template('home.html')

    sidebar = {
        'title': 'Additional report information',
        'description': 'The data included in the shown table represents a report on the currently <b>unpaid invoices</b>. '
         + 'More specifically, it shows the number of invoices per user that have not been paid yet for orders created within the last year. '
    }

    return render_template('report.html', df=df, report_type=report_type, sidebar=sidebar)

@app.route('/migrate', methods=['GET', 'POST'])
@is_database_initialized
@is_logged_in
def migrate():
    """ Migration page letting users migrate from MySQL to Mongo database. """
    # Save the referrer URL, default to 'profile' if None
    referrer_url = request.referrer or url_for('profile')

    if app.config['ACTIVE_DB'] == 'MySQL':
        # Copy all data from MySQL database to MongoDB
        migrate_data(db=db, mongo_db=mongo_db)
        # Drop all tables from MySQL database
        sql_drop_tables(db=db)

        # Change which database is currently active in config
        app.config['ACTIVE_DB'] = 'MongoDB'
        session['db_status'] = 'MongoDB'
        flash(message=f"Successfully migrated to MongoDB.", category='success')

        return redirect(referrer_url)
    else:
        flash(message="Migration to MongoDB already completed.", category='warning')
        return redirect(referrer_url)

@app.route('/shopping_basket', methods=['GET', 'POST'])
@is_database_initialized
@is_logged_in
def shopping_basket():
    """ Shopping basket page, lets users see the items they have added. """
    # Fetch shopping basket data for current user
    df = find_cart_by_user_id(db=db, mongo_db=mongo_db, user_id=session['user_id'])
    return render_template('shopping_basket.html', title='Shopping Basket', df=df)

@app.route('/checkout', methods=['GET', 'POST'])
@is_database_initialized
@is_logged_in
def checkout():
    """ Checkout page, lets users review and finalize their order. """
    df = find_cart_by_user_id(db=db, mongo_db=mongo_db, user_id=session['user_id'])
    return render_template('checkout.html', title='Checkout', df=df)

@app.route('/buy', methods=['POST'])
@is_database_initialized
@is_logged_in
def buy():
    """ Buy page, lets users place their order. """
    df = find_cart_by_user_id(db=db, mongo_db=mongo_db, user_id=session['user_id'])
    result = create_and_insert_order(db=db, mongo_db=mongo_db, df=df, user_id=session['user_id'])
    if result == True:
        flash(message=f"Order placed successfully!", category='success')
        return redirect(url_for('home'))
    else: 
        flash(message=f"Order could not be placed!", category='danger')
        return redirect(url_for('home'))