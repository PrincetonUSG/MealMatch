from operator import le
import random
import string
import notifications
import database
from datetime import datetime
from big_lists import dhall_list

from user_profile import get_from_netid
from database import new_connection, close_connection
from server import senior_year

SITE_URL = "https://mealmatch.tigerapps.org/"


def remove_match(netid, matchid, phonenum):
    sql = """ UPDATE matches
                SET active = FALSE,
                first_accepted = FALSE,
                second_accepted = FALSE
                WHERE match_id = %s"""

    cur, conn = new_connection()
    cur.execute(sql, [matchid])
    close_connection(cur, conn)

    message = "{} cancelled your match. Check "\
        "the MealMatch app for more information" \
        .format(get_from_netid(netid, 'name')[0])
    notifications.send_message(message, phonenum)


def match_requests():
    # Create queries for both lunch and dinner request matching

    dhall_str = ', '.join(["r."+dh.upper() for dh in dhall_list])
    parse_requests = """SELECT REQUESTID, r.NETID, BEGINTIME, ENDTIME, u.NAME, PHONENUM, {}, 
                                u.YEAR, u.MAJOR, u.MATCHPREF
                                FROM requests as r, users as u 
                                WHERE r.LUNCH = {} 
                                AND r.MATCHID IS NULL 
                                AND r.ACTIVE = TRUE
                                AND r.netid = u.netid
                                ORDER BY BEGINTIME ASC
                                """

    parse_requests_lunch = parse_requests.format(dhall_str, "TRUE")
    parse_requests_din = parse_requests.format(dhall_str, "FALSE")

    # Run helper method to find and insert matches into matches table
    execute_match_query(parse_requests_lunch, True)
    execute_match_query(parse_requests_din, False)


def score_match(first, second):

    # by default, a possible match has a score of 1
    score = 1
    # match pref type index is 14 (last element)

    same_match_pref = (first[14] == second[14])

    # add two points if the match preference is same, regardless of type
    if same_match_pref:

        # # Major and Year matching preferences
        if first[14] == "Major/Year":

            # add point if majors are the same
            score += 1 if first[13] == second[13] else 0

            # add point if class years are the same
            # if both class years are beyond current senior year, they are both grad students,
            # treat as matching year for matching algo, add a point
            both_grad_students = first[12] < senior_year(
            ) and second[12] < senior_year()
            score += 1 if (first[12] == second[12]
                           or both_grad_students) else 0
        # Both random matching preferences
        else:
            score += 2

    print('match score for ', first[1], second[1], 'is : ', score)
    return score


