from __future__ import print_function

import os
import sys
from pprint import pprint

from notion_client import Client

try:
    from dotenv import load_dotenv
except ModuleNotFoundError:
    print("Could not load .env because python-dotenv not found.")
else:
    load_dotenv()

NOTION_TOKEN = os.getenv("NOTION_TOKEN", "")

while NOTION_TOKEN == "":
    print("NOTION_TOKEN not found.")
    NOTION_TOKEN = input("Enter your integration token: ").strip()


import datetime
import os.path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from dateutil.parser import *

# If modifying these scopes, delete the file token.json.
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]


def get_events():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.json"):
        creds = Credentials.from_authorized_user_file("token.json", SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("credentials.json", SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.json", "w") as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # Call the Calendar API
        dt = datetime.datetime.utcnow() + datetime.timedelta(days=1)
        dt = dt.replace(hour=0, minute=0, second=0, microsecond=0)
        now = dt.isoformat() + "Z"  # 'Z' indicates UTC time
        max_dt = dt.replace(hour=23, minute=59, second=0, microsecond=0)
        max = max_dt.isoformat() + "Z"  # 'Z' indicates UTC time
        print(now)
        print(max)
        print("Getting the upcoming 10 events")
        events_result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=now,
                timeMax=max,
                maxResults=10,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )
        events = events_result.get("items", [])

        if not events:
            print("No upcoming events found.")
            sys.exit()
        else:
            return events

    except HttpError as error:
        print("An error occurred: %s" % error)


# Initialize the client
notion = Client(auth=NOTION_TOKEN)


primary_block = os.getenv("PRIMARY_BLOCK", "")

calendar_block = notion.blocks.retrieve(block_id=primary_block)


events = get_events()
block_id = os.getenv("BLOCK_ID", "")
existing_rows = notion.blocks.children.list(block_id=block_id)

for result in existing_rows['results'][1:]:
    notion.blocks.delete(block_id=result['id'])
# Prints the start and name of the next 10 events
for event in events:
    start = event["start"].get("dateTime", event["start"].get("date"))
    start = parse(start)
    summary = event["summary"]
    print(start.time(), event["summary"])

    meeting_title = summary
    meeting_url = event['htmlLink']
    meeting_time = str(start.time())
    google_id = event['id']
    

    new_row_template = [
        {
            "table_row": {
                "cells": [
                    [
                        {
                            "type": "text",
                            "text": {
                                "content": meeting_title,
                                "link": {"url": meeting_url},
                            },
                            "plain_text": meeting_title,
                            "href": meeting_url,
                        }
                    ],
                    [
                        {
                            "type": "text",
                            "text": {"content": meeting_time, "link": None},
                            "plain_text": meeting_time,
                            "href": None,
                        }
                    ]
                ]
            }
        }
    ]

    new_row = notion.blocks.children.append(block_id, children=new_row_template)
