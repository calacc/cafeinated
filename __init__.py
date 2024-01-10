import pathlib
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import pyrebase
from firebase import firebase
import firebase_admin
from firebase_admin import firestore, storage, credentials
import os
from google_auth_oauthlib.flow import Flow


app = Flask(__name__, template_folder='templates')

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
firebase_admin.initialize_app(cred, {'storageBucket': 'cafeinated-ab14e.appspot.com'})
db = firestore.client()
mybucket = storage.bucket()
storage = firebase.storage()
google_client_id = '29698415898-rh7piac5kjd1nr5okk9a5cb332el91he.apps.googleusercontent.com'
client_secrets_file = os.path.join(pathlib.Path(__file__).parent, "config/client_secret.json")
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

flow = Flow.from_client_secrets_file(client_secrets_file=client_secrets_file,
                                     scopes=["https://www.googleapis.com/auth/userinfo.profile", 
                                             "https://www.googleapis.com/auth/userinfo.email", "openid"],
                                     redirect_uri=["http://127.0.0.1:1111/callback",
                                                   "https://cafeinated.onrender.com/callback"])

import gets
import actions
import pages