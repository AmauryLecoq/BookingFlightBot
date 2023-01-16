
from enum import Enum
from typing import Dict
from botbuilder.ai.luis import LuisRecognizer
from botbuilder.core import IntentScore, TopIntent, TurnContext

from booking_details import BookingDetails

# Package to help with Luis entities recognition
from recognizers_date_time import DateTimeRecognizer
from recognizers_text import Culture


class Intent(Enum):
    BOOK_FLIGHT = "BookFlight"
    NONE_INTENT = "None"


def top_intent(intents: Dict[Intent, dict]) -> TopIntent:
    max_intent = Intent.NONE_INTENT
    max_value = 0.0

    for intent, value in intents:
        intent_score = IntentScore(value)
        if intent_score.score > max_value:
            max_intent, max_value = intent, intent_score.score

    return TopIntent(max_intent, max_value)


class LuisHelper:
    @staticmethod
    async def execute_luis_query(
        luis_recognizer: LuisRecognizer, turn_context: TurnContext
    ) -> (Intent, object):
        """
        Returns an object with preformatted LUIS results for the bot's dialogs to consume.
        """
        result = None
        intent = None

        try:
            recognizer_result = await luis_recognizer.recognize(turn_context)

            intent = (
                sorted(
                    recognizer_result.intents,
                    key=recognizer_result.intents.get,
                    reverse=True,
                )[:1][0]
                if recognizer_result.intents
                else None
            )

            if intent == Intent.BOOK_FLIGHT.value:
                result = BookingDetails()

                # We need to get the result from the LUIS JSON which at every level returns an array.
                # Get the destination city
                dst_city_entities = recognizer_result.entities.get("dst_city", [])
                if len(dst_city_entities) > 0:
                    if recognizer_result.entities.get("dst_city", [])[0]:
                        result.destination = dst_city_entities[0].capitalize()
                    
                    else:
                        result.destination = None
                
                else :
                    result.destination = None


                # Get the origin city
                or_city_entities = recognizer_result.entities.get("or_city", [])
                if len(or_city_entities) > 0:
                    if recognizer_result.entities.get("or_city", [])[0]:
                        result.origin = or_city_entities[0].capitalize()
                    
                    else:
                        result.origin = None
                
                else :
                    result.origin = None

                # Get the Start Date of the trip from Luis
                obj = DateTimeRecognizer(Culture.English)
                model = obj.get_datetime_model()
                str_date_entities = recognizer_result.entities.get("str_date", [])
                # As this might contains unformatted date/time, we will the recognozer to transform it
                
                if len(str_date_entities)>0:
                    if recognizer_result.entities.get("str_date", [])[0]:
                        str_date = recognizer_result.entities.get("str_date", [])[0]
                        recog_date = model.parse(str_date)
                        for resolution in recog_date[0].resolution["values"]:
                            if "timex" in resolution:
                                date = resolution["timex"]
                                result.start_date = date
                                break
                    else:
                        result.start_date = None
                else:
                    result.start_date = None
                
                # Get the Return date of the trip from Luis
                end_date_entities = recognizer_result.entities.get("end_date", [])
                # As this might contains unformatted date/time, we will the recognozer to transform it
                if len(end_date_entities)>0:
                    if recognizer_result.entities.get("end_date", [])[0]:
                        end_date = recognizer_result.entities.get("end_date", [])[0]
                        recog_date = model.parse(end_date)
                        for resolution in recog_date[0].resolution["values"]:
                            if "timex" in resolution:
                                date = resolution["timex"]
                                result.end_date = date
                                break
                    else:
                        result.end_date = None
                else:
                    result.end_date = None


                # It is possible that ML entities is note recognize but that luis find PreBuild Entities
                # This is valid for both Town/country and Time
                # This value will be a TIMEX. And we are only interested in a Date so grab the first result and drop
                # the Time part. TIMEX is a format that represents DateTime expressions that include some ambiguity.
                # e.g. missing a Year.
                # Get the Start date of the trip


                """if end_date_entities:
                    timex = end_date_entities[0]["timex"]

                    if timex:
                        datetime = timex[0].split("T")[0]

                        result.end_date = datetime"""

                # Get the budget for the trip



        except Exception as exception:
            print(exception)

        return intent, result
