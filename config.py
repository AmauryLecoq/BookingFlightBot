#!/usr/bin/env python
# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Configuration for the bot."""

from dotenv import load_dotenv

import os

load_dotenv()


class DefaultConfig:
    """Configuration for the bot."""

    #PORT = 3978
    #for deployment trial
    PORT = 8000
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    LUIS_APP_ID = os.environ.get("LuisAppId", "")
    LUIS_API_KEY = os.environ.get("LuisAPIKey", "")
    # LUIS endpoint host name, ie "westus.api.cognitive.microsoft.com"
    LUIS_API_HOST_NAME = os.environ.get("LuisAPIHostName", "")
    APPINSIGHTS_INSTRUMENTATION_KEY = os.environ.get(
        "AppInsightsInstrumentationKey", ""
    )
    CONNECTION_STRING = f"InstrumentationKey={APPINSIGHTS_INSTRUMENTATION_KEY}"
    LUIS_AUTHORING_KEY = os.environ.get("LuisAuthoringKey", "")
    LUIS_AUTHORING_HOST_NAME = os.environ.get("LuisAuthoringEndpoint", "")
