import os
import sys
import json

import requests
from flask import Flask, request
from watson_developer_cloud import ConversationV1, ToneAnalyzerV3


app = Flask(__name__)

conversation = ConversationV1(
  username='cc57b219-35e4-4e13-befc-1adfd097fb9b',
  password='ZlNUp7YY2KmG',
  version='2017-04-21'
)

tone_analyzer = ToneAnalyzerV3(
   username='018a73a6-40a0-4d83-a0c7-299f22225e45',
   password='hUkLMvnom8tl',
   version='2016-05-19'
)

workspace_id = '0e84fef1-e33a-4b04-913d-121f2064205a'

@app.route('/', methods=['GET'])
def verify():
    # when the endpoint is registered as a webhook, it must echo back
    # the 'hub.challenge' value it receives in the query arguments
    if request.args.get("hub.mode") == "subscribe" and request.args.get("hub.challenge"):
        if not request.args.get("hub.verify_token") == os.environ["VERIFY_TOKEN"]:
            return "Verification token mismatch", 403
        return request.args["hub.challenge"], 200

    return "Hello world", 200


@app.route('/', methods=['POST'])
def webhook():

    # endpoint for processing incoming messaging events
    data = request.get_json()
    log(data)  # you may not want to log every incoming message in production, but it's good for testing

    if data["object"] == "page":

        for entry in data["entry"]:
            for messaging_event in entry["messaging"]:

                if messaging_event.get("message"):  # someone sent us a message

                    sender_id = messaging_event["sender"]["id"]        # the facebook ID of the person sending you the message
                    recipient_id = messaging_event["recipient"]["id"]  # the recipient's ID, which should be your page's facebook ID
                    message_text = messaging_event["message"]["text"]  # the message's text

                    anger = int()
                    disgust = int()
                    fear = int()
                    joy = int()
                    sad = int()
                    if('/reaction' in message_text.split(' ')):
                        message = message_text[10:]
                        tone = tone_analyzer.tone(text=message)

                        for d in tone['document_tone']['tone_categories'][0]['tones']:
                            print(d)
                            if(d['tone_name'] == "Anger"):
                                anger = d['score']
                            elif(d['tone_name'] == "Disgust"):
                                disgust = d['score']
                            elif(d['tone_name'] == "Fear"):
                                fear = d['score']
                            elif(d['tone_name'] == "Joy"):
                                joy = d['score']
                            elif(d['tone_name'] == "Sadness"):
                                sad = d['score']
                        # Check Highest score and send message
                        if(fear >= disgust and fear >= anger and fear >=joy and fear >= sad):
                            send_message(sender_id,':o')
                        elif(anger >= disgust and anger >= fear and anger >=joy and anger >= sad):
                            send_message(sender_id,'>:(')
                        elif(disgust >= anger and disgust >= fear and disgust >=joy and disgust >= sad):
                            send_message(sender_id,'-_-')
                        elif(joy >= disgust and joy >= anger and joy >= fear and joy >= sad):
                            send_message(sender_id,':D')
                        elif(sad >= disgust and sad >= anger and sad >=joy and sad >= fear):
                            send_message(sender_id, ':(')

                        send_message(sender_id, "Contextual analysis done")
                    else:

                        global context
                        # Get response from ibm watson service
                        response = conversation.message(
                                        workspace_id=workspace_id,
                                        message_input={'text': message_text},
                                        context=context
                                        )
                        context = response['context']
                        message_response = str(response['output']['text'][0])
                        send_message(sender_id, message_response)

                if messaging_event.get("delivery"):  # delivery confirmation
                    pass

                if messaging_event.get("optin"):  # optin confirmation
                    send_message(sender_id, "Thanks for trying this bot. Say hi to continue!")

                if messaging_event.get("postback"):  # user clicked/tapped "postback" button in earlier message
                    pass

    return "ok", 200


def send_message(recipient_id, message_text):

    log("sending message to {recipient}: {text}".format(recipient=recipient_id, text=message_text))

    params = {
        "access_token": os.environ["PAGE_ACCESS_TOKEN"]
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


def log(message):  # simple wrapper for logging to stdout on heroku
    print(str(message))
    sys.stdout.flush()


if __name__ == '__main__':
    print("Running app")
    app.run(debug=True)
