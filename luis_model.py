from azure.cognitiveservices.language.luis.authoring import LUISAuthoringClient
from azure.cognitiveservices.language.luis.authoring.models import ApplicationCreateObject
from azure.cognitiveservices.language.luis.runtime import LUISRuntimeClient

from msrest.authentication import CognitiveServicesCredentials
from functools import reduce

from pathlib import Path
import pandas as pd

from config import DefaultConfig

import requests

CONFIG = DefaultConfig()

import json, time, uuid

import azure.cognitiveservices.language.luis.version as azl

azure_luis_version = azl.VERSION
print(f"azure-cognitiveservices-language-luis package version: {azure_luis_version}")

if (azure_luis_version != "0.7.0"):
    print("please use the 0.7.0 version of azure-cognitiveservices-language-luis package")
    exit()



def get_grandchild_id(model, childName, grandChildName):
    
    theseChildren = next(filter((lambda child: child.name == childName), model.children))
    theseGrandchildren = next(filter((lambda child: child.name == grandChildName), theseChildren.children))
    
    grandChildId = theseGrandchildren.id
    
    return grandChildId

def get_turn_entities(data, index, ls_entities):
    luis_data = []
    for conversation in data["turns"][index]:
        json_part = {}
        txt = conversation["text"].lower()
        json_part["text"] = txt
        json_part["intentName"] = "BookFlight"
        # Nous n'utiliserons que ce qu'ont
        # écrit les utilisateurs
        if conversation["author"] == "user":
            for act in conversation["labels"]["acts_without_refs"]:
                entities = []
                for arg in act["args"]:
                    if arg["key"] in ls_entities:
                        entity = {}
                        key = arg["key"].lower()
                        if "val" in arg.keys():
                            val = arg["val"]
                            if val is not None:
                                val = arg["val"].lower()
                                if val != "-1":
                                    startCharIndex = txt.index(val)
                                    endCharIndex = startCharIndex + len(val)
                                    entity["entityName"] = key
                                    entity["startCharIndex"] = startCharIndex
                                    entity["endCharIndex"] = endCharIndex
                                    entities.append(entity)
                json_part["entityLabels"] = entities
                
        if (len(json_part)>0):
            if "entityLabels" in json_part.keys():
                if len(json_part["entityLabels"])>0:
                    luis_data.append(json_part)
    return luis_data

def convert_data(data, ls_entities):
        luis_data = []
        for i in range(data.shape[0]):
            json_part = get_turn_entities(data, i, ls_entities)
            if len(json_part)>0:
                for j in range(len(json_part)):
                    luis_data.append(json_part[j])
        return luis_data

def luis_model():

    # add calls here, remember to indent properly
    authoringKey = CONFIG.LUIS_AUTHORING_KEY
    authoringEndpoint = CONFIG.LUIS_AUTHORING_HOST_NAME
    predictionKey = CONFIG.LUIS_API_KEY
    predictionEndpoint = "https://" + CONFIG.LUIS_API_HOST_NAME

    #Extract information from our json file
    BASE_DIR = Path(__file__).resolve(strict=True).parent
    file_name = f"{BASE_DIR}/data/frames.json"
    data = pd.read_json(file_name)


    ls_entities = [
        "or_city",
        "dst_city",
        "str_date",
        "end_date",
        "budget"
    ]

    # pour convertir les data pour LUIS :
    luis_data = convert_data(data, ls_entities)
    #train_utterances_qty = int(len(luis_data)*80/100)
    train_utterances_qty = 100

    # We use a UUID to avoid name collisions.
    UteranceQty = train_utterances_qty
    appName = "FlightBookingLuis" + str(UteranceQty) + " " + str(uuid.uuid4())
    versionId = "0.0"
    intentName = "BookFlight"

    client = LUISAuthoringClient(authoringEndpoint, CognitiveServicesCredentials(authoringKey))

    # define app basics
    appDefinition = ApplicationCreateObject(name=appName, initial_version_id=versionId, culture='en-us')

    # create app
    app_id = client.apps.add(appDefinition)

    # get app id - necessary for all other changes
    print("Created LUIS app with ID {}".format(app_id))

    client.model.add_intent(app_id, versionId, intentName)

    # Add Prebuilt entity
    client.model.add_prebuilt(app_id, versionId, prebuilt_extractor_names=["number"])
    client.model.add_prebuilt(app_id, versionId, prebuilt_extractor_names=["datetimeV2"])
    client.model.add_prebuilt(app_id, versionId, prebuilt_extractor_names=["geographyV2"])

    # add entity to app
    budgetId = client.model.add_entity(app_id, versionId, name='budget')
    dst_cityId = client.model.add_entity(app_id, versionId, name='dst_city')
    or_cityId = client.model.add_entity(app_id, versionId, name='or_city')
    end_dateId = client.model.add_entity(app_id, versionId, name='end_date')
    str_dateId = client.model.add_entity(app_id, versionId, name='str_date')

    cityId_listId = [dst_cityId, or_cityId]
    dateId_list = [end_dateId, str_dateId]

    # Some entity have features: Number in Budget
    prebuiltFeatureNotRequiredDefinition = { "model_name": "number" }
    client.features.add_entity_feature(app_id, versionId, budgetId, prebuiltFeatureNotRequiredDefinition)

    # Some entity have features: datimeV2 in end_date & str_date
    prebuiltFeatureNotRequiredDefinition = { "model_name": "datetimeV2" }
    for prebuiltId in dateId_list:
        client.features.add_entity_feature(app_id, versionId, prebuiltId, prebuiltFeatureNotRequiredDefinition)
    
    # Some entity have features: geographyV2 in dst_city & dst_city
    prebuiltFeatureNotRequiredDefinition = { "model_name": "geographyV2" }
    for prebuiltId in cityId_listId:
        client.features.add_entity_feature(app_id, versionId, prebuiltId, prebuiltFeatureNotRequiredDefinition)


    # Define labeled example for BookFlight intent
    for i in range(UteranceQty):
        labeledExampleUtteranceWithMLEntity = luis_data[i]
        client.examples.add(app_id, versionId, labeledExampleUtteranceWithMLEntity, { "enableNestedChildren": True })

    #Define example for None Intent (around 10% of main intent)
    ExampleUtterrancesNone = [
        {
            "text": "I want to dance",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "I want to go to the restaurant",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "I want to book a hotel in paris",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "Please, we want to buy this book",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "Canada weather is colder than France one",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "Give me the weather forecast",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "The Sun and the Moon are part of the Solar system",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "My cab is not yet here, please advice location",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "My train was cancelled again, please advice next departure",
            "intentName": "None",
            "entityLabels" : [],
        },
        {
            "text": "Quantic computer are the future breakthrough technology",
            "intentName": "None",
            "entityLabels" : [],
        },
    ]

    for utterance in ExampleUtterrancesNone:
        client.examples.add(app_id, versionId, utterance, { "enableNestedChildren": True })


    client.train.train_version(app_id, versionId)
    waiting = True
    while waiting:
        info = client.train.get_status(app_id, versionId)

        # get_status returns a list of training statuses, one for each model. Loop through them and make sure all are done.
        waiting = any(map(lambda x: 'Queued' == x.details.status or 'InProgress' == x.details.status, info))
        if waiting:
            print ("Waiting 10 seconds for training to complete...")
            time.sleep(10)
        else: 
            print ("trained")
            waiting = False

    # Prepare for publishing of the app
    client.apps.update_settings(app_id, is_public= True)

    # Publish the app
    responseEndpointInfo = client.apps.publish(app_id, versionId, is_staging=False)

luis_model()

    











