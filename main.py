from spotify_client import SpotifyClient
from state import EventState
from tracker import Tracker
from db import init_db


def main():
    init_db()
    spotify = SpotifyClient()
    state = EventState()
    tracker = Tracker(spotify, state)
    tracker.run()


if __name__ == "__main__":
    main()
