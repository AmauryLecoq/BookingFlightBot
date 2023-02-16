from azure.cognitiveservices.language.luis.authoring import LUISAuthoringClient
from azure.cognitiveservices.language.luis.authoring.models import ApplicationCreateObject
from azure.cognitiveservices.language.luis.runtime import LUISRuntimeClient

from msrest.authentication import CognitiveServicesCredentials
from functools import reduce

from pathlib import Path
import pandas as pd

from config import DefaultConfig

import requests

from pathlib import Path
import pandas as pd

import json, time, uuid

CONFIG = DefaultConfig()


authoringKey = CONFIG.LUIS_AUTHORING_KEY
authoringEndpoint = CONFIG.LUIS_AUTHORING_HOST_NAME
predictionKey = CONFIG.LUIS_API_KEY
predictionEndpoint = "https://" + CONFIG.LUIS_API_HOST_NAME

app_id = CONFIG.LUIS_APP_ID

versionId = "0.0"

def get_turn_entities(data, index, ls_entities):
    luis_data = []
    for conversation in data["turns"][index]:
        json_part = {}
        txt = conversation["text"].lower()
        json_part["text"] = txt
        json_part["intent"] = "BookFlight"
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
                                    entity["entity"] = key
                                    entity["startPos"] = startCharIndex
                                    entity["endPos"] = endCharIndex
                                    entities.append(entity)
                json_part["entities"] = entities
                
        if (len(json_part)>0):
            if "entities" in json_part.keys():
                if len(json_part["entities"])>0:
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


    
slot_name = "Production"
headers = {'Content-Type': 'application/json','Ocp-Apim-Subscription-Key': predictionKey}

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

LabeledTestSetUtterances = []
for i in range(1, 20):
        LabeledTestSetUtterances.append(luis_data[-i])
        test_json = {"LabeledTestSetUtterances": LabeledTestSetUtterances}

#print(test_json)
req_start = requests.post(f'{predictionEndpoint}/luis/v3.0-preview/apps/\
                          {app_id}/slots/{slot_name}/evaluations',
headers=headers, json=test_json)

start = req_start.json()
print(start)
operationId = start["operationId"]

waiting = True
while waiting:
    req_status = requests.get(f'{predictionEndpoint}/luis/v3.0-preview/apps/\
                              {app_id}/slots/{slot_name}/evaluations/{operationId}/status',
headers=headers
)
    status = req_status.json()
    if status["status"] != 'succeeded':
        print(status)
        print ("Waiting 10 seconds for testing to complete...")
        time.sleep(10)
        
    else: 
        print(status)
        print ("tested")
        waiting = False
        


print(status)

req_result = requests.get(
 f'{predictionEndpoint}/luis/v3.0-preview/apps/{app_id}/slots/{slot_name}/evaluations/{operationId}/result',
 headers=headers   
)

result = req_result.json()

intent_stats = result["intentModelsStats"]
entities_stats = result["entityModelsStats"]

# Retrieve intents score from testing
intent_precision, intent_recall, intent_fScore = intent_stats[0]["precision"],intent_stats[0]["recall"], intent_stats[0]["fScore"]

print()
print(
    f"Our target for Intent is to ensure our bot understand the intent\n\
without rejecting possible request: highest fScore possible\n\
(low False Negative answer rate (high recall) and high True positive answer rate (high Precision))\n\
    intent_precision = {intent_precision}\n\
    intent_recall = {intent_recall}\n\
    intent_fScore = {intent_fScore}\n"
    )

# Retrieve Entities score from testing

print(
    f"As for entities, we need to ensure we understand Customer request.\n\
Therefore, as for Intent, a high fScore is required"
)

for i in range(5):

    entity_name, entity_precision, entity_recall, entity_fScore = entities_stats[i]["modelName"],entities_stats[i]["precision"], entities_stats[i]["recall"], entities_stats[i]["fScore"]
    print(
        f"\n\
    {entity_name}_precision = {entity_precision}\n\
    {entity_name}_recall = {entity_recall}\n\
    {entity_name}_fScore = {entity_fScore}"
        )

