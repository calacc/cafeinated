import os
from flask import Flask, flash, redirect, render_template, request, url_for, session, abort
from flask_sqlalchemy import SQLAlchemy
import datetime
import pyrebase
from firebase import firebase
import firebase_admin
from firebase_admin import credentials
from firebase_admin import firestore
# import FieldFilter

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

def create_new_user(email, type):
    new_user={
        'email': email,
        'type': type,
    }
    doc_ref= db.collection(u'Users').document(new_user['email'])
    doc_ref.set(new_user)

def create_new_shop(name, address, phone_nr, owner):
    new_shop={
        'address': address,
        'name': name, 
        'owner': owner,
        'phone_nr': phone_nr
    }
    
    doc_ref=db.collection(u'Shops').document(name.replace(" ", ""))
    doc_ref.set(new_shop)

def create_new_menu_item(item_name, price, item_type, shop_id):
    current_date = datetime.date.today()
    date_list = [str(current_date.year), str(current_date.month), str(current_date.day)]
    date_added = ' '.join(date_list)
    new_item={
        'name': item_name,
        'price': price, 
        'type': item_type,
        'date_added': date_added
    }
    shop_ref=db.collection(u'Shops').document(shop_id)
    shop_ref.collection('menu').add(new_item)

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
            
            create_new_user(email, 'customer')

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
            
            create_new_user(email, 'shop-owner')

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

@app.route('/my-shops', methods=['POST', 'GET'])
def my_shops():
    if request.method == 'POST':
        form_type = request.form['form_type']
        if form_type=='add_shop':
            name = request.form['name']
            phone_number = request.form['phone_number']
            address = request.form['address']

            create_new_shop(name, address, phone_number, session['user'])
            return redirect('/my-shops')
        
        elif form_type=='add_menu_item':
            item_name = request.form['item_name']
            price = request.form['price']
            item_type = request.form['item_type']
            shop_id = request.form['shop_id']

            create_new_menu_item(item_name, price, item_type, shop_id)
            return redirect('/my-shops')

    else:

        shops_stream = db.collection("Shops").where("owner", "==", session['user']).stream()
        shops={}
        for shop in shops_stream:
            shop_data=shop.to_dict()
            shop_id=shop_data['name'].replace(" ", "")
            menu_items = db.collection("Shops").document(shop_id).collection("menu").stream()
            shop_data['menu'] = [menu_item.to_dict() for menu_item in menu_items]

            shops[shop_id]=shop_data

        current_date = datetime.date.today()
        date_list = [str(current_date.year), str(current_date.month), str(current_date.day)]
        todays_date = ' '.join(date_list)
        print(todays_date)
        return render_template('shop-owner/my-shops.html', shops=shops, todays_date=todays_date)

@app.route('/coffeeshops', methods=['POST', 'GET'])
def index():
    shops_stream = db.collection("Shops").stream()
    shops={}
    for shop in shops_stream:
        shop_data=shop.to_dict()
        shop_id=shop_data['name'].replace(" ", "")
        menu_items = db.collection("Shops").document(shop_id).collection("menu").stream()
        shop_data['menu'] = [menu_item.to_dict() for menu_item in menu_items]

        shops[shop_id]=shop_data

    if 'user' in session:
        user_type = get_user_type(session['user'])
        if user_type=='customer':
            return render_template('customer/shops.html', shops=shops)
        elif user_type=='shop-owner':
            return render_template('shop-owner/shops.html', shops=shops)
    else:
        return render_template('not-logged-in/shops.html', shops=shops)

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