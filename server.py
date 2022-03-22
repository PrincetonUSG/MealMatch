from flask import Flask, request, jsonify
import profile
import os
app = Flask(__name__)

@app.route("/")
def home_view():
        return "<h1>Welcome to the MealMatch Server</h1>"
        
#Display either CAS profile login screen or 
#welcome screen based on whether user is logged
#into the application
@app.route('/getloginstatus', methods=['GET'])
def login_status():
    payload = request.json
    netid = payload["netid"]
    login_status = profile.get_loginstatus(netid)
    return jsonify({
        'status': 'OK',
        'data': {"login_status": login_status}
        })

#Display either CAS profile login screen or 
#welcome screen based on whether user is logged
#into the application
@app.route('/getprofilestatus', methods=['GET'])
def profile_status():
    payload = request.json
    netid = payload["netid"]
    profile_status = profile.get_profilestatus(netid)
    return jsonify({
        'status': 'OK',
        'data': {"profile_status": profile_status}
        })


#Create a profile for a user in MongoDB
@app.route('/createprofile', methods=['POST'])
def create_profile_main():
    payload = request.json
    netid = payload["netid"]
    name = payload["name"]
    year = payload["year"]
    major = payload["major"]
    phonenum = payload["phonenum"]
    bio = payload["bio"]

    netid_new = profile.create_profile(netid, name, year, major, phonenum, bio)
    return jsonify({
        'status': 'OK',
        'data': {"netid": netid_new}
        })



@app.route('/status', methods=["GET"])
def status():
    return jsonify({"message": "ok"})

port = int(os.environ.get('PORT', 5001))
app.run(host='0.0.0.0', port=port, debug=False )
