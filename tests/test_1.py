import sys
import pathlib
import aiounittest
import pytest

from botbuilder.core import (
    BotFrameworkAdapterSettings,
    ConversationState,
    MemoryStorage,
    UserState,
)

from botbuilder.schema import (
    Activity,
    ActivityTypes
)

from botbuilder.dialogs.prompts import (
    AttachmentPrompt,
    PromptOptions,
    PromptValidatorContext
)


from botbuilder.core import(
    TurnContext,
    ConversationState,
    MemoryStorage,
    MessageFactory
)

from config import DefaultConfig
from dialogs import MainDialog, BookingDialog
from bots import DialogAndWelcomeBot

from botbuilder.dialogs import DialogSet, DialogTurnStatus
from botbuilder.core.adapters import TestAdapter

from adapter_with_error_handler import AdapterWithErrorHandler
from flight_booking_recognizer import FlightBookingRecognizer

from booking_details import BookingDetails


class BookingDialogTest(aiounittest.AsyncTestCase):

    async def test_booking_dialog(self):
        async def exec_test(turn_context: TurnContext):
            #need to set dialog context
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()
            if (results.status == DialogTurnStatus.Empty):
                dialog_context.options = booking_details
                await dialog_context.begin_dialog(dialog_id, booking_details)
            elif results.status == DialogTurnStatus.Complete:
                reply =  results.result
                await turn_context.send_activity(reply)
            
            await conv_state.save_changes(turn_context)

        #need to create object for the test adapter
        adapter = TestAdapter(exec_test)
        # for dialog state u need converstation state
        conv_state = ConversationState(MemoryStorage())
        booking_details = BookingDetails()
        dialog_id = BookingDialog.__name__
        #for dialog set u need dialoag state
        dialogs_state = conv_state.create_property("dialog_state")



        dialogs = DialogSet(dialogs_state)
        dialogs.add(BookingDialog())
        #test adapter will be use to pass all information
        


        step1 = await adapter.test("Hello", "To what city would you like to travel?") # call adapter to ask
        step2 = await step1.test("Paris", "From what city will you be travelling?") # input to the adapter
        step3 = await step2.test("Lille", "On what date would you like to travel?")
        step4 = await step3.test("01-01-2023", "On what date would you like to travel?")
        step5 = await step4.test("31-01-2023", "What will be your budget for this trip?")
        step6 = await step5.send("1000")

        await step6.assert_reply(
            f"Please confirm, I have you traveling to: Paris"
            f" from: Lille on: 2023-01-01."
            f" Returning on: 2023-01-31 with a budget of : 1000 ."
            f" (1) Yes or (2) No")
            
