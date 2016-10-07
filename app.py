import os
import sys
import json
import requests
from flask import Flask, request
app = Flask(__name__)

               

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


                    if message_text.startswith('/coderush'):
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
    
    
    
