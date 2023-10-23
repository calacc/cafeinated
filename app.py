import os
from flask import Flask, redirect, render_template, request, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pyrebase
from firebase import firebase

app = Flask(__name__)

config = {
    'apiKey': 'AIzaSyDkHcb2ygZuvYI3MZ1pB2WDISC7vgAmLUE',
    'authDomain': 'cafeinated-ab14e.firebaseapp.com',
    'projectId': 'cafeinated-ab14e',
    'storageBucket': 'cafeinated-ab14e.appspot.com',
    'messagingSenderId': '29698415898',
    'appId': '1:29698415898:web:ef6e70fc421929b2a1a0a3',
    'measurementId': 'G-X7J5JBGF4L',
    'databaseURL': 'https://console.firebase.google.com/project/cafeinated-ab14e/database/cafeinated-ab14e-default-rtdb/data/~2F'
}

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()
db = firebase.database()

app.secret_key = 'secret'


def login_is_required(function):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            abort(401)
        else:
            return function()
    return wrapper

@app.route('/create-account', methods=['POST','GET'])
def create_account():
    if('user' in session):
        return redirect('/')
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user=auth.create_user_with_email_and_password(email, password)
            user=auth.sign_in_with_email_and_password(email, password)
            session['user']=email
            return redirect('/')
        except:
            return 'failed to create account'
    return render_template('not-logged-in/create-account.html')
   

@app.route('/login', methods=['POST','GET'])
def login():
    if('user' in session):
        return redirect('/')
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user=auth.sign_in_with_email_and_password(email, password)
            session['user']=email
            return redirect('/')
        except:
            return 'failed to log in'

    else:
        return render_template('not-logged-in/login.html')

@app.route('/logout', endpoint='customer logs out from this page')
@login_is_required
def logout():
    if 'user' in session:
        session.pop('user')
        return redirect('/')

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
db = SQLAlchemy(app)

class Todo(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.String(200), nullable=False)
    date_created = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return '<Task %r>' % self.id
    
@app.route('/')
def home(): 
    if 'user' in session:
        return render_template('customer/home.html')
    else:
        return render_template('not-logged-in/home.html')


@app.route('/about-us')
def about_us():
    if 'user' in session:
        return render_template('customer/about-us.html')
    else:
        return render_template('not-logged-in/about-us.html')

@app.route('/my-account', endpoint='customer\'s account page')
@login_is_required
def my_account():
    return render_template('customer/my-account.html')

@app.route('/shopping-cart', endpoint='customer\'s shopping cart page')
@login_is_required
def shopping_cart():
    return render_template('customer/shopping-cart.html')

@app.route('/coffeeshops', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':
        task_content = request.form['content']
        new_task = Todo(content=task_content)

        try:
            db.session.add(new_task)
            db.session.commit()
            return redirect('/coffeeshops')
        except:
            return 'there was an issue adding your task'
    else:
        tasks = Todo.query.order_by(Todo.date_created).all()
        if 'user' in session:
            return render_template('customer/shops.html', tasks=tasks)
        else:
            return render_template('not-logged-in/shops.html', tasks=tasks)

@app.route('/delete/<int:id>')
def delete(id):
    task_to_delete = Todo.query.get_or_404(id)

    try:
        db.session.delete(task_to_delete)
        db.session.commit()
        return redirect('/coffeeshops')
    except:
        return 'There was a problem deleting that task'
    
@app.route('/update/<int:id>', methods=['GET', 'POST'])
def update(id):
    task_to_update = Todo.query.get_or_404(id)

    if request.method == 'POST':
        task_to_update.content=request.form['content']

        try:
            db.session.commit()
            return redirect('/coffeeshops')
        except:
            return 'There was an issue updating your task'
    else:
        return render_template('customer/update.html', task=task_to_update)
    

if __name__ == "__main__":
    app.run(port=1111,debug=True)