from datetime import datetime

from config import VERBOSE
from print_functions import print_dt


class EventState:
    def __init__(self):
        self.current_track_id = None
        self.start_time = None
        self.last_progress_ms = 0

    def update(self, currentlyPlaying):
        if not currentlyPlaying or not currentlyPlaying.get("item"):
            return {"action": "no_track"}
        track_id = currentlyPlaying["item"]["id"]
        progress_ms = currentlyPlaying.get("progress_ms", 0)

        # same song if same id
        if track_id == self.current_track_id:
            # restart event if progress goes backwards (e.g. user seeks back or restarts song)
            if progress_ms < self.last_progress_ms:
                old_event = self.close_event()
                self.start_time = datetime.now()
                self.last_progress_ms = progress_ms
                if VERBOSE:
                    print(
                        f'{print_dt(datetime.now())}🔄 RESTART: {currentlyPlaying["item"]["name"]}'
                    )
                return {
                    "action": "restart",
                    "old_event": old_event,
                    "track_data": currentlyPlaying["item"],
                }
            # update last progress
            self.last_progress_ms = progress_ms
            return {"action": "continue"}

        # new song if different id
        old_event = None
        if self.current_track_id:
            old_event = self.close_event()
        self.current_track_id = track_id
        self.start_time = datetime.now()
        self.last_progress_ms = progress_ms
        if VERBOSE:
            print(
                f'{print_dt(datetime.now())}▶️ START: {currentlyPlaying["item"]["name"]}'
            )
        return {
            "action": "new_track",
            "old_event": old_event,
            "track_data": currentlyPlaying["item"],
        }

    def close_event(self):
        played_ms = self.last_progress_ms or 0
        if VERBOSE:
            print(f"{print_dt(datetime.now())}⏹️ END: Played {played_ms} ms")
        return {
            "track_id": self.current_track_id,
            "started_at": self.start_time,
            "ended_at": datetime.now(),
            "played_ms": played_ms,
            "is_skipped": played_ms < 30000,
        }
