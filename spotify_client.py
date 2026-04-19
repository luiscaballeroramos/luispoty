import spotipy
from spotipy.oauth2 import SpotifyOAuth

from config import CLIENT_ID, CLIENT_SECRET, REDIRECT_URI
import tkinter as tk
from tkinter import messagebox


class SpotifyClient:
    def __init__(self):
        self.sp = spotipy.Spotify(
            auth_manager=SpotifyOAuth(
                client_id=CLIENT_ID,
                client_secret=CLIENT_SECRET,
                redirect_uri=REDIRECT_URI,
                scope="user-read-playback-state user-read-recently-played",
            )
        )

    def get_currently_playing(self):
        try:
            return self.sp.currently_playing()
        except:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror(
                "Error", "Error en SpotifyClient.get_currently_playing"
            )
            root.destroy()
            return None

        # except SpotifyException as e:
        #     if e.http_status == 429:
        #         retry = int(e.headers.get("Retry-After", 60))
        #         time.sleep(retry)
        #         return None
        #     raise

    def get_recently_played(self, limit=20):
        return self.sp.current_user_recently_played(limit=limit)
