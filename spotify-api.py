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

    return redirect('/favorites_overview')

@app.route('/favorites_overview')
def get_overall_favorites():
    welcome_string = "Here are your 10 top tracks and artists and their popularity scores (calculated using number of plays/how recent plays are) using collected data over several years: <br><br>"
    current_page = 'overview'
    return get_data_for_time('long_term', welcome_string, current_page, 10)


@app.route('/myfavorites_longterm')
def get_myfavorites():
    welcome_string = "Here are your top tracks and their popularity scores (calculated using number of plays/how recent plays are) using collected data over several years: <br><br>"
    current_page = 'long'
    return get_data_for_time('long_term', welcome_string, current_page, 50)


@app.route('/myfavorites_mediumterm')
def get_tracks_medium():
    welcome_string = "Here are your top tracks and their popularity scores (calculated using number of plays/how recent plays are) using collected data over several years: <br><br>"
    current_page = 'medium'
    return get_data_for_time('medium_term', welcome_string, current_page, 50)
   

@app.route('/myfavorites_shortterm')
def get_tracks_short():
    welcome_string = "Here are your top tracks and their popularity scores (calculated using number of plays/how recent plays are) using collected data over 4 weeks or so: <br><br>"
    current_page = 'short'
    return get_data_for_time('short_term', welcome_string, current_page, 50)


def get_data_for_time(time_period, welcome_string, current_page, count):
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    songsresponse = requests.get(API_BASE_URL + 'me/top/tracks?time_range='+time_period+'&limit='+str(count), headers=headers)
    artistsresponse = requests.get(API_BASE_URL + 'me/top/artists?time_range='+time_period+'&limit='+str(count), headers=headers)
    topsongs = songsresponse.json()
    topartists = artistsresponse.json()

    people = ''
    names = ''
    count = 1
    counter = 1
    genres = {}

    for item in topartists['items']:
        people += str(counter) + ": " + item['name']
        people += "; Popularity score: "+ str(item['popularity'])
        people += '<br>'
        counter += 1
        artist_info = get_artist_info(item['name'], item['id'])
        for genre in artist_info['genres']:
            if genre in genres.keys():
                genres[genre] += 1
            else:
                genres[genre] = 1

    genre_count = 0
    genre_information = '<br><br>Your top genres were:<br>'
    for key in dict(sorted(genres.items(), key=lambda item: item[1], reverse=True)).keys():
        genre_count += 1
        genre_information += str(genre_count)+') '+key+', showing up '+str(genres[key])+' times<br>'

    for item in topsongs['items']:
        if count == 1:
            top_song = item['id']
            top_name = item['name']
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

    top_features = get_track_audio_features(top_name, top_song)
    top_info = "Your favorite song, "+top_features['name']+', was in '+top_features['overall_key']+"."

    artist_intro = "First up, the artists!<br><br>"
    tracks_intro = "Next, the tracks!<br><br>"
    redirect_to_long = "<br><br>Look at data for <a href='/myfavorites_longterm'>the last few years</a>."
    redirect_to_medium = "<br><br>Look at data for <a href='/myfavorites_mediumterm'>the last 6 months</a>."
    redirect_to_small = "<br><br>Look at data for <a href='/myfavorites_shortterm'>the last 4 weeks</a>."
    redirect_home = "<br><br>Go back to <a href='/favorites_overview'>the summary page</a>."

    if current_page == 'overview':
        return welcome_string+artist_intro+people+'<br>'+tracks_intro+names+'<br>'+top_info+genre_information+redirect_to_long+redirect_to_medium+redirect_to_small
    elif current_page == 'long':
        return welcome_string+artist_intro+people+'<br>'+tracks_intro+names+'<br>'+top_info+genre_information+redirect_to_medium+redirect_to_small+redirect_home
    elif current_page == 'medium':
        return welcome_string+artist_intro+people+'<br>'+tracks_intro+names+'<br>'+top_info+genre_information+redirect_to_long+redirect_to_small+redirect_home
    else:
        return welcome_string+artist_intro+people+'<br>'+tracks_intro+names+'<br>'+top_info+genre_information+redirect_to_long+redirect_to_medium+redirect_home

def get_track_audio_features(name, id):
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'audio-features/'+id, headers=headers)
    features = response.json()

    translate_key = {-1: 'unknown', 0: "C", 1: "C#/Db", 2: "D", 3: "D#/Eb", 4: "E", 5: "F", 6: "F#/Gb", 7: "G", 8:"G#/Ab", 9:"A", 10: "A#/Bb", 11: "B"}
    translate_mode = {1: 'major', 0: 'minor'}

    info = features
    info['name'] = name
    info['key'] = translate_key[features['key']]
    info['mode'] = translate_mode[features['mode']]
    info['overall_key'] = info['key']+' '+info['mode']

    return info

def get_artist_info(name, id):
    if 'access_token' not in session:
        return redirect('/login')
    
    if datetime.datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    
    headers = {
        'Authorization': f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'artists/'+id, headers=headers)
    artist_info = response.json()

    info = artist_info
    info['name'] = name

    return info
    

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)