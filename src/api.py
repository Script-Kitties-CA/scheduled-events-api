import asyncio
import requests
import time
import os
from datetime import datetime

import discord
from quart import Quart
from dotenv import load_dotenv

load_dotenv()

SERVER_ID = int(os.environ["SERVER_ID"])
BOT_TOKEN = os.environ["BOT_TOKEN"]

HIDDEN_STR = "hidden"

app = Quart(__name__)

events = None
client = None

class Event:
    """Event type to store a subset of scheduled event data."""

    def __init__(self, name, start_time, end_time):
        self.name = name
        self.start_time = self.convert_time(start_time)
        self.end_time = self.convert_time(end_time)

    def convert_time(self, input_time):
        """Converts datetime objects to ISO time strings."""

        if type(input_time) == datetime:
            return input_time.isoformat()

        return input_time

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

    def __init__(self):
        self._events = dict()
        self.get_events_http()

    def add_event(self, event_id, event):
        """Adds an event."""

        self.update_event(event_id, event)

    def update_event(self, event_id, event):
        """Updates an event."""

        self._events[int(event_id)] = event

    def delete_event(self, event_id):
        """Removes an event."""
        try:
            self._events.pop(event_id)
        except KeyError:
            pass

    def get_events_http(self):
        """Hits the Discord API using HTTP to initialize the events on start."""

        SLEEP_TIME = 10     # Discord API rate limits.

        print("Initializing events from Discord API...")

        while True:
            headers = {"Authorization": f"Bot {BOT_TOKEN}"}
            endpoint = f"https://discord.com/api/guilds/{SERVER_ID}/scheduled-events"

            response = requests.get(endpoint, headers=headers)

            if response.status_code == 200:
                for event in response.json():
                    if event["description"] is None or HIDDEN_STR not in event["description"]:
                        print(event["name"], event["id"])
                        self.add_event(
                            event["id"],
                            Event(
                                event["name"],
                                event["scheduled_start_time"],
                                event["scheduled_end_time"]
                            )
                        )

                break
            else:
                print(f"Waiting {SLEEP_TIME} seconds. Discord API request failed: {response.text}")
                time.sleep(SLEEP_TIME)

        print("Event initialization complete.")

    def get_json(self):
        """Returns a list of all events in JSON format."""

        event_list = []

        for event in self._events.values():
            event_list.append(
                event.to_json()
            )

        event_list.sort(key=lambda x: x["start_time"])

        return event_list

class Client(discord.Client):
    """Discord bot."""

    async def on_ready(self):
        print('Logged on as', self.user)

    async def on_scheduled_event_create(self, event):
        """When discord event is created."""

        if not self.check_event(event):
            return

        events.add_event(
            event.id,
            Event(
                event.name,
                event.start_time,
                event.end_time
            )
        )

    async def on_scheduled_event_update(self, before, event):
        """When a discord event is updated."""

        if not self.check_event(event):
            return

        events.update_event(
            event.id,
            Event(
                event.name,
                event.start_time,
                event.end_time
            )
        )

    def check_event(self, event):
        """Check if hidden string is in event description.
        Ensure event is deleted if it is.
        """

        if event.guild_id != SERVER_ID:
            return False

        if HIDDEN_STR in event.description:
            events.delete_event(event.id)
            return False

        return True

    async def on_scheduled_event_delete(self, event):
        """When a discord event is deleted."""

        events.delete_event(event.id)

@app.route("/events", methods=["GET"])
async def send_events():
    """Returns events as API endpoint."""

    return events.get_json(), 200

@app.before_serving
async def before_serving():
    """Starts the discord bot alongside quart."""

    loop = asyncio.get_event_loop()
    await client.login(BOT_TOKEN)
    loop.create_task(client.connect())

def init():
    """Main."""

    global events, client, app

    events = Events()

    intents = discord.Intents.default()
    client = Client(intents=intents)

init()

if __name__ == "__main__":
    app.run()
