from distutils.command import upload
from __init__ import app, db, auth, mybucket, flow, google_client_id
import gets
import time

from flask import Flask, flash, redirect, render_template, request, send_file, url_for, session, abort
import datetime
import uuid
from firebase_admin import credentials, storage
import google.auth.transport.requests
from pip._vendor import cachecontrol
from google.oauth2 import id_token
import requests

def create_new_shop(name, address, phone_nr, owner):
    new_shop={
        'address': address,
        'name': name, 
        'owner': owner,
        'phone_nr': phone_nr
    }
    
    doc_ref=db.collection(u'Shops').document(name.replace(" ", ""))
    doc_ref.set(new_shop)

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
    cart_copy.append({'name': item_name, 'price': item_price, 'shop': shop_name, 'completed': False})

    session['cart'] = cart_copy

    return redirect('/coffeeshops')  

@app.route('/remove_from_cart', methods=['POST'])
def remove_from_cart():
    name_del=request.form['name']
    shop_del=request.form['shop']
    cart_copy = session['cart'].copy()
    count=0
    index=0
    for item in cart_copy:
        if item['name']==name_del and item['shop']==shop_del:
            index=count
        count=count+1
    removed_item = cart_copy.pop(index)
    session['cart'] = cart_copy
    return redirect('/shopping-cart')

@app.route('/place-order', methods=['POST'])
def place_order():
    user_id = session['user'] 
    cart = session.get('cart', [])
    order_id = str(uuid.uuid4())
    current_date = datetime.date.today()
    date_list = [str(current_date.year), str(current_date.month), str(current_date.day)]
    date_added = ' '.join(date_list)

    total_price=0
    for item in cart:
        total_price+=item['price']
    order_data = {
        'user_id': user_id,
        'items': cart,
        'status': 0, # 0-not ready, 1-being delivered, 2-arriving soon, 3-delivered
        'order_id': order_id,
        'date': date_added,
        'total_price': total_price
    }
    order_ref = db.collection('Orders').add(order_data)
    session.pop('cart', None)

    return redirect('/shopping-cart')

