from __future__ import print_function

import google
import google_auth_oauthlib
import googleapiclient
from django.shortcuts import render, redirect
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response

from calendar_apis.constants import SCOPES, REDIRECT_URL, API_SERVICE_NAME, API_VERSION


@api_view(['GET'])
def GoogleCalendarInitView(request):
    try:
        flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
            'credentials.json', scopes=SCOPES)
        flow.redirect_uri = REDIRECT_URL

        authorization_url, state = flow.authorization_url(
            access_type='offline')

        # Storing the state in the session
        request.session['state'] = state
        # Sending redirection url
        return Response({"url": authorization_url}, status=status.HTTP_200_OK)
    except:
        # Server error
        return Response(status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def GoogleCalendarRedirectView(request):
    # Getting the state back from session
    state = request.session['state']

    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'credentials.json', scopes=SCOPES, state=state)

    flow.redirect_uri = REDIRECT_URL

    authorization_response = request.get_full_path()
    flow.fetch_token(authorization_response=authorization_response)

    credentials = flow.credentials
    request.session['credentials'] = {'token': credentials.token,
                                      'refresh_token': credentials.refresh_token,
                                      'token_uri': credentials.token_uri,
                                      'client_id': credentials.client_id,
                                      'client_secret': credentials.client_secret,
                                      'scopes': credentials.scopes}

    credentials = google.oauth2.credentials.Credentials(
        **request.session['credentials'])

    # Use the Google API Discovery Service to build client libraries, IDE plugins,
    # and other tools that interact with Google APIs.
    # The Discovery API provides a list of Google APIs and a machine-readable "Discovery Document" for each API
    service = googleapiclient.discovery.build(
        API_SERVICE_NAME, API_VERSION, credentials=credentials)

    # Returns the calendars on the user's calendar list
    calendar_list = service.calendarList().list().execute()

    # Getting user ID which is his/her email address
    calendar_id = calendar_list['items'][0]['id']

    # Getting all events associated with a user ID (email address)
    events = service.events().list(calendarId=calendar_id).execute()

    events_list = []
    if not events['items']:
        return Response({"message": "No data found!"}, status=status.HTTP_200_OK)
    else:
        for event in events['items']:
            events_list.append(event)
        return Response({"data": events_list}, status=status.HTTP_200_OK)
    return Response({"error": "No event found"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
