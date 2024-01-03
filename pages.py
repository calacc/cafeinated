from __init__ import app, db

from flask import Flask, flash, redirect, render_template, request, url_for, session, abort
from itertools import chain

import gets


@app.route('/shopping-cart')
def shopping_cart():
    cart = session.get('cart', [])
    print(f"Cart items: {cart}")
    items_clean={}
    for item in cart:
        if item['shop'] not in items_clean:
            items_clean[item['shop']]=[]
        items_clean[item['shop']].append(item)
    print(items_clean)
    return render_template('customer/shopping-cart.html', 
                           items_clean=items_clean,
                           get_cart_total_price=gets.get_cart_total_price)


@app.route('/my-orders')
def my_orders():
    user_type = gets.get_user_type(session['user'])
    if user_type=='customer':
        my_orders_active = [
            order.to_dict() for order in chain(
                db.collection('Orders').where('user_id', '==', session['user']).where('status', '==', 0).stream(),
                db.collection('Orders').where('user_id', '==', session['user']).where('status', '==', 1).stream(),
                db.collection('Orders').where('user_id', '==', session['user']).where('status', '==', 2).stream()
            )
        ]

        my_orders_inactive = [
            order.to_dict() for order in db.collection('Orders').where('user_id', '==', session['user']).where('status', '==', 3).stream()
        ]
        return render_template('customer/my-orders.html', my_orders_active=my_orders_active, my_orders_inactive=my_orders_inactive)

@app.route('/orders', methods=['GET'])
def active_orders():
    # active_orders = [order.to_dict() for order in db.collection('Orders').where('status', '==', False).stream()]
    user_type = gets.get_user_type(session['user'])
    if user_type=='shop-owner':
        shops_stream = db.collection("Shops").where("owner", "==", session['user']).stream()
        owned_shops = {shop.id.replace(" ", " "): shop.to_dict() for shop in shops_stream}
        owned_shops_list = list(owned_shops.keys())

        active_orders = [order.to_dict() for order in db.collection('Orders').where('status', '==', 0).stream()]


        shop_content = {shop_id: {'shop_name': shop_data['name'], 'items': []} for shop_id, shop_data in owned_shops.items()}
        shop_orders={}

        for order in active_orders:
            order_id = order['order_id']

            for item in order['items']:
                if item['shop'] in owned_shops and item['completed']==False:
                    shop_id = item['shop']
                    if shop_id not in shop_orders:
                        shop_orders[shop_id] = {}
                    if order_id not in shop_orders[shop_id]:
                        shop_orders[shop_id][order_id] = {'shop_name': shop_content[shop_id]['shop_name'], 'items':[]}
                    copied_item = item.copy()
                    shop_orders[shop_id][order_id]['items'].append(copied_item)
        print(shop_content)
        return render_template('shop-owner/orders.html', shop_orders=shop_orders)
    elif user_type=='rider':

        shops_stream = db.collection("Shops").stream()
        all_shops = {shop.id.replace(" ", " "): shop.to_dict() for shop in shops_stream}
        all_shops_list = list(all_shops.keys())
        shop_content = {shop_id: {'shop_name': shop_data['name'], 'items': [], 'address': shop_data['address']} for shop_id, shop_data in all_shops.items()}

        active_orders = [
            order.to_dict() for order in chain(
                db.collection('Orders').where('status', '==', 0).stream(),
                db.collection('Orders').where('status', '==', 1).stream(),
                db.collection('Orders').where('status', '==', 2).stream()
            )
        ]
        shop_orders={}
        # print(active_orders)
        for order in active_orders:
            order_id = order['order_id']
            if order_id not in shop_orders:
                shop_orders[order_id] = {'shops': {}, 'date': order['date'], 'status': order['status'], 'user_id': order['user_id']}

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

        return render_template('delivery/orders.html', shop_orders=shop_orders,
                                can_complete_order=gets.can_complete_order,
                                get_user_address=gets.get_user_address,
                                get_user_phonenr=gets.get_user_phonenr,
                                get_user_name=gets.get_user_name)

@app.route('/orders', methods=['POST'])
def complete_order():
    user_type = gets.get_user_type(session['user'])
    order_id=request.form['order_id']
    order_ref = db.collection('Orders').where('order_id', '==', order_id).limit(1)
    orders = order_ref.get()
    order_doc = orders[0]
    order_data = order_doc.to_dict()

    if user_type=='shop-owner':
        shop_id=request.form['shop_id']
        count=0
        for item in order_data.get('items', []):
            if item['shop'] == shop_id:
                order_data['items'][count]['completed'] = True
            count=count+1

    elif user_type=='rider':
        form_type=request.form['form_type']
        if form_type=='complete_order':
            order_data['status']=1
        elif form_type=='order_arriving_soon':
            order_data['status']=2
        elif form_type=='deliver_order':
            order_data['status']=3

    order_doc.reference.set(order_data)
    return redirect('/orders')

@app.route('/')
def home(): 
    if 'user' in session:
        user_type = gets.get_user_type(session['user'])
        if user_type=='admin':
            return render_template('admin/home.html')
        elif user_type=='customer':
            return render_template('customer/home.html')
        elif user_type=='shop-owner':
            return render_template('shop-owner/home.html')
        elif user_type=='rider':
            return render_template('delivery/home.html')
    else:
        return render_template('not-logged-in/home.html')

@app.route('/about-us')
def about_us():
    if 'user' in session:
        user_type = gets.get_user_type(session['user'])
        if user_type=='customer':
            return render_template('customer/about-us.html')
        elif user_type=='shop-owner':
            return render_template('shop-owner/about-us.html')
    else:
        return render_template('not-logged-in/about-us.html')

@app.route('/my-account', endpoint='customer\'s account page')
@gets.login_is_required
def my_account():
    user_type = gets.get_user_type(session['user'])
    user_ref = db.collection(u'Users').document(session['user'])
    user_data = user_ref.get().to_dict()
    if user_type=='customer':
        return render_template('customer/my-account.html', user_data=user_data)
    elif user_type=='shop-owner':
        return render_template('shop-owner/my-account.html', user_data=user_data)

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
        user_type = gets.get_user_type(session['user'])
        if user_type=='customer':
            return render_template('customer/shops.html', shops=shops, 
                                    generate_map_embed_code=gets.generate_map_embed_code,
                                    acceptable_shop_name=gets.acceptable_shop_name,
                                    list_images=gets.list_images)
        elif user_type=='shop-owner':
            return render_template('shop-owner/shops.html', shops=shops, 
                                    generate_map_embed_code=gets.generate_map_embed_code,
                                    acceptable_shop_name=gets.acceptable_shop_name,
                                    list_images=gets.list_images)
    else:
        return render_template('not-logged-in/shops.html', shops=shops, 
                                    generate_map_embed_code=gets.generate_map_embed_code,
                                    acceptable_shop_name=gets.acceptable_shop_name,
                                    list_images=gets.list_images)
 