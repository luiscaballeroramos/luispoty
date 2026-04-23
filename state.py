from datetime import datetime, timezone
from config import VERBOSE
from print_functions import print_dt

class EventState:
    def __init__(self):
        self.current_track_id = None
        self.current_track_data = None
        self.start_time = None
        self.last_progress_ms = 0

    def update(self, currently_playing):
        if not currently_playing or not currently_playing.get("item"):
            # if no track is currently playing but we had one before, close that event
            if self.current_track_id:
                return {"action": "track_stopped", "old_event": self.close_event()}
            return {"action": "no_track"}
        track_id = currently_playing["item"]["id"]
        progress_ms = currently_playing.get("progress_ms", 0)
        now = datetime.now(timezone.utc)

        # same track continues
        if track_id == self.current_track_id:
            # restart event if progress goes backwards (e.g. user seeks back or restarts song)
            if progress_ms < self.last_progress_ms - 5000: # Salto hacia atrás > 5s
                old_event = self.close_event()
                self.start_time = now
                self.last_progress_ms = progress_ms
                if VERBOSE:
                    print(
                        f'{print_dt(datetime.now())}🔄 RESTART: {currently_playing["item"]["name"]}'
                    )
                return {"action": "restart", "old_event": old_event, "track_data": currently_playing["item"]}

            self.last_progress_ms = progress_ms
            return {"action": "continue"}

        # new track starts
        old_event = self.close_event() if self.current_track_id else None
        self.current_track_id = track_id
        self.current_track_data = currently_playing["item"]
        self.start_time = now
        self.last_progress_ms = progress_ms
        if VERBOSE:
            print(
                f'{print_dt(datetime.now())}▶️ START: {currently_playing["item"]["name"]}'
            )
        return {
            "action": "new_track",
            "old_event": old_event,
            "track_data": currently_playing["item"],
        }

    def close_event(self):
        if not self.current_track_id: return None

        played_ms = self.last_progress_ms
        # skip if played less than 30s or less than 50% of the track
        duration = self.current_track_data.get("duration_ms", 1)
        is_skipped = played_ms < 30000 and (played_ms / duration) < 0.5
        if VERBOSE:
            print(f"{print_dt(datetime.now())}⏹️ END: Played {played_ms} ms & skipped: {is_skipped}")

        event = {
            "track_id": self.current_track_id, # Se resolverá a ID numérico en tracker.py
            "started_at": self.start_time,
            "ended_at": datetime.now(timezone.utc),
            "played_ms": played_ms,
            "is_skipped": is_skipped,
            "source": "polling"
        }
        self.current_track_id = None
        self.last_progress_ms = 0
        return event
