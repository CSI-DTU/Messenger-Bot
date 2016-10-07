import os
import sys
from flask import Flask, render_template, url_for, session, flash, request, redirect
from wtforms import Form, TextField, TextAreaField, validators, StringField, SubmitField, IntegerField
from flask_oauth import OAuth
import requests,json
app = Flask(__name__)

DEBUG = True
app = Flask(__name__)
app.config.from_object(__name__)
app.config['SECRET_KEY'] = '7d441f27d441f27567d441f2b6176a'
oauth = OAuth()

###################################################################
'''
registration-handler
Its database is REG_USERS which stores fb Ids of the users who have already registered.
'''

FACEBOOK_APP_ID = os.environ["FB_APP_ID"]
FACEBOOK_APP_SECRET = os.environ["FB_APP_SECRET"]
               
facebook = oauth.remote_app('facebook',
    base_url='https://graph.facebook.com/',
    request_token_url=None,
    access_token_url='/oauth/access_token',
    authorize_url='https://www.facebook.com/dialog/oauth',
    consumer_key=FACEBOOK_APP_ID,
    consumer_secret=FACEBOOK_APP_SECRET,
    request_token_params={'scope': 'email'}
)

msngr_id=''

class ReusableForm(Form):
    name = TextField('Name:', validators=[validators.required()], default = "guest")
    year = IntegerField('Year:', [validators.NumberRange(min=1, max=4)], default = 1)
    rollno = TextField('Roll number:',validators=[validators.required()], default = 'abcd')
    contact = IntegerField('Contact number:',[validators.NumberRange(min=1000000000,max=9999999999)], default = 1234567890)


@app.route('/login')
def login():
    return facebook.authorize(callback=url_for('facebook_authorized',
        next=request.args.get('next') or request.referrer or None,
        _external=True))


@app.route('/login/authorized')
@facebook.authorized_handler
def facebook_authorized(resp):
    global msngr_id
    if resp is None:
        return 'Access denied: reason=%s error=%s' % (
            request.args['error_reason'],
            request.args['error_description']
        )
    session['oauth_token'] = (resp['access_token'], '')
    me = facebook.get('/me')
    return redirect(url_for('registration'))


@facebook.tokengetter
def get_facebook_oauth_token():
    return session.get('oauth_token')

@app.errorhandler(400)
def forbidden_400(exception):
    return redirect(url_for('login'))
    

@app.route("/register/<m_id>/", methods=['GET'])
def register(m_id):
    global msngr_id
    msngr_id = m_id
    return redirect(url_for('login'))
    

 
@app.route("/registration", methods=['GET', 'POST'])
@facebook.authorized_handler
def registration(resp):
    global msngr_id
    '''
    if resp is None:
        return redirect(url_for('login'))
    '''
    try:
        me = facebook.get('/me')
    except:
        return redirect(url_for('login'))
        

        
    form = ReusableForm(request.form)
    
    if request.method == 'POST':
        '''check for any empty fields'''
        all_filled = [ 'empty' for value in request.form.values() if value == '']  
        
        if len(request.form.keys()) == 3 or 'empty' in all_filled:
            flash('Error: All the form fields are required.')
            return render_template('register.html', form=form)

        
        if form.validate():
            with open("REG_USERS.txt",'r') as f:
                USERS = json.load(f)

            if me.data['id'] in USERS:
                flash("Error: You have already registered!")
            else:
                flash("Thanks for registration %s!"%(request.form['name']))
                user={'fbid':me.data['id'],'m_id':msngr_id,'data':request.form}

                with open("CR_USERS.txt",'r') as f:
                    cr_users = json.load(f)
                cr_users[user['m_id']] = user['data']
                
                with open("CR_USERS.txt",'w') as f:
                    f.write(json.dumps(cr_users))
                
                USERS.append(user['fbid'])
                with open("REG_USERS.txt",'w') as f:
                    f.write(json.dumps(USERS))
        
        else:
            error_msg=''
            if form.errors.has_key('contact'):
                flash("Error: Please enter a valid contact number!")
            elif form.errors.has_key('password'):
                flash("Error: Password must be atleast 6 characters long!")
 
    return render_template('register.html', form=form,user = me)


@app.route("/logout")
@facebook.authorized_handler
def logout(resp):
    if resp is None:
        redirect(url_for('login'))
    session.clear()
    return redirect("https://www.facebook.com/dtu.csi/")

################################################################## 
'''
csi-messenger-bot-handler
Its database is CR_USERS
'''
@app.route('/', methods=['GET'])
def verify():
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFICATION_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200
    return "Hello world", 200


@app.route('/coderush', methods=['POST'])
def coderush():
    user = request.get_json()
    
    with open("CR_USERS.txt",'r') as f:
        cr_users = json.load(f)
        
    # add user to cr_users' list  
    cr_users[user['m_id']] = user['data']
    log(cr_users)
    
    with open("CR_USERS.txt",'w') as f:
        f.write(json.dumps(cr_users))    
    return "ok",200

@app.route('/users', methods=['GET'])
def CR_USERS_DATA():
    with open("CR_USERS.txt",'r') as f:
        cr_users = json.load(f)
    return str(cr_users)
    

@app.route('/', methods=['POST'])
def webook():
    data = request.get_json()
    log(data)
    
    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:
                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID

                    message_text = messaging_event["message"]["text"]


                    if message_text.startswith('/register'):
                        url = "https://coderush.herokuapp.com/register/%s"%(sender_id)
                        send_message(sender_id,"Register here:%s"%url)
                        return "ok",200
                        

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
    
    
    
