import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI

class SpotifyClient:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id="1562b563518b40848fa76d89a37609a3",
            client_secret="ba1248d2aac04918aab2a7af32978113",
            redirect_uri="http://127.0.0.1:8888/",
            scope="user-read-playback-state user-read-recently-played"
        ))

    def get_current(self):
        return self.sp.currently_playing()

    def get_recent(self, limit=20):
        return self.sp.current_user_recently_played(limit=limit)
