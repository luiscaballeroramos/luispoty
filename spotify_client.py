import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI


class SpotifyClient:
    def __init__(self):
        self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
            redirect_uri=REDIRECT_URI,
            scope="user-read-playback-state user-read-recently-played"
        ))

    def get_current(self):
        try:
            return self.sp.currently_playing()
        except SpotifyException as e:
            if e.http_status == 429:
                retry = int(e.headers.get("Retry-After", 60))
                time.sleep(retry)
                return None
            raise

    def get_recent(self, limit=20):
        return self.sp.current_user_recently_played(limit=limit)
