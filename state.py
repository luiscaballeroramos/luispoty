from datetime import datetime


class TrackerState:
    def __init__(self):
        self.current_track_id = None
        self.start_time = None
        self.last_progress_ms = 0

    def update(self, data):
        if not data or not data.get("item"):
            return {"action": "no_track"}

        track_id = data["item"]["id"]
        progress_ms = data.get("progress_ms", 0)

        # misma canción
        if track_id == self.current_track_id:

            # reinicio
            if progress_ms < self.last_progress_ms:
                old_event = self.close_event()

                self.start_time = datetime.utcnow()
                self.last_progress_ms = progress_ms

                return {
                    "action": "restart",
                    "old_event": old_event,
                    "track_data": data["item"]
                }

            self.last_progress_ms = progress_ms
            return {"action": "continue"}

        # nueva canción
        old_event = None
        if self.current_track_id:
            old_event = self.close_event()

        self.current_track_id = track_id
        self.start_time = datetime.utcnow()
        self.last_progress_ms = progress_ms

        return {
            "action": "new_track",
            "old_event": old_event,
            "track_data": data["item"]
        }

    def close_event(self):
        played_ms = self.last_progress_ms or 0

        return {
            "track_id": self.current_track_id,
            "started_at": self.start_time,
            "ended_at": datetime.utcnow(),
            "played_ms": played_ms,
            "is_skipped": played_ms < 30000
        }
