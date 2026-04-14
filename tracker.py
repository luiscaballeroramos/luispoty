import time
import json
from datetime import datetime, timedelta, timezone


from db import Session
from models import Track, ListeningEvent, RawPolling, RecentSync


DUPLICATE_WINDOW = 60  # segundos


class Tracker:
    def __init__(self, spotify_client, state):
        self.spotify = spotify_client
        self.state = state

    # ---------- TRACKS ----------

    def upsert_track(self, session, track_data):
        track = session.query(Track).filter_by(
            spotify_id=track_data["id"]
        ).first()

        now = datetime.utcnow()

        if not track:
            track = Track(
                spotify_id=track_data["id"],
                name=track_data["name"],
                duration_ms=track_data["duration_ms"],
                play_count=1,
                last_played_at=now
            )
            session.add(track)
            session.flush()

        else:
            # 🔹 incrementos controlados
            track.play_count = (track.play_count or 0) + 1
            track.last_played_at = now

        return track

    # ---------- DEDUP ----------

    def is_duplicate(self, session, event):
        window_start = event["started_at"] - timedelta(seconds=DUPLICATE_WINDOW)
        window_end = event["started_at"] + timedelta(seconds=DUPLICATE_WINDOW)

        existing = session.query(ListeningEvent).filter(
            ListeningEvent.track_id == event["track_id"],
            ListeningEvent.started_at.between(window_start, window_end)
        ).first()

        return existing is not None

    # ---------- EVENTS ----------

    def save_event(self, session, event):
        if not event:
            return

        # 🔹 filtro real de escucha
        if event["played_ms"] < 30000:
            return

        exists = session.query(ListeningEvent).filter_by(
            track_id=event["track_id"],
            started_at=event["started_at"]
        ).first()

        if exists:
            return

        session.add(ListeningEvent(**event))

        # 🔹 actualizar métricas reales del track
        track = session.query(Track).filter_by(id=event["track_id"]).first()
        if track:
            track.play_count = (track.play_count or 0) + 1
            track.last_played_at = event["ended_at"]

    # ---------- RAW ----------

    def save_raw(self, session, data):
        session.add(RawPolling(raw_json=json.dumps(data)))

    # ---------- RECOVERY ----------
    def sync_recent(self, session):
        try:
            recent = self.spotify.get_recent(limit=20)
        except Exception:
            return

        last_sync = session.query(RecentSync).first()
        last_time = last_sync.last_played_at if last_sync else None

        if last_time and last_time.tzinfo is None:
            last_time = last_time.replace(tzinfo=timezone.utc)

        new_last_time = last_time

        for item in reversed(recent.get("items", [])):

            played_at = datetime.fromisoformat(
                item["played_at"].replace("Z", "+00:00")
            ).astimezone(timezone.utc)

            if last_time and played_at <= last_time:
                continue

            track_data = item["track"]
            track = self.upsert_track(session, track_data)

            event = {
                "track_id": track.id,
                "started_at": played_at,
                "ended_at": played_at,
                "played_ms": track.duration_ms,
                "is_skipped": False
            }

            if not self.is_duplicate(session, event):
                session.add(ListeningEvent(**event))

            if not new_last_time or played_at > new_last_time:
                new_last_time = played_at

        if new_last_time:
            new_last_time = new_last_time.astimezone(timezone.utc)

            if not last_sync:
                session.add(RecentSync(last_played_at=new_last_time))
            else:
                last_sync.last_played_at = new_last_time

    # ---------- LOOP ----------

    def run(self, interval=15):
        session = Session()
        counter = 0

        while True:
            try:
                data = self.spotify.get_current()

                self.save_raw(session, data)

                result = self.state.update(data)

                if result["action"] in ["new_track", "restart"]:
                    if result["old_event"]:
                        self.save_event(session, result["old_event"])

                    self.upsert_track(session, result["track_data"])

                # recovery
                counter += 1
                if counter >= 4:
                    self.sync_recent(session)
                    counter = 0

                session.commit()

                time.sleep(interval)

            except Exception as e:
                print("Error:", e)
                session.rollback()
                time.sleep(interval * 2)
