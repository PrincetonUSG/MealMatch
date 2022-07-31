##
from nis import match
from sys import stdout, stderr
from datetime import date, datetime, tzinfo
from argparse import ArgumentParser
import os
from urllib import response

from dateutil import parser
from apscheduler.schedulers.background import BackgroundScheduler
from flask import Flask, request, session
from flask import render_template, make_response, redirect, url_for
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from flask_talisman import Talisman


import user_profile
import meal_requests
import matcher
import auth
import keys
import req_validation
from big_lists import majors, dept_code, dhall_list

app = Flask(__name__)
app.secret_key = keys.APP_SECRET_KEY


@app.route('/landing', methods=['GET'])
def landing_page():
    html = render_template('landing.html',
                           landing=True)
    response = make_response(html)
    return response


@app.route('/', methods=['GET'])
def home_page():
    if session.get('username'):
        html = render_template('homescreen.html')
        response = make_response(html)
        return response
    else:
        return redirect('/landing')


@app.route('/next', methods=['GET'])
def go_to_cas():
    auth.authenticate()
    return redirect(url_for('homescreen'))


@app.route('/index', methods=['GET'])
def homescreen():
    if not session.get('username'):
        return redirect('/landing')  # go to landing page
    if not user_profile.exists(session.get('username')):
        # return redirect('/create_account')
        # go to create account page, pass flag for having valid phone number
        return redirect(url_for('.update_account_form', valid_phonenum='1'))
    html = render_template('homescreen.html')
    response = make_response(html)
    return response

# ABOUT PAGE


@app.route('/about', methods=['GET'])
def about_method():
    logged_out = session.get('username') == None
    html = render_template('about.html',
                           logged_out=logged_out,
                           landing=False)
    response = make_response(html)
    return response

# get what the senior class's year is right now


def senior_year():
    td = date.today()
    return td.year if td.month < 6 else td.year+1

##########

# establish the route for creating/editing your account


@app.route('/edit_account', methods=['GET'])
@app.route('/create_account', methods=['GET'])
def update_account_form():

    username = auth.authenticate()

    profile_dict = user_profile.get_profile(username)

    valid_phonenum = request.args.get('valid_phonenum')

    if valid_phonenum == '1':
        valid_phonenum = True
    elif valid_phonenum == '0':
        valid_phonenum = False
    else:  # protect against malicious manually entering parameter to different than 0 or 1
        return make_response(render_template('page404.html'), 404)

    title_value = ""
    button_value = ""
    new_user = not user_profile.exists(username)

    # netid detected in system
    if not new_user:
        title_value = 'Edit Your Profile!'
        button_value = "Submit Changes"
    else:
        title_value = 'Create Your Account!'
        button_value = "Get Started!"

    html = render_template('editprofile.html',
                           senior_class=senior_year(),
                           majors=majors,
                           existing_profile_info=profile_dict,
                           title_value=title_value,
                           button_value=button_value,
                           valid_phonenum=valid_phonenum,
                           new_user=new_user)
    response = make_response(html)
    return response

# HOMESCREEN --- SUBMIT PROFILE FORM


@app.route('/submit_profile_form', methods=["GET"])
def form():
    name = request.args.get('name').strip()
    netid = auth.authenticate()
    year = request.args.get('year')
    major = request.args.get('major')
    bio = request.args.get('bio').strip()
    phonenum = request.args.get('phonenum')
    match_pref = request.args.get('match-pref')
    yeardict = {}
    for i in range(4):
        y = str(senior_year()+i)
        yeardict[y] = 'class of '+str(y)
    if year == "Grad Student":
        y = str(senior_year()-1)
        yeardict[y] = year
        year = y
    if bio == "":
        bio = "Hey, my name is %s. Let's grab a meal sometime!" % name
    if user_profile.exists(netid):
        if(user_profile.validate_phonenum(phonenum)):
            print('Phone number validated')
            user_profile.edit_profile(
                netid, name, int(year), major, phonenum, bio, match_pref)
        else:
            return redirect(url_for('update_account_form', valid_phonenum='0'))
    else:
        if(user_profile.validate_phonenum(phonenum)):
            user_profile.create_profile(
                netid, name, int(year), major, phonenum, bio, match_pref)
        else:
            return redirect(url_for('update_account_form', valid_phonenum='0'))

    return redirect('/index')


