import pandas as pd
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve(strict=True).parent
file_name = f"{BASE_DIR}/frames.json"
data = pd.read_json(file_name)


ls_entities = [
    "or_city",
    "dst_city",
    "str_date",
    "end_date",
    "budget"
]

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


# pour convertir les data pour LUIS :
luis_data = convert_data(data, ls_entities)

json_object = json.dumps(luis_data)
json_file = f"{BASE_DIR}/extract_frames.json"

with open(json_file, "w") as outfile:
    outfile.write(json_object)