import os
import sys
from flask import Flask, render_template, url_for, session, flash, request, redirect
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, IntegerField
# from pymongo import MongoClient
from firebase import firebase
import requests,json
app = Flask(__name__)

DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'
MONGODB_URI = os.environ.get('MONGODB_URI')
client = MongoClient(MONGODB_URI, connectTimeoutMS=30000, socketTimeoutMS=None, socketKeepAlive=True)
db = client.get_default_database()
coderush_users = db.coderush_users
firebase = firebase.FirebaseApplication('https://csidtubot.firebaseio.com/')
###################################################################
REG_HERE = "Register here:https://csidtubot.herokuapp.com/register?id=%s"
NOT_REG = "Sorry you have not registered yet. Type /register to generate registration link. :)"
GEN_INFO = "Welcome to online prelims round of CODERUSH! bla bla bla"

###################################################################
'''
registration-handler
'''

class ReusableForm(Form):
    name = TextField('Name:', validators=[validators.required()], default = "guest")
    year = IntegerField('Year:', [validators.NumberRange(min=1, max=4)], default = 1)
    rollno = TextField('Roll number:',validators=[validators.required()], default = 'abcd')
    contact = IntegerField('Contact number:',[validators.NumberRange(min=1000000000,max=9999999999)], default = 1234567890)

 
@app.route("/register", methods=['GET', 'POST'])
def registration():
    user_id = request.args.get('id')
    
    form = ReusableForm(request.form)
    
    if request.method == 'POST':
        '''check for any empty fields'''
        all_filled = [ 'empty' for value in request.form.values() if value == '']  
        
        if len(request.form.keys()) == 3 or 'empty' in all_filled:
            flash('Error: All the form fields are required.')
            return render_template('register.html', form=form)

        
        if form.validate():
            
            USERS = loadDB()

            if USERS.has_key(user_id):
                flash("Error: You have already registered!")
            else:
                flash("Thanks for registration %s!"%(request.form['name']))
                USERS[user_id] = request.form
                pushDB(USERS)
                
        else:
            error_msg=''
            if form.errors.has_key('contact'):
                flash("Error: Please enter a valid contact number!")
            elif form.errors.has_key('password'):
                flash("Error: Password must be atleast 6 characters long!")
 
    return render_template('register.html', form=form)


@app.route("/logout")
def logout():
    return redirect("https://www.facebook.com/dtu.csi/")

################################################################## 
'''
csi-messenger-bot-handler
[
    {
        "subscriber_id": ..........,
        "contact": ............,
        "year": ............,
        "rollno": ...........,
        "name": ...........,
    },
    {
        "subscriber_id": ..........,
        "contact": ............,
        "year": ............,
        "rollno": ...........,
        "name": ...........,
    },
    {
        "subscriber_id": ..........,
        "contact": ............,
        "year": ............,
        "rollno": ...........,
        "name": ...........,
    }
]
'''

def loadDB():
    users = coderush_users.find()
    return users

def pushDB(users):
    for user in users:
        coderush_users.insert_one({
            "subscriber_id": user['subscriber_id'],
            "contact": user['contact'],
            "year": user['year'],
            "rollno": user['rollno'],
            "name": user['name']
        })


@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFICATION_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200


@app.route('/users', methods=['GET'])
def USERS_DATA():   
    return str(loadDB())
    

@app.route('/', methods=['POST'])
def webook():
    data = request.get_json()
    log(data)

    USERS = loadDB()
    
    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = ''
                    try:    
                        message_text = messaging_event["message"]["text"]  # the message's text
                    except:
                        print "Message Text absent"

                    if(message_text[0] == '@' or len(message_text) == 0):
                        return "ok", 200
                    # send_message(sender_id, message_text)
            
                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    pass

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass
                try:
                    message_text = messaging_event["message"]["text"]
                except:
                    return "ok",200

                if message_text.startswith('/register'):
                    send_message(sender_id,REG_HERE%sender_id)
                    return "ok",200
                
                elif message_text.startswith('/coderush'):
                    if USERS.has_key(sender_id):
                        send_message(sender_id,GEN_INFO)
                    else:
                        send_message(sender_id,NOT_REGISTERED)
                        
                        
                        
    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token":  os.environ["PAGE_ACCESS_TOKEN"]
    }
    headers = {
        "Content-Type": "application/json"
    }
    data = json.dumps({
        "recipient": {
            "id": recipient_id
        },
        "message": {
            "text": message_text
        }
    })
    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)


    
    

def send_image(recipient_id,image):
    log("sending image to {recipient}:".format(recipient=recipient_id))

    params = {
        "access_token":  os.environ["PAGE_ACCESS_TOKEN"]
        }
    headers = {
        "Content-Type": "application/json"
    }

    data = json.dumps({
            "recipient": {
                "id": recipient_id
                },
            "message": {
                "attachment":{
                    "type":"image",
                    "payload":{
                        "url":image
                        }
                    }
                }
            })

    r = requests.post("https://graph.facebook.com/v2.6/me/messages", params=params, headers=headers, data=data)
    if r.status_code != 200:
        log(r.status_code)
        log(r.text)

    

def log(message):  # simple wrapper for logging to stdout on heroku
    print str(message)
    sys.stdout.flush()


if __name__ == '__main__':
    app.run(debug=True)