from os import environ
from twilio.rest import Client
import vobject
from user_profile import get_from_netid
import meal_requests
from database import new_connection, close_connection


def generate_virtual_card(netid):
    name, phone_num = get_from_netid(netid, "name", "phonenum")

    phone_num = '+1'+phone_num
    first_name, last_name = name.split()

    vCard = vobject.vCard()
    vCard.add('N').value = vobject.vcard.Name(
        family=last_name, given=first_name)
    vCard.add('FN').value = name

    vCard.add('TEL')
    vCard.tel.value = phone_num
    vCard.tel.type_param = 'MOBILE'


def send_message(message, phonenumber):
    account_sid = environ['TWILIO_ACCOUNT_SID']
    auth_token = environ['TWILIO_AUTH_TOKEN']
    client = Client(account_sid, auth_token)

    print(message)
    print(phonenumber)

    message = client.messages \
        .create(
            body=message,
            from_='+1' + environ['TWILIO_NUMBER'],
            to='{}'.format(phonenumber)
        )


def send_recurring_request_notifications_lunch():
    print('sending recur request notifications')
    recur_reqs_dicts = meal_requests.get_all_recurring_requests()
    netids = []
    for rr in recur_reqs_dicts:
        normal_req = meal_requests.recur_request_to_normal_request(rr)
        if normal_req['meal_type'] == True:
            netids.append(rr['netid'])

    get_users_phone_numbers_sql_string = \
        ''' SELECT u.phonenum FROM users as u WHERE u.netid IN ({})'''
    netid_string_reps = []

    for netid in netids:
        netid_string_reps.append('\'{}\''.format(netid))

    netid_vals = ','.join(netid_string_reps)
    print(netid_vals)

    sql = get_users_phone_numbers_sql_string.format(netid_vals)
    print(sql)

    cur, conn = new_connection()
    cur.execute(sql)
    rows = cur.fetchall()
    close_connection(cur, conn)

    print(rows)

    recur_req_message = '''MealMatch: Your recurring lunch request for today is about to be submitted. Check the status on the app at {}'''.format(
        'mealmatch.tigerapps.org/matches')

    for row in rows:
        phonenum = row[0]
        print(row[0])
        send_message(recur_req_message, phonenum)
        print('should have sent message')


def send_recurring_request_notifications_dinner():
    print('sending recur request notifications')
    recur_reqs_dicts = meal_requests.get_all_recurring_requests()
    netids = []
    for rr in recur_reqs_dicts:
        normal_req = meal_requests.recur_request_to_normal_request(rr)
        if normal_req['meal_type'] == False:
            netids.append(rr['netid'])

    get_users_phone_numbers_sql_string = \
        ''' SELECT u.phonenum FROM users as u WHERE u.netid IN ({})'''
    netid_string_reps = []

    for netid in netids:
        netid_string_reps.append('\'{}\''.format(netid))

    netid_vals = ','.join(netid_string_reps)
    print(netid_vals)

    sql = get_users_phone_numbers_sql_string.format(netid_vals)
    print(sql)

    cur, conn = new_connection()
    cur.execute(sql)
    rows = cur.fetchall()
    close_connection(cur, conn)

    print(rows)

    recur_req_message = '''MealMatch: Your recurring dinner request for today is about to be submitted. Check the status on the app at {}'''.format(
        'mealmatch.tigerapps.org/matches')

    for row in rows:
        phonenum = row[0]
        print(row[0])
        send_message(recur_req_message, phonenum)
        print('should have sent message')