def execute_match_query(parse_requests, lunch):
    # Number of characters in id
    N = 16
    cur, conn = new_connection()
    cur.execute(parse_requests)
    rows = cur.fetchall()

    matched = []
    # iterate through requests, comparing pairs to examine match
    for i in range(len(rows)):

        poss_matches = []
        first = rows[i]  # First request

        # Do not attempt to find match if row is already matched
        if i in matched:
            continue

        for j in range(i + 1, len(rows)):
            # Do not attempt to find match if row is already matched
            if j in matched:
                continue

            second = rows[j]  # Second request

            print("Test!")
            print(first[1])
            print(second[1])

            overlap = find_overlap(first[2], first[3], second[2], second[3])

            # if there is no valid overlap between current requests
            # then skip current pairing
            if not overlap:
                print("Continue")
                continue

            # Do not match two requests originating from same user
            if first[1] == second[1]:
                print("Continue")
                continue

            # Evaluate possible dining halls for each request
            first_poss_dhalls = find_possible_dhalls(first)
            second_poss_dhalls = find_possible_dhalls(second)

            combined_dhalls = first_poss_dhalls & second_poss_dhalls
            print('combined halls: ', combined_dhalls)

            # No common dining halls between a pair of requests
            if len(combined_dhalls) == 0:
                print("Continue")
                continue

            # Assign score to current possible match and add it
            # to the current possible matches
            # index for major: 12
            # index for class year: 11

            # default score for match with time overlap is 1
            score = 1

            print('first pref', first)
            print('second pref', second)

            # match preference type is last element
            # determines if users want same type of match

            # score match based on user profiles
            score = score_match(first, second)

            # if first[11] == second[11]:
            #     score += 1
            # if first[12] == second[12]:
            #     score += 2
            poss_matches.append((j, score, combined_dhalls, overlap))

        # Continue loop if there are no possible matches
        if len(poss_matches) == 0:
            continue

        # Now execute a match

        # Sort possible matches by match score, i.e., second item in
        # the list of tuples, in descending order
        poss_matches.sort(key=lambda x: x[1], reverse=True)
        chosen_row = poss_matches[0]
        second = rows[chosen_row[0]]  # Grab requests row of chosen request

        # joining dhalls with slash
        #  dhall = '/'.join(chosen_row[2])  # Dhall(s) chosen for match
        # choose random element from list of combined dining halls
        dhall = random.choice(list(combined_dhalls))
        print('chosen loc: ', dhall)
        best_overlap = chosen_row[3]

        # Establish start and end windows for match
        start_int, end_int = best_overlap

        # Obtain matchid
        match_id = ''.join(random.choices(
            string.ascii_uppercase + string.digits, k=N))
        first_netid = first[1]
        second_netid = second[1]

        sql = "INSERT INTO matches (MATCH_ID, FIRST_NETID, SECOND_NETID, MATCH_TIME, DINING_HALL, " \
              "START_WINDOW, END_WINDOW, FIRST_ACCEPTED, SECOND_ACCEPTED, ACTIVE, LUNCH) "
        sql += "VALUES ({})".format(",".join(["%s"] * 11))

        # Current time for match made
        now = datetime.now().replace(second=0, microsecond=0)

        val = (match_id, first_netid, second_netid, now, dhall,
               start_int, end_int, False, False, True, lunch)

        cur.execute(sql, val)

        # Modify requests after match is made
        from meal_requests import modify_request
        modify_request(first[0], match_id)
        modify_request(second[0], match_id)

        message = "You matched with {} on MealMatch! Check the app for more information on your match. \n" + SITE_URL+"matches"
        notifications.send_message(message.format(first[4]), second[5])
        notifications.send_message(message.format(second[4]), first[5])

        # cache the row numbers being matched
        matched.append(i)
        matched.append(j)

    close_connection(cur, conn)


# Helper method, returns a list of selected dhalls from request
def find_possible_dhalls(row):
    # dhalls indexed starting at 6
    dhalls = row[6:6 + len(dhall_list)]
    return {dhall_list[i] for i in range(len(dhalls)) if dhalls[i]}


def get_all_matches(netid):

    # remove all expired matches
    clean_matches()

    query = """SELECT * 
            FROM matches as m, users as u
            WHERE (m.first_netid = u.netid
            OR m.second_netid = u.netid)
            AND (m.first_netid = %s OR m.second_netid = %s)
            AND (u.netid != %s)
            AND (m.active = TRUE)
            ORDER BY match_time ASC"""

    cur, conn = new_connection()
    cur.execute(query, (netid, netid, netid))
    rows = cur.fetchall()
    close_connection(cur, conn)
    print(rows)

    keys = ["match_id", "first_netid", "second_netid", "match_time", "dhall",
            "start", "end", "first_accepted", "second_accepted", "active", "lunch",
            'other_netid', 'other_name', 'other_year', 'other_major', 'other_phonenum', 'other_bio']

    all_matches_dict = [dict(zip(keys, row)) for row in rows]
    print('matches_dict: \n', all_matches_dict)

    # all_matches = [list(row) for row in rows]
    return all_matches_dict


