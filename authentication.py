import pyrebase

config = {
    'apiKey': 'AIzaSyDkHcb2ygZuvYI3MZ1pB2WDISC7vgAmLUE',
    'authDomain': 'cafeinated-ab14e.firebaseapp.com',
    'projectId': 'cafeinated-ab14e',
    'storageBucket': 'cafeinated-ab14e.appspot.com',
    'messagingSenderId': '29698415898',
    'appId': '1:29698415898:web:ef6e70fc421929b2a1a0a3',
    'measurementId': 'G-X7J5JBGF4L',
    'databaseURL': ''
}

firebase = pyrebase.initialize_app(config)

auth = firebase.auth()

email = 'tes2t@gmail.com'
password = '456987'

# user = auth.create_user_with_email_and_password(email, password)
# print(user)

user=auth.sign_in_with_email_and_password(email, password)
print(user)

info = auth.get_account_info(user['idToken'])
print(info)

auth.send_email_verification(user['idToken'])

auth.send_password_reset_email(email)