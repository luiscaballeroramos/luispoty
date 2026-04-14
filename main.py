from spotify_client import SpotifyClient
from state import TrackerState
from tracker import Tracker
from db import init_db


def main():
    init_db()

    spotify = SpotifyClient()
    state = TrackerState()

    tracker = Tracker(spotify, state)
    tracker.run()


if __name__ == "__main__":
    main()