def get_past_matches(netid):
    query = """SELECT first_netid, second_netid,
            end_window, dining_hall, match_id, lunch,
            first_accepted, second_accepted
            FROM matches
            WHERE (first_netid = %s
            OR second_netid = %s)
            AND first_accepted = TRUE
            AND second_accepted = TRUE
            ORDER BY end_window DESC"""

    cur, conn = new_connection()
    cur.execute(query, (netid, netid))
    matches = cur.fetchmany(4)
    close_connection(cur, conn)

    past_matches = []
    for match in matches:
        match_info = {}
        other_netid = match[0] if match[1] == netid else match[1]

        match_info['netid'] = other_netid
        match_info['name'], match_info['phonenum'], match_info['bio'] = get_from_netid(
            other_netid, 'name', 'phonenum', 'bio')
        match_info['day'] = match[2]
        match_info['dhall'] = match[3]
        match_info['id'] = match[4]
        match_info['meal'] = 'Lunch' if match[5] else 'Dinner'

        past_matches.append(match_info)
        print(match_info)

    return past_matches


def accept_match(netid, matchid, phonenum):
    print("ACCEPT MATCH")
    print(netid)
    query = """SELECT match_id, first_netid, second_netid, first_accepted, second_accepted FROM matches
            WHERE match_id = %s"""

    cur, conn = new_connection()
    cur.execute(query, [matchid])
    row = cur.fetchone()

    netid_type = ""
    match_name = get_from_netid(netid, 'name')[0]

    if row[1] == netid:
        # We know that the user is the first_netid
        netid_type = 'FIRST_ACCEPTED'
        if not row[4]:
            # If the other person has accepted, notify the other person that theres a match
            message = "{} accepted the match! Confirm that you'll be there on the MealMatch App!".format(
                match_name) + "\n" + SITE_URL+"matches"
        else:
            # If the other person has not accepted, notify the other person that match is confirmed
            message = "{} also accepted the match! Text your match and have fun eating!".format(
                match_name)
            # match has been finalized, update matches count
            database.update_matches_usage_metric()

    elif row[2] == netid:
        # We know that the user is the second_netid
        netid_type = 'SECOND_ACCEPTED'
        if not row[3]:
            # If the other person has accepted, notify the other person that theres a match
            message = "{} accepted the match! Confirm that you'll be there on the MealMatch App!".format(
                match_name) + "\n" + SITE_URL+"matches"
        else:
            # If the other person has not accepted, notify the other person that match is confirmed
            message = "{} also accepted the match! Text your match and have fun eating!".format(
                match_name)
            # match has been finalized, update matches count
            database.update_matches_usage_metric()
    notifications.send_message(message, phonenum)

    query = """UPDATE matches SET {} = TRUE WHERE MATCH_ID = %s""".format(
        netid_type)
    cur.execute(query, [matchid])
    close_connection(cur, conn)


# Find overlap between two datetime intervals, used in finding matches
# between two requests
# inter_1 and inter_2 are tuples of datetime object
def find_overlap(start_A, end_A, start_B, end_B):
    start_int = max(start_A, start_B)
    end_int = min(end_A, end_B)

    # There is no overlap in input intervals
    if start_int >= end_int:
        return False

    # Check if overlap is smaller than 30 minutes, not suitable for
    # adequate meal time
    # CHANGE LATER TEMPORARY
    if (end_int - start_int).total_seconds() / 60.0 < 20:
        return False

    # return the start and end of the overlap
    return (start_int, end_int)

# Clean matches table of expired matches


def clean_matches():
    sql = """SELECT *
            FROM matches"""

    cur, conn = new_connection()
    cur.execute(sql)

    rows = cur.fetchall()

    now = datetime.now()

    # list of old matches that have expired
    old_matches = [row[0] for row in rows if row[6] < now]

    sql = """ UPDATE matches
                SET active = FALSE
                WHERE match_id = %s"""

    for id in old_matches:
        cur.execute(sql, [id])

    close_connection(cur, conn)