# TEST ROUTE --- FORCE MATCHES
@app.route('/forcematches', methods=['GET'])
def force_matches():
    matcher.match_requests()
    return redirect("/matches")


# SUBMIT REQUEST
@app.route('/submitrequest', methods=['GET'])
def submit_request():
    print('match has been made', file=stdout)

    # parse request arguments, throw exception if not parseable
    try:
        meal_type = request.args.get('meal')
        print('Meal type', meal_type, file=stdout)
        dhall = request.args.get('location')
        print('DHALL STRING:', dhall, file=stdout)
        start_time = request.args.get('start')
        end_time = request.args.get('end')
        at_dhall = request.args.get('atdhall')
    except Exception as ex:
        return make_response(render_template('page404.html'), 404)

    print(request.args, file=stdout)

    # validate back end submission of requests to ensure
    # direct URL submission of invalid request cannot occurr
    if not validate_req(request.args):
        print('request deemed invalid')

        if at_dhall == "True":
            return redirect('/ondemand?error=invalid_request')
        else:
            return redirect('/schedule?error=invalid_request')

    meal_type = (meal_type == "lunch")
    at_dhall = (at_dhall == "True")

    # multiple dhalls can be selected via scheduled match
    # Dining halls are listed in between '-' of dhall request parameter

    dhall_arr = [hall_name in dhall for hall_name in dhall_list]
    print('dhall_arr: ', dhall_arr, file=stdout)

    if start_time == "now":
        start_time_datetime = datetime.now()
    else:
        start_time_datetime = parser.parse(start_time)

    end_time_datetime = parser.parse(end_time)

    success = meal_requests.add_request(auth.authenticate(), meal_type,
                                        start_time_datetime, end_time_datetime, dhall_arr, at_dhall)

    if success:
        print('request submitted', file=stdout)
        return redirect("/matches")
    else:
        return redirect("/schedule?error=multiplerequests")


def validate_req(args):
    # We have to run the same validation we did in html
    # for if the user submits via the address link:(
    print('request validation running', file=stdout)
    print('args in validate_req', args, file=stdout)
    try:
        meal_type = args.get('meal')
        print('Meal type', meal_type, file=stdout)
        dhall = args.get('location')
        print('DHALL STRING:', dhall, file=stdout)
        start_time = args.get('start')
        end_time = args.get('end')
        at_dhall = args.get('atdhall')
        print('req type: ', at_dhall, file=stdout)
        if at_dhall == "False":
            at_dhall = False
        if at_dhall == "True":
            at_dhall = True
    except Exception as ex:
        print('exception in validate_req', file=stdout)
        return make_response(render_template('page404.html'), 404)

    if not at_dhall:
        print('req to validate is scheduled')
        return req_validation.validate_scheduled_req(args)
    else:
        print('req to validate is on demand')
        return req_validation.validate_ondemand_req(args)


# HOMESCREEN -> SCHEDULE MATCH PAGE
@app.route('/schedule', methods=['GET'])
def schedulematch():
    error = request.args.get('error')

    if error is None:
        error = ""

    now = datetime.now()
    html = render_template('scheduledmatch.html',
                           dhalls=dhall_list,
                           error=error,
                           date=now)
    response = make_response(html)
    return response

# HOMESCREEN -> ON DEMAND MATCH PAGE


@app.route('/ondemand', methods=['GET'])
def ondemand():
    error = request.args.get('error')

    if error is None:
        error = ""
    now = datetime.now()
    match_pref = user_profile.get_from_netid(
        auth.authenticate(), 'matchpref')[0]
    html = render_template('ondemandmatch.html',
                           dhalls=dhall_list,
                           error=error,
                           date=now,
                           match_pref=match_pref)
    response = make_response(html)
    return response

# HOMESCREEN -> MATCHES PAGE


