import os
import uuid
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

def create_new_user(address, email, name, phonenr, type):
    if type=='customer':
        new_user={
            'address': address,
            'email': email,
            'name': name,
            'phonenr': phonenr,
            'type': type,
        }
    else:
        new_user={
            'email': email,
            'name': name,
            'phonenr': phonenr,
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

@app.route('/delete-account', methods=['POST'])
def delete_account():
    if 'user' in session:
        if request.method=='POST':
            user_to_delete=session['user']
            session.pop('cart', None)
            session.pop('user')
            doc_ref = db.collection(u'Users').document(user_to_delete)
            doc_ref.delete()
    return redirect('/')
    

@app.route('/add-to-cart', methods=['POST'])
def add_to_cart():
    item_name = request.form['item_name']
    item_price = float(request.form['item_price'])
    shop_name = request.form['shop_name']

    if 'cart' not in session:
        session['cart'] = []

    cart_copy = session['cart'].copy()
    cart_copy.append({'name': item_name, 'price': item_price, 'shop': shop_name})

    session['cart'] = cart_copy

    return redirect('/coffeeshops')  

@app.route('/shopping-cart')
def shopping_cart():
    cart = session.get('cart', [])
    print(f"Cart items: {cart}")
    return render_template('customer/shopping-cart.html', cart=cart)

@app.route('/place-order', methods=['POST'])
def place_order():

    user_id = session['user'] 
    cart = session.get('cart', [])
    order_id = str(uuid.uuid4())

    order_data = {
        'user_id': user_id,
        'items': cart,
        'status': False,
        'order_id': order_id,
    }
    order_ref = db.collection('Orders').add(order_data)
    session.pop('cart', None)

    return redirect('/')

@app.route('/orders', methods=['GET'])
def active_orders():
    active_orders = [order.to_dict() for order in db.collection('Orders').where('status', '==', False).stream()]

    shops_stream = db.collection("Shops").where("owner", "==", session['user']).stream()
    owned_shops = {shop.id.replace(" ", " "): shop.to_dict() for shop in shops_stream}

    shop_orders = {shop_id: {'shop_name': shop_data['name'], 'orders': []} for shop_id, shop_data in owned_shops.items()}

    for order in active_orders:
        for item in order['items']:
            if item['shop'] in owned_shops:
                shop_id = item['shop']
                shop_orders[shop_id]['orders'].append(order)

    return render_template('shop-owner/orders.html', shop_orders=shop_orders)

@app.route('/orders', methods=['POST'])
def complete_order():
    order_id=request.form['order_id']
    order_ref = db.collection('Orders').where('order_id', '==', order_id).limit(1)
    orders = order_ref.get()
    order_doc = orders[0]
    order_doc.reference.update({'status': True})
    print(f"Order {order_id} completed successfully.")
    return redirect('/orders')

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            abort(401)
        else:
            return function()
    return wrapper

@app.route('/edit-account', methods=['POST', 'GET'])
def edit_account():
    user_type = get_user_type(session['user'])
    user_ref = db.collection(u'Users').document(session['user'])
    user_data = user_ref.get().to_dict()
    if  request.method == 'POST':
        updated_user={}
        if user_type=='customer':
            address = request.form['address']
            name = request.form['name']
            phonenr = request.form['phonenr']
            updated_user={
                'address': address,
                'name': name,
                'phonenr': phonenr,
            }
        elif user_type=='shop-owner':
            name = request.form['name']
            phonenr = request.form['phonenr']
            updated_user={
                'name': name,
                'phonenr': phonenr,
            }
        doc_ref= db.collection(u'Users').document(session['user'])
        doc_ref.update(updated_user)
        return redirect('/my-account')
    else:
        if user_type=='customer':
            return render_template('customer/edit-account.html', user_data=user_data)
        elif user_type=='shop-owner':
            return render_template('shop-owner/edit-account.html', user_data=user_data)

@app.route('/create-customer-account', methods=['POST','GET'])
def create_customer_account():
    if('user' in session):
        return redirect('/')
    if request.method=='POST':
        address = request.form.get('address')
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        phonenr = request.form.get('phonenr')
        try:
            user=auth.create_user_with_email_and_password(email, password)
            user=auth.sign_in_with_email_and_password(email, password)
            
            create_new_user(address, email, name, phonenr, 'customer')

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
        name = request.form.get('name')
        password = request.form.get('password')
        phonenr = request.form.get('phonenr')
        try:
            user=auth.create_user_with_email_and_password(email, password)
            user=auth.sign_in_with_email_and_password(email, password)
            
            create_new_user('', email, name, phonenr, 'shop-owner')

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

@app.route('/logout')
@login_is_required
def logout():
    if 'user' in session:
        session.pop('cart', None)
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
    user_ref = db.collection(u'Users').document(session['user'])
    user_data = user_ref.get().to_dict()
    if user_type=='customer':
        return render_template('customer/my-account.html', user_data=user_data)
    elif user_type=='shop-owner':
        return render_template('shop-owner/my-account.html', user_data=user_data)

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
    
if __name__ == "__main__":
    app.run(port=1111,debug=True)