# Package installations
from datetime import datetime
import requests
from flask import Flask, redirect, request, jsonify, session
import urllib.parse
import datetime 


app = Flask(__name__)
app.secret_key = 'df3038ecd2e7433a98617c3cb55f1887123456'

CLIENT_ID = 'df3038ecd2e7433a98617c3cb55f1887'
CLIENT_SECRET = 'fb9dcaa8bdcf442ab7437332ac00dbb2'
REDIRECT_URI = 'https://my-spotify-favorites.vercel.app/callback'

AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

@app.route('/')
def index():
    return "Hey hey friends!! Welcome to my Spotify App :D I wanted to be able to look at some more of my listening data! <br> <a href='/login'>Login with Spotify</a>"

@app.route('/login')
def login():
    scope = 'user-read-private user-read-email playlist-read-private playlist-read-collaborative user-top-read'

    params = {
        'client_id': CLIENT_ID,
        'response_type': 'code',
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'show_dialog': True
    }

    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"

    return redirect(auth_url)

@app.route('/callback')
def callback():
    if 'error' in request.args:
        return jsonify({"error": request.args['error']})
    
    if 'code' in request.args:
        req_body = {
            'code': request.args['code'],
            'grant_type': 'authorization_code',
            'redirect_uri': REDIRECT_URI,
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

    response = requests.post(TOKEN_URL, data=req_body)
    token_info = response.json()

    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token']
    session['expires_at'] = datetime.datetime.now().timestamp() + token_info['expires_in']

    return redirect('/myfavorites')

@app.route('/myfavorites')
def get_myfavorites():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/top/tracks?time_range=long_term&limit=50', headers=headers)
    topsongs = response.json()

    names = ''
    count = 1

    for item in topsongs['items']:
        artists = ''
        for i in range(len(item['artists'])):
            if i == len(item['artists'])-1:
                artists += item['artists'][i]['name']
            else:
                artists += item['artists'][i]['name'] + ", "
        names += str(count) + ": " + item['name'] + " by " + artists
        names += "; Popularity score: "+ str(item['popularity'])
        names += '<br>'
        count += 1 

    medium = get_tracks_medium()
    short = get_tracks_short()

    return "Here are your top tracks and their popularity scores (calculated using number of plays/how recent plays are) using collected data over several years: <br><br>"+names+medium+short

def get_tracks_medium():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/top/tracks?time_range=medium_term&limit=50', headers=headers)
    topsongs = response.json()

    names = ''
    count = 1

    for item in topsongs['items']:
        artists = ''
        for i in range(len(item['artists'])):
            if i == len(item['artists'])-1:
                artists += item['artists'][i]['name']
            else:
                artists += item['artists'][i]['name'] + ", "
        names += str(count) + ": " + item['name'] + " by " + artists
        names += "; Popularity score: "+ str(item['popularity'])
        names += '<br>'
        count += 1 

    # return jsonify(topsongs)

    # return jsonify(playlists)
    return "<br><br>Here is the same information over the last 6 months or so: <br><br>"+names

def get_tracks_short():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/top/tracks?time_range=short_term&limit=50', headers=headers)
    topsongs = response.json()

    names = ''
    count = 1

    for item in topsongs['items']:
        artists = ''
        for i in range(len(item['artists'])):
            if i == len(item['artists'])-1:
                artists += item['artists'][i]['name']
            else:
                artists += item['artists'][i]['name'] + ", "
        names += str(count) + ": " + item['name'] + " by " + artists
        names += "; Popularity score: "+ str(item['popularity'])
        names += '<br>'
        count += 1 

    # return jsonify(topsongs)

    # return jsonify(playlists)
    return "<br><br>And again for the last 4 weeks: <br><br>"+names

@app.route('/playlists')
def get_playlists():
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/playlists', headers=headers)
    playlists = response.json()

    names = ''
    count = 1

    for item in playlists['items']:
        names += str(count) + ": " + item['name']
        names += '<br>'
        count += 1 

    # return jsonify(playlists)
    return names

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')

    if datetime.datetime.now().timestamp() > session['expires_at']:
        req_body = {
           'grant_type': 'refresh_token',
           'refresh_token': session['refresh_token'],
            'client_id': CLIENT_ID,
            'client_secret': CLIENT_SECRET
        }

    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()

    session['access_token'] = new_token_info['access_token']
    session['expires_at'] = datetime.datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/myfavorites')

# if __name__ == '__main__':
#     app.run(host='0.0.0.0', debug=True)