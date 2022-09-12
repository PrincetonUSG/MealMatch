from ast import Is
from requests import get
from database import new_connection, close_connection, update_request_usage_metric
from matcher import match_requests
from big_lists import dhall_list
from datetime import datetime, date
from sys import stdout
import random
import string


def add_request(netid, meal_type, start_time, end_time, dhall_arr, atdhall):

    print('dhall arr in add req')
    print(dhall_arr)

    # TODO: TEMP FIX to make Yeh/NCW match together
    if dhall_arr[2] or dhall_arr[5]:
        dhall_arr[2] = True
        dhall_arr[5] = True

    # TODO: TEMP FIX to make Yeh/NCW match together
    if dhall_arr[2] or dhall_arr[5]:
        dhall_arr[2] = True
        dhall_arr[5] = True

    cur, conn = new_connection()

    # confirm the user does not have an existing request for the current meal period
    if not validate_request(netid, meal_type):
        print("Cannot add request: there is already a request in the current meal period")
        return False

    sql = "INSERT INTO requests (REQUESTID, NETID,BEGINTIME,ENDTIME, LUNCH,"

    for dhall in dhall_list:
        sql += "{},".format(dhall)

    dhall_strargs = "%s, " * len(dhall_list)
    sql += "ATDHALL, ACTIVE) VALUES (%s, %s, %s, %s, %s, {}%s, %s)".format(
        dhall_strargs)

    requestId = ''.join(random.choice(
        string.ascii_letters + string.digits) for _ in range(16))

    val = [requestId, netid, start_time, end_time, meal_type]
    val += dhall_arr
    val += [atdhall, True]

    cur.execute(sql, val)
    close_connection(cur, conn)

    clean_requests()

    match_requests()

    # increment request counter
    update_request_usage_metric()

    return True

# Remove request from request table


def modify_request(request_id, match_id):
    sql = "UPDATE requests SET MATCHID = %s WHERE REQUESTID = %s"
    val = (match_id, request_id)

    cur, conn = new_connection()
    cur.execute(sql, val)
    close_connection(cur, conn)

    remove_requests([request_id])
    print("Modified request", file=stdout)


def get_all_requests(netid):
    # remove expired requests
    clean_requests()

    dhall_str = ', '.join(dhall_list)
    query = """SELECT begintime, endtime, lunch, {} ,atdhall, requestid FROM requests as r
            WHERE r.netid = %s
            AND r.active = TRUE""".format(dhall_str)

    cur, conn = new_connection()
    cur.execute(query, [netid])
    all_requests = cur.fetchall()
    close_connection(cur, conn)

    return all_requests


def validate_request(netid, meal_type):
    # search for active requests made by user with netid
    sql = """SELECT *
            FROM requests
            WHERE netid = %s AND active = TRUE AND LUNCH  = %s"""

    cur, conn = new_connection()
    cur.execute(sql, (netid, meal_type))
    rows = cur.fetchall()
    close_connection(cur, conn)

    return len(rows) == 0


def clean_requests():
    sql = """SELECT * FROM requests
             WHERE active = TRUE"""

    cur, conn = new_connection()
    cur.execute(sql)
    rows = cur.fetchall()
    close_connection(cur, conn)

    now = datetime.now()

    # list of requestids for requests that have expired
    old_requests = [row[0] for row in rows if row[3] < now]

    remove_requests(old_requests)


def remove_requests(requestids: list):
    sql = """UPDATE requests
                SET active = FALSE
                WHERE requestid = %s"""

    cur, conn = new_connection()
    for id in requestids:
        # print('request id to remove: ', id)
        cur.execute(sql, [id])
    close_connection(cur, conn)


def configure_recurring_request(netid, start_time_datetime, end_time_datetime, days, location):
    # update user's configured recurring request
    update_user_sql = ''' UPDATE users
                          SET recur = TRUE, recur_begintime = %s, recur_endtime = %s, days = %s, location = %s
                          WHERE netid = '{}' '''.format(netid)

    cur, conn = new_connection()
    cur.execute(update_user_sql, (
                start_time_datetime, end_time_datetime, days, location))
    close_connection(cur, conn)


