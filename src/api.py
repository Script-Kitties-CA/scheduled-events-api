from re import T
import requests
import time
import os
import logging

from flask import Flask, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

SERVER_ID = int(os.environ["SERVER_ID"])
BOT_TOKEN = os.environ["BOT_TOKEN"]

app = Flask(__name__)
CORS(app)

events = None

class Event:
    """Event type to store a subset of scheduled event data."""

    def __init__(self, name, start_time, end_time, started):
        self.name = name
        self.start_time = start_time
        self.end_time = end_time
        self.started = started

    def to_dict(self):
        """Return the event in a dictionary format."""

        json = {
            "name": self.name,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "started": self.started
        }

        return json

class Events:
    """Stores events."""

    BACKUP_COOLDOWN = 15
    HIDDEN_STR = "hidden"

    def __init__(self):
        self._events = dict()
        self._next_access = time.time()

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
        """Initialize the events on start."""

        app.logger.info("Initializing events from Discord API...")

        while not self.get_events_http():
            app.logger.error(f"Sleeping for {self.BACKUP_COOLDOWN} seconds.")
            time.sleep(self.BACKUP_COOLDOWN)

        app.logger.info("Event initialization complete.")


    def get_events_http(self):
        """Hits the Discord API using HTTP to get the events."""

        headers = {"Authorization": f"Bot {BOT_TOKEN}"}
        endpoint = f"https://discord.com/api/guilds/{SERVER_ID}/scheduled-events"

        response = requests.get(endpoint, headers=headers)

        try:
            if int(response.headers["x-ratelimit-remaining"]) > 0:
                self._next_access = time.time()
            else:
                self._next_access = time.time() + float(response.headers["x-ratelimit-reset-after"])
        except KeyError:
            self._next_access = time.time() + self.BACKUP_COOLDOWN

        if response.status_code == 200:
            self.clear_events()

            for event in response.json():
                if event["description"] is None or Events.HIDDEN_STR not in event["description"]:
                    self.add_event(
                        event["id"],
                        Event(
                            event["name"],
                            event["scheduled_start_time"],
                            event["scheduled_end_time"],
                            event["status"] == 2
                        )
                    )

            return True

        else:
            app.logger.error(f"Discord API request failed:\n{response.text}")
            return False

    def check_access_rate(self):
        """Return if cooldown has elapsed."""

        return time.time() >= self._next_access

    def get_event_list(self):
        """Returns a list of all events in dict format."""

        event_list = []

        for event in self._events.values():
            event_list.append(
                event.to_dict()
            )

        event_list.sort(key=lambda x: (int(not x["started"]), x["start_time"]))

        return event_list

@app.route("/events", methods=["GET"])
def send_events():
    """Returns events with an API endpoint."""

    if events.check_access_rate():
        events.get_events_http()

    return jsonify(events.get_event_list()), 200

def init():
    """Initialize."""

    global events
    events = Events()

init()

if __name__ == "__main__":
    app.run()
else:
    gunicorn_logger = logging.getLogger('gunicorn.error')
    app.logger.handlers = gunicorn_logger.handlers
    app.logger.setLevel(gunicorn_logger.level)
