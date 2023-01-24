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



class BookingDialogTest(aiounittest.AsyncTestCase):

    async def test_booking_dialog(self):
        async def exec_test(turn_context: TurnContext):
            #need to set dialog context
            dialog_context = await dialogs.create_context(turn_context)
            results = await dialog_context.continue_dialog()
            if (results.status == DialogTurnStatus.Empty):
                options = PromptOptions(prompt=Activity(
                    type= ActivityTypes.message,
                    text="what is your email adress?"))
                await dialog_context.prompt("email_prompt", options)
            elif results.status == DialogTurnStatus.Complete:
                reply =  results.result
                await turn_context.send_activity(reply)
            
            await conv_state.save_changes(turn_context)

        #need to create object for the test adapter
        adapter = TestAdapter(exec_test)
        # for dialog state u need converstation state
        conv_state = ConversationState(MemoryStorage())
        #for dialog set u need dialoag state
        dialogs_state = conv_state.create_property("dialog_state")



        dialogs = DialogSet(dialogs_state)
        dialogs.add(BookingDialog)
        #test adapter will be use to pass all information

        step1 = await adapter.test("Hello", "what can I do for you?") # call adapter to ask
        step2 = await step1.send("my email adress is amaury@live.com") # input to the adapter
        await step2.assert_reply("amaury@live.com")
            