@app.route('/matches', methods=['GET'])
def get_matches():

    netid = auth.authenticate()
    all_matches = matcher.get_all_matches(netid)
    all_requests = meal_requests.get_all_requests(netid)

    for i in range(len(all_matches)):
        match = all_matches[i]
        print('match row:', match, file=stderr)

        you_accepted = False
        opponent_accepted = True

        if netid == match['first_netid']:
            you_accepted = match['first_accepted']
            opponent_accepted = match['second_accepted']
        elif netid == match['second_netid']:
            you_accepted = match['second_accepted']
            opponent_accepted = match['first_accepted']

        if match['other_year'] <= senior_year()-1:
            all_matches[i]['other_year'] = "Grad Student"

        if you_accepted and opponent_accepted:
            all_matches[i]['first_accepted'] = "Both Accepted!"
        elif you_accepted and not opponent_accepted:
            all_matches[i]['first_accepted'] = "You Accepted"
        else:
            all_matches[i]['first_accepted'] = ""

        print('dhall', all_matches[i]['dhall'])

    req_locations = []
    for req in all_requests:
        # get lists of booleans from database
        dhalls_bools_in_req = req[3:3+len(dhall_list)]
        # get which dining halls have true values
        dhalls_in_req = [dhall_list[i]
                         for i in range(len(dhall_list)) if dhalls_bools_in_req[i]]
        # append dining halls into a string split by /
        loc = '/'.join(dhalls_in_req)
        print('REQ: ', req, "\n Loc: ", loc)
        req_locations.append(loc)

    html = render_template('matches.html',
                           all_matches=all_matches,
                           all_requests=all_requests,
                           locations=req_locations)
    response = make_response(html)
    return response

# HOMESCREEN -> HISTORY PAGE


@app.route('/history', methods=['GET'])
def past_matches():
    netid = auth.authenticate()
    past_matches = matcher.get_past_matches(netid)

    if len(past_matches) == 0:
        html = render_template('nopastmatches.html')
    else:
        html = render_template('history.html',
                               past_matches=past_matches)
    response = make_response(html)
    return response

# REMOVE REQUEST ON REQUESTS PAGE


@app.route('/removerequest', methods=['POST'])
def remove_request():
    requestid = [request.args.get("requestid")]
    print('request id to remove: ', requestid)
    meal_requests.remove_requests(requestid)
    return redirect(url_for('get_matches'))

# ACCEPT MATCH ON MATCHES PAGE


@app.route('/acceptmatch', methods=['POST'])
def accept_match():
    matchid = request.args.get("matchid")
    phonenum = request.args.get("phonenum")

    matcher.accept_match(auth.authenticate(), matchid, phonenum)
    return redirect(url_for('get_matches'))

# CANCEL MATCH ON MATCHES PAGE


@app.route('/cancelmatch', methods=['POST'])
def remove_matches():
    matchid = request.args.get("matchid")
    phonenum = request.args.get("phonenum")

    matcher.remove_match(auth.authenticate(), matchid, phonenum)
    return redirect('/matches')


@app.route('/tutorial', methods=['GET'])
def tutorial_method():
    logged_out = session.get('username') == None
    html = render_template('tutorial.html',
                           logged_out=logged_out)
    response = make_response(html)
    return response

# CAS LOGOUT


@app.route('/logout', methods=['GET'])
def logout():
    auth.logout()


# ERROR HANDLING
@app.route('/test404', methods=['GET'])
def test404(e):
    return render_template('page404.html')


@app.errorhandler(404)
def error404(e):
    return render_template('page404.html'), 404


@app.errorhandler(500)
def error500(e):
    return render_template('page500.html'), 500


# import modules to all Jinja templates
@app.context_processor
def add_imports():
    return dict(user_profile=user_profile, datetime=datetime, os=os, auth=auth)


if __name__ == "__main__":
    arg_parser = ArgumentParser(allow_abbrev=False,
                                description="Web Server")
    arg_parser.add_argument(
        "host",
        type=str,
        nargs='?',
        metavar="host",
        default="localhost",
        help="the ip address the server is running on",
    )
    args = arg_parser.parse_args()
    host = args.host
    print('host: ', args.host, file=stdout)

    try:
        scheduler = BackgroundScheduler()
        job = scheduler.add_job(
            meal_requests.clean_requests, 'interval', hours=5)
        scheduler.start()

        # redirect to HTTPS when on heroku, don't use security protocol on localhost
        if host != 'localhost':
            talisman = Talisman(app, content_security_policy=None)
            print('talisman security', file=stdout)
        else:
            print('running local host, no talisman security', file=stdout)

        port = int(os.environ.get('PORT', 5001))
        app.run(host=host, port=port, debug=False)
    except Exception as ex:
        print(ex, file=stderr)
        exit(1)