# given info as stored in DB for recurring requests, convert information to be used in /submitrequest route
def recur_request_to_normal_request(recur_request_dict):

    normal_request_dict = {}
    normal_request_dict['netid'] = recur_request_dict['netid']
    normal_request_dict['days'] = recur_request_dict['days']
    # all recurring requests are scheduled
    normal_request_dict['at_dhall'] = False
    # convert location to dhall array
    normal_request_dict['dhall_arr'] = [
        hall_name in recur_request_dict['location'] for hall_name in dhall_list]

    print(normal_request_dict['dhall_arr'])

    begin = recur_request_dict['recur_begintime']
    end = recur_request_dict['recur_endtime']

    def _zero_pad_minute(min_num):
        if min_num < 10:
            return ('0' + str(min_num))
        else:
            return str(min_num)

    # strip day and make it current, keep hour
    normal_starttime = datetime.fromisoformat(
        date.today().isoformat() + " " + str(begin.hour) + ":" + _zero_pad_minute(begin.minute) + ":00")

    normal_endtime = datetime.fromisoformat(
        date.today().isoformat() + " " + str(end.hour) + ":" + _zero_pad_minute(end.minute) + ":00")

    print('Begin: ' + normal_starttime.isoformat())

    normal_request_dict['starttime'] = normal_starttime
    normal_request_dict['endtime'] = normal_endtime

    # assume request is already validated for lunch/brunch by getting here,
    # so include brunch hours in valid request
    if (normal_starttime.hour >= 10 and normal_starttime.hour <= 14
       and normal_endtime.hour >= 10 and normal_endtime.hour <= 14):
        # Lunch is determined by boolean
        normal_request_dict['meal_type'] = True
    elif (normal_starttime.hour >= 17 and normal_starttime.hour <= 20
          and normal_endtime.hour >= 17 and normal_endtime.hour <= 20):
        normal_request_dict['meal_type'] = False
    else:
        print('UH-OH DETERMING MEAL TYPE WENT WRONG')
        return

    return normal_request_dict


# return array of dictionaries, each dictionary contains information for a request
# filters for current day
def get_all_recurring_requests():

    now = datetime.now().replace(second=0, microsecond=0)
    ISOWEEKDAY_NUM_TO_DAY_CHAR = {1: 'M', 2: 'T',
                                  3: 'W', 4: 'R', 5: 'F', 6: 'S', 7: 'U'}

    # get enabled recurring requests scheduled on today's weekday
    sql = """ SELECT u.netid, u.recur_begintime, u.recur_endtime, u.days, u.location 
              FROM users as u WHERE (u.recur = TRUE AND  u.days LIKE '%{}%')
            """.format(str(ISOWEEKDAY_NUM_TO_DAY_CHAR[now.isoweekday()]))

    cur, conn = new_connection()
    cur.execute(sql)
    rows = cur.fetchall()
    close_connection(cur, conn)

    keys = ["netid", 'recur_begintime', 'recur_endtime', 'days', 'location']
    reqs = []
    for row in rows:
        reqs.append(dict(zip(keys, row)))

    return reqs


def execute_recurring_requests_lunch():

    print('LUNCH JOB')
    recur_reqs_dicts = get_all_recurring_requests()
    normalized_req_dicts = []
    print('made past get')
    for recur_dict in recur_reqs_dicts:
        print('going into iter')
        normal_req_dict = recur_request_to_normal_request(recur_dict)

        # if boolean lunch field is true
        if normal_req_dict['meal_type'] == True:
            normalized_req_dicts.append(normal_req_dict)
        print('made it out of iter')

    for req in normalized_req_dicts:
        success = add_request(req['netid'], req['meal_type'], req['starttime'],
                              req['endtime'], req['dhall_arr'], req['at_dhall'])
        if success:
            print('recur request for ' + req['netid'] + ' added to pool')
        else:
            print('error aah')
        print(req)


