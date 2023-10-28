import os
from flask import Flask, redirect, render_template, request, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pyrebase
from firebase import firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore

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

app.secret_key = 'secret'

cred = credentials.Certificate("coffeeshops.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

def get_user_type(email):
    user_ref = db.collection(u'Users').document(email)
    user_data = user_ref.get().to_dict()
    return user_data.get('type')

# app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///shops.db'
# db = SQLAlchemy(app)


# class Shop(db.Model):
#     name = db.Column(db.String(50), primary_key=True)
#     date_created = db.Column(db.DateTime, default=datetime.utcnow)
#     phone_number = db.Column(db.String(10))
#     address = db.Column(db.String(10))
#     owner = db.Column(db.String(50))

#     def __repr__(self):
#         return '<Shop %r>' % self.name
    
    
def login_is_required(function):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            abort(401)
        else:
            return function()
    return wrapper

@app.route('/create-customer-account', methods=['POST','GET'])
def create_customer_account():
    if('user' in session):
        return redirect('/')
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user=auth.create_user_with_email_and_password(email, password)
            user=auth.sign_in_with_email_and_password(email, password)
            
            new_user={
                'email': email,
                'type': 'customer'
            }
            doc_ref= db.collection(u'Users').document(new_user['email'])
            doc_ref.set(new_user)

            session['user']=email
            return redirect('/')
        except:
            return 'failed to create customer account'
    return render_template('not-logged-in/create-customer-account.html')
   
@app.route('/create-shop-owner-account', methods=['POST','GET'])
def create_shop_owner_account():
    if('user' in session):
        return redirect('/')
    if request.method=='POST':
        email = request.form.get('email')
        password = request.form.get('password')
        try:
            user=auth.create_user_with_email_and_password(email, password)
            user=auth.sign_in_with_email_and_password(email, password)
            
            new_user={
                'email': email,
                'type': 'shop-owner'
            }
            doc_ref = db.collection(u'Users').document(new_user['email'])
            doc_ref.set(new_user)

            session['user']=email
            return redirect('/')
        except:
            return 'failed to create shop owner account'
    return render_template('not-logged-in/create-shop-owner-account.html')

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

@app.route('/logout', endpoint='user logs out from this page')
@login_is_required
def logout():
    if 'user' in session:
        session.pop('user')
        return redirect('/')
    
@app.route('/')
def home(): 
    if 'user' in session:
        user_type = get_user_type(session['user'])
        if user_type=='customer':
            return render_template('customer/home.html')
        elif user_type=='shop-owner':
            return render_template('shop-owner/home.html')
    else:
        return render_template('not-logged-in/home.html')


@app.route('/about-us')
def about_us():
    if 'user' in session:
        user_type = get_user_type(session['user'])
        if user_type=='customer':
            return render_template('customer/about-us.html')
        elif user_type=='shop-owner':
            return render_template('shop-owner/about-us.html')
    else:
        return render_template('not-logged-in/about-us.html')

@app.route('/my-account', endpoint='customer\'s account page')
@login_is_required
def my_account():
    user_type = get_user_type(session['user'])
    if user_type=='customer':
        return render_template('customer/my-account.html')
    elif user_type=='shop-owner':
        return render_template('shop-owner/my-account.html')

@app.route('/shopping-cart', endpoint='customer\'s shopping cart page')
@login_is_required
def shopping_cart():
    return render_template('customer/shopping-cart.html')

# @app.route('/coffeeshops', methods=['POST', 'GET'])
# def index():
#     if request.method == 'POST':
#         name = request.form['name']
#         phone_number = request.form['phone_number']
#         address = request.form['address']

#         new_shop = Shop(name=name, phone_number=phone_number, address=address)

#         try:
#             db.session.add(new_shop)
#             db.session.commit()
#             return redirect('/coffeeshops')
#         except:
#             return 'there was an issue adding your shop'
#     else:
#         shops = Shop.query.order_by(Shop.date_created).all()
#         if 'user' in session:
#             user_type = get_user_type(session['user'])
#             if user_type=='customer':
#                 return render_template('customer/shops.html')
#             elif user_type=='shop-owner':
#                 return render_template('shop-owner/shops.html')
#         else:
            # return render_template('not-logged-in/shops.html', shops=shops)

# @app.route('/delete/<string:name>')
# def delete(name):
#     shop_to_delete = Shop.query.get_or_404(name)

#     try:
#         db.session.delete(shop_to_delete)
#         db.session.commit()
#         return redirect('/coffeeshops')
#     except:
#         return 'There was a problem deleting that shop'
    
# @app.route('/update/<string:name>', methods=['GET', 'POST'])
# def update(name):
#     shop_to_update = Shop.query.get_or_404(name)

#     if request.method == 'POST':
#         shop_to_update.name=request.form['name']
#         shop_to_update.phone_number=request.form['phone_number']
#         shop_to_update.address=request.form['address']

#         try:
#             db.session.commit()
#             return redirect('/coffeeshops')
#         except:
#             return 'There was an issue updating your shop'
#     else:
#         return render_template('customer/update.html', shop=shop_to_update)
    

if __name__ == "__main__":
    app.run(port=1111,debug=True)