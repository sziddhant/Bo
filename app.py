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
users_locationurl = {}
user_role = {}
user_query = {}
user_team = {}
user_team['Avengers']="Avengers"
user_team['Rescue Squad']="Rescue Squad"
user_team['Squad 5']='Squad 5'
user_requirements = {}
sit_up = "all good now"
resc_details = ""
users = {}
first_aid = "https://www.cprcertified.com/blog/first-aid-and-health-safety-for-disasters"
emergency_call_data = [
    ("All in One Emergency", 112),
    ("Earth-quake Helpline service", 1092),
    ("Natural disaster control room", 1096),
    ("Police", 100),
    ("Fire", 100),
    ("Ambulance", 102),
    ("Blood Requirement", 104),
    ("Weather Enquiry", 1717),
    ("Dial a doctor", 1911),
    ("Air ambulance", 9540161344),
    ("Disaster management", 108),
    ("Emergency Relief Centre on National Highways", 1033),
    ("Hospital On Wheels", 104),
    ("Air Accident", 1071),
    ("Train Accident", 1072),
    ("Road Accident", 1073)
]
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
    z = 'I am unable to understand what you just said'
    if msgid not in user_query.keys():
        user_query[msgid] = ""
    else:
        if user_query[msgid] == "":
            if x == "Hi":
                print(user_role)
                if user_role[msgid]=="":
                    z = "Hi!\nWhat describes you> \n1. An Affected Person \n2. A Rescue Team member"
                    user_query[msgid] = "role"

                elif user_role[msgid] == "Affected":
                    z = "I can help you as follows:\n1. First-Aid Guidelines \n2. Make Emergency Calls \n3. Send requirements"
                elif user_role[msgid] == "Team":
                    z= "Hello! \n1. Requirements of affected people \n 2. Location of affected people"

            elif x =="req":
                send_message(msgid,"Requirements are:")
                for i in user_requirement:
                    send_message(msgid,i)
                z=" "

            elif x=="loc":
                for key in users_location.keys():
                    send_message(msgid,str(users_locationurl[key]))
                z=""

            elif x == "situation":
                z = sit_up
            elif x == "resdet":
                z = resc_details
                if (len(user_team)):
                    k = "There are " + str(len(user_team)) + " Teams"
                else:
                    k = "No team has registered till now."
                for key in user_team:
                    k = k + "\n" + key
                send_message(msgid, k)
            elif x == "emergency_call":
                for i in emergency_call_data:
                    send_message(msgid, str(i[0]) + " : " + str(i[1]))
                z = " "
            elif x == "first-aid":
                z = str(first_aid)
        elif user_query[msgid] == "role":
            print(inp)
            if inp.lower() == "team":
                print(inp)
                user_role[msgid] = "Team"
                user_query[msgid] = "Tname"
                z = "Enter Team name:"
            elif inp.lower() == "affected":
                print(inp)
                user_role[msgid] = "Affected"
                user_query[msgid] = "requirements"
                z = "Enter your Requirements... \n <! Type \"end\" to stop !>"
            else:
                z="What describes you> \n1. An Affected Person \n2. A Rescue Team member"


        elif user_query[msgid] == "Tname":
            user_team[inp] = msgid
            user_query[msgid] = ""
            z = "Your team name is " + inp
        elif user_query[msgid] == "requirements":
            if not x == "end":
                user_requirement.append(inp)
            z = "Any other requirement?"
            if x == "end":
                user_query[msgid] = ""
                z = "Your requirements are "
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
                        users_locationurl[recipient_id] =""

                    if message['message'].get('text'):
                        print(message)

                        response_sent_text = process(message['message']['text'], recipient_id)
                        send_message(recipient_id, response_sent_text)

                    if message['message'].get('attachments'):
                        cordi = ""
                        cordURL=""
                        try:
                            cordi = message['message']["attachments"][0]['payload']['coordinates']
                            cordiURL=message['message']["attachments"][0]['url']
                        except:
                            cordi = ""
                        if message['message']["attachments"][0]["type"]=="location":

                            response_sent_nontext="Thanks for sharing your location with the rescue team"
                        else:
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
                            users_locationurl[recipient_id] = cordiURL

                        print(users_location)

                      #  send_message(recipient_id,"Thanks for sharing your location with the rescue team")

                        send_message(recipient_id, response_sent_nontext)
    return "Message Processed"


def verify_fb_token(token_sent):
    if token_sent == VERIFY_TOKEN:
        return request.args.get("hub.challenge")
    return 'Invalid verification token'


def send_message(recipient_id, response):
    bot.send_text_message(recipient_id, response)
    return "Success"


if __name__ == '__main__':
    app.run()