def execute_recurring_requests_dinner():

    print('DINNER JOB RUNNING')
    recur_reqs_dicts = get_all_recurring_requests()
    normalized_req_dicts = []
    print('made past get')
    for recur_dict in recur_reqs_dicts:
        print('going into iter')
        normal_req_dict = recur_request_to_normal_request(recur_dict)

        # if boolean lunch field is true
        if normal_req_dict['meal_type'] == False:
            normalized_req_dicts.append(normal_req_dict)

        print('made it out of iter')
        print(normalized_req_dicts)

    for req in normalized_req_dicts:
        success = add_request(req['netid'], req['meal_type'], req['starttime'],
                              req['endtime'], req['dhall_arr'], req['at_dhall'])
        if success:
            print('recur request for ' + req['netid'] + ' added to pool')
        else:
            print('error aah')
        print(req)


def get_users_recurring_request(netid):

    update_user_sql = ''' SELECT netid, recur, recur_begintime, recur_endtime, days, location
                        FROM users
                          WHERE netid = '{}' '''.format(netid)

    cur, conn = new_connection()
    cur.execute(update_user_sql)
    row = cur.fetchone()
    close_connection(cur, conn)

    keys = ["netid", 'recur', 'recur_begintime',
            'recur_endtime', 'days', 'location']
    req_dict = dict(zip(keys, row))
    print('testyyyy ' + str(req_dict))
    if req_dict != None and req_dict['recur'] == True:
        print('req dict')
        print('Non-null reqdict ' + str(req_dict))
        return req_dict
    else:
        print('Not valid RR ' + str(req_dict))
        return None


def recurring_meal_string_to_days(day_string):
    day_char_arr = list(day_string)
    day_char_to_full_name = {'M': "Monday", 'T': 'Tuesday', 'W': "Wednesday",
                             'R': 'Thursday', 'F': "Friday", "S": "Saturday", "U": 'Sunday'}
    days = ""
    for day_char in day_char_arr:
        days += (day_char_to_full_name[day_char]+",")

    # for one day, there will be 2 elements in the split
    if len(days.split(',')) == 2:
        return days.split(',')[0]
    # 2 days are presenr
    elif len(days.split(',')) == 3:
        sep_days = days.split(',')
        print(sep_days[0] + ' and ' + sep_days[1])
        return sep_days[0] + ' and ' + sep_days[1]
    elif len(days.split(',')) > 3:
        day_str = ""
        sep_days = days.split(',')
        for i in range(len(sep_days) - 2):
            day_str += (sep_days[i] + ", ")
            print(day_str)
        day_str += " and " + sep_days[len(sep_days) - 2]
        print(day_str)
        return day_str


def cancel_recurring_request(netid):
    update_user_sql = ''' UPDATE users
                          SET recur = FALSE, recur_begintime = NULL, recur_endtime = NULL, days = NULL, location = NULL
                          WHERE netid = '{}' '''.format(netid)
    cur, conn = new_connection()
    cur.execute(update_user_sql)
    print('the update cancel rr has executed')
    close_connection(cur, conn)


def get_current_weekday_char():
    now = datetime.now().replace(second=0, microsecond=0)
    ISOWEEKDAY_NUM_TO_DAY_CHAR = {1: 'M', 2: 'T',
                                  3: 'W', 4: 'R', 5: 'F', 6: 'S', 7: 'U'}
    return ISOWEEKDAY_NUM_TO_DAY_CHAR[now.isoweekday()]


def recur_request_to_string(recur_req_dict):
    if recur_req_dict == None:
        return None
    else:
        # change to normal req for easier field access
        req = recur_request_to_normal_request(recur_req_dict)
        if req['meal_type']:
            meal = 'Lunch'
        else:
            meal = 'Dinner'

        dhalls_in_req = [dhall_list[i]
                         for i in range(len(dhall_list)) if req['dhall_arr'][i]]
        # append dining halls into a string split by /
        loc = '/'.join(dhalls_in_req)
        day_string = recurring_meal_string_to_days(req['days'])

        ret_string = meal + ' @ ' + loc + " from " + \
            req['starttime'].strftime('%-I:%M%p') + "-" + req['endtime'].strftime('%-I:%M%p') \
            + ', on ' + day_string

        return ret_string
