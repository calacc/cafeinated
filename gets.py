from __init__ import db, mybucket

from flask import session, abort
from geopy.geocoders import Nominatim

def list_images(folder_path):
    # List files in the specified folder in Firebase Storage
    blobs = mybucket.list_blobs(prefix=folder_path)
    image_urls = [blob.public_url for blob in blobs]
    return image_urls

def acceptable_shop_name(name):
    return name.replace(" ", "_")

def get_cart_total_price():
    cart = session.get('cart', [])
    total_price=0
    for item in cart:
        total_price+=item['price']
    return total_price

def get_user_type(email):
    user_ref = db.collection(u'Users').document(email)
    user_data = user_ref.get().to_dict()
    return user_data.get('type')

def get_user_address(email):
    user_ref = db.collection(u'Users').document(email)
    user_data = user_ref.get().to_dict()
    return user_data.get('address')

def get_user_phonenr(email):
    user_ref = db.collection(u'Users').document(email)
    user_data = user_ref.get().to_dict()
    return user_data.get('phonenr')

def get_user_name(email):
    user_ref = db.collection(u'Users').document(email)
    user_data = user_ref.get().to_dict()
    return user_data.get('name')

def can_complete_order(order_data):

    if order_data['status']>0 and order_data['status']<3:
        return True
    for shop_id, shop_data in order_data['shops'].items():
        for item in shop_data['items']:
            if item['completed']==False:
                return False
    return True

def login_is_required(function):
    def wrapper(*args, **kwargs):
        if 'user' not in session:
            abort(401)
        else:
            return function()
    return wrapper

def geocode_address(address):
    geolocator = Nominatim(user_agent='cafeinated-ab14e')
    location = geolocator.geocode(address)

    if location:
        return location.latitude, location.longitude
    else:
        return None
    
def generate_map_embed_code(address):
    coordinates = geocode_address(address)

    if coordinates:
        return f'<iframe width="500px" height="400px" frameborder="0" style="border:0; border-radius:10px; margin-top: calc(100% - 80%);" ' \
            f'src="https://www.google.com/maps/embed/v1/view?key=AIzaSyA4YbofL5tc2as0qsmjv3yDc556NaD3usE&center={coordinates[0]},{coordinates[1]}&zoom=20" allowfullscreen></iframe>'
    else:
        return '<p>Unable to generate map for the provided address.</p>'
