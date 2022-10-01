import requests
import time
import os
import logging

from flask import Flask
from dotenv import load_dotenv

load_dotenv()

SERVER_ID = int(os.environ["SERVER_ID"])
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = Flask(__name__)

events = None

class Event:
    """Event type to store a subset of scheduled event data."""

    def __init__(self, name, start_time, end_time):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time

    def to_json(self):
        """Return the event in JSON format."""

        json = {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time
        }

        return json

class Events:
    """Stores events."""

    COOLDOWN = 30
    HIDDEN_STR = "hidden"

    def __init__(self):
        self._events = dict()
        self.last_access = 0

        self.get_events_http()

    def add_event(self, event_id, event):
        """Adds an event."""

        self._events[int(event_id)] = event

    def delete_event(self, event_id):
        """Removes an event."""

        try:
            self._events.pop(event_id)
        except KeyError:
            pass

    def clear_events(self):
        """Removes all events."""

        self._events.clear()

    def initialize(self):
        """Hits the Discord API using HTTP to initialize the events on start."""

        SLEEP_TIME = 10     # Discord API rate limits.

        app.logger.info("Initializing events from Discord API...")

        while not self.get_events_http():
            app.logger.error(f"Sleeping for {SLEEP_TIME} seconds.")
            time.sleep(SLEEP_TIME)

        app.logger.info("Event initialization complete.")


    def get_events_http(self):
            headers = {"Authorization": f"Bot {BOT_TOKEN}"}
            endpoint = f"https://discord.com/api/guilds/{SERVER_ID}/scheduled-events"

            response = requests.get(endpoint, headers=headers)

            if response.status_code == 200:
                self.clear_events()

                for event in response.json():
                    if event["description"] is None or Events.HIDDEN_STR not in event["description"]:
                        self.add_event(
                            event["id"],
                            Event(
                                event["name"],
                                event["scheduled_start_time"],
                                event["scheduled_end_time"]
                            )
                        )

                self.last_access = time.time()

                return True

            else:
                app.logger.error(f"Discord API request failed:\n{response.text}")
                return False

    def check_last_access(self):
        """Return if cooldown has elapsed."""

        return time.time() - self.last_access >= Events.COOLDOWN

    def get_json(self):
        """Returns a list of all events in JSON format."""

        event_list = []

        for event in self._events.values():
            event_list.append(
                event.to_json()
            )

        event_list.sort(key=lambda x: x["start_time"])

        return event_list

@app.route("/events", methods=["GET"])
def send_events():
    """Returns events as API endpoint."""

    if events.check_last_access():
        events.get_events_http()

    return events.get_json(), 200

def init():
    """Main."""

    global events
    events = Events()

init()

if __name__ == "__main__":
    app.run()
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
