import time
import json
import random
import signal
from datetime import datetime, timedelta, timezone
# from spotipy.exceptions import SpotifyException
from config import VERBOSE
from db import Session, Track, ListeningEvent, RawPolling, RecentSync

DUPLICATE_WINDOW_MINUTES = 2

class Tracker:
    def __init__(self, spotify_client, state):
        self.spotify = spotify_client
        self.state = state
        self.running = True
        # Manejo de cierre limpio
        signal.signal(signal.SIGINT, self.stop_gracefully)
        signal.signal(signal.SIGTERM, self.stop_gracefully)

    def stop_gracefully(self, signum, frame):
        print("\n🛑 Deteniendo tracker...")
        self.running = False

    def upsert_track(self, session, track_data):
        track = session.query(Track).filter_by(spotify_id=track_data["id"]).first()
        if not track:
            track = Track(
                spotify_id=track_data["id"],
                name=track_data["name"],
                duration_ms=track_data["duration_ms"],
                play_count=0,
                last_played_at=datetime(1993,3,25,0,0,0)
            )
            session.add(track)
            session.flush()
        return track

    def is_duplicate(self, session, track_db_id, started_at):
        # Buscamos si existe un evento para el mismo track en una ventana de tiempo
        window_start = started_at - timedelta(minutes=DUPLICATE_WINDOW_MINUTES)
        window_end = started_at + timedelta(minutes=DUPLICATE_WINDOW_MINUTES)

        return session.query(ListeningEvent).filter(
            ListeningEvent.track_id == track_db_id,
            ListeningEvent.started_at.between(window_start, window_end)
        ).first() is not None
    def save_event(self, session, event_dict, track_spotify_id, track_name):
        if not event_dict:
            return

        if VERBOSE:
            print("Saving event:", track_name, event_dict["started_at"])

        # Buscar el track por el spotify_id (que es lo que enviamos desde close_event)
        track = session.query(Track).filter_by(spotify_id=track_spotify_id).first()
        if not track:
            print("❌ Track not found:", track_spotify_id)
            return

        # NO usamos deduplicación: solo sync es fuente de verdad

        new_event = ListeningEvent(
            track_id=track.id, # Aquí usamos el ID numérico
            started_at=event_dict["started_at"],
            ended_at=event_dict["ended_at"],
            played_ms=event_dict["played_ms"],
            is_skipped=event_dict["is_skipped"],
            source=event_dict["source"]
        )
        session.add(new_event)

        if not event_dict["is_skipped"]:
            track.play_count = (track.play_count or 0) + 1
            track.last_played_at = event_dict["ended_at"]

    def sync_recent(self, session):
        try:
            recent = self.spotify.get_recently_played(limit=20)
            last_sync = session.query(RecentSync).first()
            last_time = last_sync.last_played_at.replace(tzinfo=timezone.utc) if last_sync else None

            max_played_at = last_time

            for item in reversed(recent.get("items", [])):
                played_at_utc = datetime.fromisoformat(item["played_at"].replace("Z", "+00:00"))

                if last_time and played_at_utc <= last_time:
                    continue

                track = self.upsert_track(session, item["track"])

                event = {
                    "started_at": played_at_utc - timedelta(milliseconds=item["track"]["duration_ms"]),
                    "ended_at": played_at_utc,
                    "played_ms": item["track"]["duration_ms"],
                    "is_skipped": False,
                    "source": "sync"
                }

                self.save_event(session, event, item["track"]["id"],item["track"]["name"])

                if not max_played_at or played_at_utc > max_played_at:
                    max_played_at = played_at_utc

            # actualizar UNA sola vez
            if max_played_at:
                if not last_sync:
                    session.add(RecentSync(last_played_at=max_played_at))
                else:
                    last_sync.last_played_at = max_played_at

        except Exception as e:
            print(f"Error en sync: {e}")

    def run(self):
        session = Session()
        counter = 0
        print("🚀 Tracker iniciado...")

        while self.running:
            try:
                cp = self.spotify.get_currently_playing()

                if cp:
                    session.add(RawPolling(raw_json=json.dumps(cp)))

                result = self.state.update(cp)

                # Solo aseguramos que el track existe (NO guardamos eventos de polling)
                if result["action"] in ["new_track", "restart", "track_stopped"]:
                    if "track_data" in result:
                        self.upsert_track(session, result["track_data"])

                # Sync periódico (fuente de verdad)
                counter += 1
                if counter >= 3:
                    self.sync_recent(session)
                    counter = 0

                session.commit()
                time.sleep(10 + random.uniform(-2, 2))

            except Exception as e:
                print(f"Loop Error: {e}")
                session.rollback()
                time.sleep(20)

        # cierre limpio
        final_event = self.state.close_event()
        if final_event:
            # opcional: guardarlo o ignorarlo (yo lo ignoraría si sync manda)
            pass

        session.close()
        print("👋 Tracker cerrado correctamente.")