@app.route('/edit-account', methods=['POST', 'GET'])
def edit_account():
    user_type = gets.get_user_type(session['user'])
    user_ref = db.collection(u'Users').document(session['user'])
    user_data = user_ref.get().to_dict()
    if  request.method == 'POST':
        updated_user={}
        if user_type=='customer':
            address = request.form['address']
            name = request.form['name']
            phonenr = request.form['phonenr']
            google_auth = request.form.get('google_auth')
            updated_user={
                'address': address,
                'name': name,
                'phonenr': phonenr,
                'google_auth': google_auth
            }
        elif user_type=='shop-owner':
            name = request.form['name']
            phonenr = request.form['phonenr']
            google_auth = request.form.get('google_auth')
            updated_user={
                'name': name,
                'phonenr': phonenr,
                'google_auth': google_auth
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
            return render_template('not-logged-in/error-page.html', errors=["Încercare de creare cont nereușită!"])
    return render_template('not-logged-in/create-customer-account.html')
   
@app.route('/create-shop-owner-account', methods=['POST','GET'])
def create_shop_owner_account():
    if('user' in session):
        return redirect('/')
    if request.method=='POST':
        id_token = request.form.get('idToken')
        email = request.form.get('email')
        name = request.form.get('name')
        password = request.form.get('password')
        phonenr = request.form.get('phonenr')
        try:
            # decoded_token = auth.verify_id_token(id_token)
            # uid = decoded_token['uid']

            # Check if the user already exists
            # user = auth.get_user(uid)

            # new_user = auth.create_user(uid=uid)
            user=auth.create_user_with_email_and_password(email, password)
            user=auth.sign_in_with_email_and_password(email, password)
            
            create_new_user('', email, name, phonenr, 'shop-owner')

            session['user']=email
            return redirect('/')
        except:
            return render_template('not-logged-in/error-page.html', errors=["Încercare de creare cont nereușită!"])
    return render_template('not-logged-in/create-shop-owner-account.html')

@app.route('/-create-customer-account', methods=['POST','GET'])
def create_customer_account_google():
    if('user' in session):
        return redirect('/')
    if request.method=='POST':
        address = request.form.get('address')
        email = request.form.get('email')
        name = request.form.get('name')
        phonenr = request.form.get('phonenr')
        try:
            create_new_user(address, email, name, phonenr, 'customer')
            session['user']=email
            return redirect('/')
        except:
            return render_template('not-logged-in/error-page.html', errors=["Încercare de creare cont nereușită!"])
    return render_template('not-logged-in/create-customer-account-google.html', name=session['name'], email=session['email'])
   
@app.route('/-create-shop-owner-account', methods=['POST','GET'])
def create_shop_owner_account_google():
    if('user' in session):
        return redirect('/')
    if request.method=='POST':
        id_token = request.form.get('idToken')
        email = request.form.get('email')
        name = request.form.get('name')
        phonenr = request.form.get('phonenr')
        try:
            
            create_new_user('', email, name, phonenr, 'shop-owner')

            session['user']=email
            return redirect('/')
        except:
            return render_template('not-logged-in/error-page.html', errors=["Încercare de creare cont nereușită!"])
    return render_template('not-logged-in/create-shop-owner-account-google.html', name=session['name'], email=session['email'])

@app.route('/login', methods=['POST','GET'])
def login():
    if('user' in session):
        return redirect('/')
    if request.method == 'POST':
        form_type=request.form.get('form_type')
        if form_type=='login_password':
            email = request.form.get('email')
            password = request.form.get('password')
            try:
                user=auth.sign_in_with_email_and_password(email, password)
                session['user']=email
                session['pass']=password
                return redirect('/')
            except:
                return render_template('not-logged-in/error-page.html', errors=["Încercare de autentificare nereușită!", 
                                                                                "Emailul sau parola introduse sunt invalide."])
        if form_type=='login_google':
            authorization_url, state = flow.authorization_url(access_type='offline',include_granted_scopes='true')
            session["state"] = state
            return redirect(authorization_url)
    else:
        return render_template('not-logged-in/login.html')

@app.route("/callback")
def callback():
    flow.fetch_token(authorization_response=request.url)

    if not session["state"] == request.args["state"]:
        abort(500)  # State does not match!

    credentials = flow.credentials
    request_session = requests.session()
    cached_session = cachecontrol.CacheControl(request_session)
    token_request = google.auth.transport.requests.Request(session=cached_session)

    id_info = id_token.verify_oauth2_token(
        id_token=credentials._id_token,
        request=token_request,
        audience=google_client_id
    )

    session["google_id"] = id_info.get("sub")
    session["name"] = id_info.get("name")
    session["email"] = user_email = id_info.get('email')
    # print(user_email)

    users_ref = db.collection('Users')
    query = users_ref.where('email', '==', user_email).limit(1)
    docs = query.get()
    if len(docs) > 0 and docs[0].exists:
        session['user']=user_email
        return redirect(url_for('home', _external=True))
    else:
        return render_template('not-logged-in/choose-type.html')

@app.route('/logout')
@gets.login_is_required
def logout():
    if 'user' in session:
        session.pop('cart', None)
        session.pop('user')
        session.clear()
        return redirect('/')
    
@app.route('/delete/<string:shop_id>', methods=['POST'])
def delete_shop(shop_id):
    if request.method == 'POST':
        shop_id=shop_id.replace("_", "")
        doc_ref = db.collection(u'Shops').document(shop_id)
        doc_ref.delete()
        return redirect('/my-shops')

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
        elif form_type=='delete_shop':
            shop_to_delete = request.form['shop_id']
            doc_ref = db.collection(u'Shops').document(shop_to_delete)
            doc_ref.delete()
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
        return render_template('shop-owner/my-shops.html', shops=shops, todays_date=todays_date,
                                generate_map_embed_code=gets.generate_map_embed_code,
                                acceptable_shop_name=gets.acceptable_shop_name,
                                list_images=gets.list_images)

@app.route('/edit-menu/<string:shop_id>/delete-item/<string:item_name_to_delete>', methods=['POST'])
def delete_item(shop_id,item_name_to_delete):
    # Check if the delete button was clicked
    if request.method=='POST':
        id_copy=shop_id
        id_copy=id_copy.replace("_", "")
        user_ref = db.collection(u'Shops').document(id_copy)
        user_data = user_ref.get().to_dict()
        menu_ref = user_ref.collection('menu')
        menu = {doc.id: doc.to_dict() for doc in menu_ref.stream()}

        count = 0
        for item_id, menu_item in menu.items():
            if f'delete_{count}' in request.form:
                print('\n\nintra aici\n\n')
                db.collection(u'Shops').document(id_copy).collection('menu')
                menu_ref = db.collection('Shops').document(id_copy).collection('menu')
                query = menu_ref.where('name', '==', item_name_to_delete)
                docs = query.get()

                for doc in docs:
                    doc.reference.delete()
            count=count+1

        # Redirect back to the items page or wherever you want to go after deletion
        return redirect(url_for('edit_menu_details', shop_id=shop_id))

@app.route('/edit-menu/<string:shop_id>', methods=['POST', 'GET'])
def edit_menu_details(shop_id):
    if request.method == 'POST':
        form_type=request.form['form_type']
        if form_type=='add_menu_item':
            item_name = request.form['item_name']
            price = request.form['price']
            item_type = request.form['item_type']

            create_new_menu_item(item_name, price, item_type, shop_id.replace("_",""))
            return redirect(url_for('edit_menu_details', shop_id=shop_id))
        elif form_type=='update_menu':
            id_copy=shop_id.replace("_", "")
            user_ref = db.collection(u'Shops').document(id_copy)
            user_data = user_ref.get().to_dict()
            menu_ref = user_ref.collection('menu')
            menu = {doc.id: doc.to_dict() for doc in menu_ref.stream()}

            count = 0
            for item_id, menu_item in menu.items():
                name = request.form.get(f'item_name_{count}')
                price = request.form.get(f'price_{count}')
                item_type = request.form.get(f'item_type_{count}')
                date_added = menu_item.get('date_added', '')  # Ensure date_added is retrieved properly
                print(f'delete_{count}' in request.form)
                print(request.form)

                if name is None:
                    name = menu_item.get('name', '')
                if price is None:
                    price = menu_item.get('price', '')
                if item_type is None:
                    item_type = menu_item.get('type', '')

                updated_item = {
                    'name': name,
                    'price': price,
                    'type': item_type,
                    'date_added': date_added
                }

                shop_ref = db.collection(u'Shops').document(id_copy)
                doc_ref = shop_ref.collection('menu').document(item_id)
                doc_ref.set(updated_item, merge=True)
                print(f'Document After Update ({item_id}): {doc_ref.get().to_dict()}\n')

                count += 1


            return redirect(url_for('edit_menu_details', shop_id=shop_id))
    else:
        shop_id=shop_id.replace("_", " ")
        shop_ref = db.collection('Shops').where('name', '==', shop_id).limit(1)
        this_shop = shop_ref.get()
        print(this_shop)
        shop_doc = this_shop[0]
        this_shop_data = shop_doc.to_dict()
        menu_items = db.collection("Shops").document(shop_id.replace(" ","")).collection("menu").stream()
        this_shop_data['menu'] = [menu_item.to_dict() for menu_item in menu_items]

        shops_stream = db.collection("Shops").where("owner", "==", session['user']).stream()
        shops={}
        for shop in shops_stream:
            shop_data=shop.to_dict()
            shop_id=shop_data['name'].replace(" ", "")
            menu_items = db.collection("Shops").document(shop_id).collection("menu").stream()
            shop_data['menu'] = [menu_item.to_dict() for menu_item in menu_items]

            shops[shop_id]=shop_data
        print(this_shop_data)
        return render_template('shop-owner/edit-menu-items.html', shops=shops, 
                               this_shop_data=this_shop_data, 
                               generate_map_embed_code=gets.generate_map_embed_code,
                               acceptable_shop_name=gets.acceptable_shop_name)

@app.route('/edit-shop/<string:shop_id>', methods=['POST', 'GET'])
def edit_shop_details(shop_id):
    if request.method == 'POST':
        form_type=request.form['form_type']
        if form_type=='edit_shop':
            copy_id=shop_id.replace("_", "")
            name = request.form['shop_name']
            address = request.form['address']
            phone_nr = request.form['phonenr']
            shop_id = request.form['shop_id']
            user_ref = db.collection(u'Shops').document(copy_id)
            user_data = user_ref.get().to_dict()
            menu=user_data.get('menu')
            updated_shop={
                'address': address,
                'name': name, 
                'owner': session['user'],
                'phone_nr': phone_nr,
                'menu': menu
            }
            doc_ref=db.collection(u'Shops').document(name.replace(" ", ""))
            doc_ref.update(updated_shop)
            
            file = request.files['file']
            if file:
                good_name=name.replace(" ", "")
                filename = f"logos/{good_name}"

                blob = mybucket.blob(filename)
                if blob.exists():
                    blob.delete()

                blob = mybucket.blob(filename)
                blob.upload_from_string(file.read(), content_type=file.content_type)

                file_url = f"{blob.public_url}?timestamp={int(time.time())}"

                doc_ref=db.collection(u'Shops').document(name.replace(" ", ""))
                doc_ref.update({'logo_url': file_url})
        return redirect(url_for('my_shop_page', shop_id=shop_id))
    else:
        shop_id=shop_id.replace("_", " ")
        shop_ref = db.collection('Shops').where('name', '==', shop_id).limit(1)
        this_shop = shop_ref.get()
        print(this_shop)
        shop_doc = this_shop[0]
        this_shop_data = shop_doc.to_dict()
        menu_items = db.collection("Shops").document(shop_id).collection("menu").stream()
        this_shop_data['menu'] = [menu_item.to_dict() for menu_item in menu_items]

        shops_stream = db.collection("Shops").where("owner", "==", session['user']).stream()
        shops={}
        for shop in shops_stream:
            shop_data=shop.to_dict()
            shop_id=shop_data['name'].replace(" ", "")
            menu_items = db.collection("Shops").document(shop_id).collection("menu").stream()
            shop_data['menu'] = [menu_item.to_dict() for menu_item in menu_items]

            shops[shop_id]=shop_data
        print(this_shop_data)
        return render_template('shop-owner/edit-shop-details.html', shops=shops, 
                               this_shop_data=this_shop_data, 
                               generate_map_embed_code=gets.generate_map_embed_code,
                               acceptable_shop_name=gets.acceptable_shop_name,
                               list_images=gets.list_images)

@app.route('/images/<shop_name>')
def get_logo(shop_name):
    try:
        folder_path = f"logos/{shop_name}"
        image_urls = gets.list_images(folder_path)
        if image_urls:
            return redirect(image_urls[0])
        else:
            return "No images found for the specified shop."

    except Exception as e:
        return str(e)

@app.route('/<string:shop_id>', methods=['POST', 'GET'])
def my_shop_page(shop_id):
    if request.method == 'POST':
        form_type = request.form['form_type']
        if form_type=='add_menu_item':
            item_name = request.form['item_name']
            price = request.form['price']
            item_type = request.form['item_type']
            shop_id = request.form['shop_id']

            create_new_menu_item(item_name, price, item_type, shop_id)
            return redirect(url_for('my_shop_page', shop_id=shop_id))
        elif form_type=='delete_shop':
            shop_to_delete = request.form['shop_id']
            doc_ref = db.collection(u'Shops').document(shop_to_delete)
            doc_ref.delete()
            return redirect('/my-shops')
    else:
        shop_id=shop_id.replace("_", " ")
        shop_ref = db.collection('Shops').where('name', '==', shop_id).limit(1)
        this_shop = shop_ref.get()
        print(this_shop)
        shop_doc = this_shop[0]
        this_shop_data = shop_doc.to_dict()
        menu_items = db.collection("Shops").document(shop_id).collection("menu").stream()
        this_shop_data['menu'] = [menu_item.to_dict() for menu_item in menu_items]

        shops_stream = db.collection("Shops").where("owner", "==", session['user']).stream()
        shops={}
        for shop in shops_stream:
            shop_data=shop.to_dict()
            shop_id=shop_data['name'].replace(" ", "")
            menu_items = db.collection("Shops").document(shop_id).collection("menu").stream()
            shop_data['menu'] = [menu_item.to_dict() for menu_item in menu_items]

            shops[shop_id]=shop_data
        print(this_shop_data)
        return render_template('shop-owner/myshop-page.html', shops=shops, 
                               this_shop_data=this_shop_data, 
                               generate_map_embed_code=gets.generate_map_embed_code,
                               acceptable_shop_name=gets.acceptable_shop_name)

@app.route('/all-users')
def all_users():

    users = [ user.to_dict() for user in  db.collection('Users').stream()]
    shops_stream = db.collection("Shops").stream()
    all_shops = {shop.id.replace(" ", " "): shop.to_dict() for shop in shops_stream}
    all_shops_list = list(all_shops.keys())
    shop_content = {shop_id: {'shop_name': shop_data['name'], 'owner': shop_data['owner']} for shop_id, shop_data in all_shops.items()}

    all_users={}
    # print(active_orders)
    for user in users:
        user_type=user['type']
        if user_type not in ['admin', 'rider']:
            user_mail=user['email']
            user_name=user['name']
            user_phonenr=user['phonenr']
            shops=[]
            if user_type=='shop-owner':
                for shopid, shopdata in shop_content.items():
                    if shopdata['owner']==user_mail:
                        shops.append(shopdata['shop_name'])
            all_users.update({user_mail: {'name': user_name, 'type': user_type, 'phonenr':user_phonenr, 'shops': shops}})
            
    return render_template('admin/users.html',all_users=all_users)

@app.route('/riders', methods=['POST', 'GET'])
def rider():

    if request.method == 'POST':
        rider_name = request.form['rider_name']
        rider_email = request.form['rider_email']

        new_rider={
            'name': rider_name, 
            'email': rider_email,
            'type': 'rider'
        }
        
        doc_ref=db.collection(u'Users').document(rider_email)
        doc_ref.set(new_rider)

        user=auth.create_user_with_email_and_password(rider_email, "riderCafeinated")

        return redirect("/riders")
    else:
        users = [ user.to_dict() for user in  db.collection('Users').stream()]

        riders={}
        # print(active_orders)
        for user in users:
            user_type=user['type']
            if user_type=='rider':
                user_mail=user['email']
                user_name=user['name']
                riders.update({user_mail: {'name': user_name, 'email': user_mail}})
                
        return render_template('admin/riders.html',riders=riders)

@app.route('/all-orders')
def all_orders():
    shops_stream = db.collection("Shops").stream()
    all_shops = {shop.id.replace(" ", " "): shop.to_dict() for shop in shops_stream}
    all_shops_list = list(all_shops.keys())
    shop_content = {shop_id: {'shop_name': shop_data['name'], 'items': [], 'address': shop_data['address']} for shop_id, shop_data in all_shops.items()}

    active_orders = [ order.to_dict() for order in  db.collection('Orders').stream()]
    shop_orders={}
    # print(active_orders)
    for order in active_orders:
        order_id = order['order_id']
        if order_id not in shop_orders:
            shop_orders[order_id] = {'shops': {}, 'date': order['date'], 'status': order['status'],
                                      'user_id': order['user_id']}

        for item in order['items']:
            shop_id = item['shop']
            if shop_id not in shop_orders:
                shop_orders[order_id]['shops'][shop_id] = {
                    'shop_name': shop_content[shop_id]['shop_name'],
                    'items':[], 
                    'address':shop_content[shop_id]['address']
                }
            copied_item = item.copy()
            shop_orders[order_id]['shops'][shop_id]['items'].append(copied_item)
    return render_template('admin/orders.html',shop_orders=shop_orders,
                                can_complete_order=gets.can_complete_order,
                                get_user_address=gets.get_user_address,
                                get_user_phonenr=gets.get_user_phonenr,
                                get_user_name=gets.get_user_name)
