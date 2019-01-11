from flask import Flask, request
import mysql.connector
from mysql.connector import errorcode

from pymessenger.bot import Bot
from old import *
from data import *
from luis import *


config = {
    'host': '',
    'user': '',
    'password': '',
    'database': ''
}

app = Flask(__name__)
bot = Bot(ACCESS_TOKEN)
users_location = {}
user_role = {}
user_query = {}
user_team = {}
user_requirements = {}
sit_up = "all good now"
resc_details = "The teams are on the way"
users = {}
first_aid = "Call Alis"
emergency_call_data = "Just Dial :- +918888888888"
user_requirement = []

try:
    conn = mysql.connector.connect(**config)
    print("Connection established")
except mysql.connector.Error as err:
    if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
        print("Something is wrong with the user name or password")
    elif err.errno == errorcode.ER_BAD_DB_ERROR:
        print("Database does not exist")
    else:
        print(err)
else:
    cursor = conn.cursor()
    # Drop previous table of same name if one exists
    cursor.execute("DROP TABLE IF EXISTS user;")
    print("Finished dropping table (if existed).")

# Create table

cursor.execute(
    "CREATE TABLE user (id serial PRIMARY KEY, recipient_id VARCHAR(50),role VARCHAR(15),loc_lat VARCHAR(50),loc_long VARCHAR(50),requirements VARCHAR(100),Tname VARCHAR(100));")
print("Finished creating table.")


def db_update():

    # Insert some data into table

    for user in user_query.keys():
        print("1")

        cursor.execute(
            "INSERT INTO user (recipient_id, role,loc_lat,loc_long,requirements) VALUES (%s, %s, %s, %s, %s);",
            (user, user_role[user], users_location[user]["lat"], users_location[user]["long"], str(user_requirement)))
        print("Inserted", cursor.rowcount, "row(s) of data.")

    # Cleanup
    conn.commit()
    cursor.close()
    conn.close()
    print("Done.")


def process(x, msgid):
    inp = x
    x = msg_luis(x)
    z = 'idk'
    if msgid not in user_query.keys():
        user_query[msgid] = ""
    else:
        if user_query[msgid] == "":
            if x == "Hi":

                print(user_role)
                if user_role[msgid]=="":
                    z = "Hi!\nAre you a affected person or from a rescue team"
                    user_query[msgid] = "role"

                elif user_role[msgid] == "Affected":
                    z = "I can help you as follows\nEmergency\nSend requirements\nSituation Updates\nFirst-Aid Guidelines"
                    z = z + "\nMake Emergency Calls"
                    print("GG Pant")

            elif x == "situation":
                z = sit_up
            elif x == "resdet":
                z = resc_details

                k = "there are " + str(len(user_team)) + " Teams"
                for key in user_team:
                    k = k + "\n" + key
                send_message(msgid, k)
            elif x == "emergency_call":
                z = emergency_call_data
            elif x == "first-aid":
                z = first_aid
        elif user_query[msgid] == "role":
            print("1")
            print(inp)
            if inp.lower() == "team":
                print(inp)
                print("TEam if")
                user_role[msgid] = "Team"
                user_query[msgid] = "Tname"
                z = "Enter Team name"
            elif inp.lower() == "affected":
                print(inp)
                user_role[msgid] = "Affected"
                user_query[msgid] = "requirements"
                z = "Enter your Requirements\n type end to stop"

        elif user_query[msgid] == "Tname":
            user_team[inp] = msgid
            user_query[msgid] = ""
            z = "Your team name is " + inp
        elif user_query[msgid] == "requirements":
            if not inp.lower() == "end":
                user_requirement.append(inp)
            z = "ok, and?"
            if inp == "end":
                user_query[msgid] = ""
                z = "Requirements are "
                send_message(msgid, z)
                for i in user_requirement:
                    send_message(msgid, i)
                z = "..."

    return z


@app.route('/', methods=['GET', 'POST'])
def recieve_message():
    if request.method == 'GET':
        token_sent = request.args.get("hub.verify_token")
        return verify_fb_token(token_sent)
    else:
        output = request.get_json()
        for event in output['entry']:
            messaging = event['messaging']
            for message in messaging:
                if message.get('message'):

                    recipient_id = message['sender']['id']
                    if recipient_id not in user_query.keys():
                        user_query[recipient_id] = ""
                        user_requirements[recipient_id] = ""
                        user_role[recipient_id] = ""
                        users_location[recipient_id] = {'lat':'','long':''}

                    if message['message'].get('text'):
                        print(message)

                        response_sent_text = process(message['message']['text'], recipient_id)
                        send_message(recipient_id, response_sent_text)

                    if message['message'].get('attachments'):
                        cordi = ""
                        try:

                            cordi = message['message']["attachments"][0]['payload']['coordinates']

                        except:
                            cordi = ""

                        response_sent_nontext = get_message("")

                        try:
                            db_update()
                        except:
                            print("DB update fail")
                        print("\n")
                        print(message['message'])
                        print("\n")
                        print(cordi)

                        if not cordi == "":
                            users_location[recipient_id] = cordi
                        print(users_location)

                        send_message(recipient_id, response_sent_nontext)
    return "Message Processed"


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def send_message(recipient_id, response):
    bot.send_text_message(recipient_id, response)
    return "success"


if __name__ == '__main__':
    app.run()

