import datetime
import jwt
from flask import Flask, jsonify, request, make_response
from functools import wraps
import requests
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mysecretkey'

# create a mock user database with email addresses as keys
users = {
    "john@example.com": "password123",
    "test@test.com": "test123"
}


def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.cookies.get('access_token')

        if not token:
            return jsonify({'message': 'Token is missing'}), 401

        try:
            data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
            current_user = data['user']
        except:
            return jsonify({'message': 'Token is invalid'}), 401

        if current_user not in users:
            return jsonify({'message': 'User does not exist'}), 401
        
        return f(current_user, *args, **kwargs)

    return decorated


@app.route('/getData', methods=['GET'])
@token_required
def getData(current_user):
    # response = requests.get("https://www.reddit.com/r/images/new.json?limit=30")

    url = "https://www.reddit.com/r/images/new.json?limit=30"
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)

    if(response):
        data = response.json()

        # Return the data as a JSON response
        return jsonify(data), 200
    else:
        # If the request was not successful, return an error message
        return jsonify({'error': 'Unable to retrieve data'}), 500

@app.route('/isLoggedIn', methods=['GET'])
@token_required
def isLoggedIn(current_user):
    return jsonify({'message': 'user is logged in'}), 200

# login route that sends a JWT token upon successful authentication
@app.route('/login', methods=['POST'])
def login():

    try:
        data = request.json
        if not data:
            return {
                "message": "Please provide user details",
                "data": None,
                "error": "Bad request"
            }, 400
        
        email = data.get('email')
        password = data.get('password')
        if email not in users or users[email] != password:
            return jsonify({'message': 'Invalid credentials', 'WWW-Authenticate': 'Basic auth="Login required"'}), 401

        token = jwt.encode({'user': email, 'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=30)}, app.config['SECRET_KEY'])
        # return jsonify({'token': token})

        response = make_response(jsonify({'message': 'Login successful'}), 200)
        response.set_cookie('access_token', token, httponly=True)

        return response

    except Exception as e:
        return {
                "message": "Something went wrong!",
                "error": str(e),
                "data": None
        }, 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port)
