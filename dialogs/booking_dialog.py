# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Flight booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.dialogs import (
    WaterfallDialog, 
    WaterfallStepContext, 
    DialogTurnResult
)
from botbuilder.dialogs.prompts import (
    ConfirmPrompt, 
    TextPrompt,
    PromptOptions,
    ChoicePrompt,
    PromptValidatorContext
)
from botbuilder.core import (
    MessageFactory, 
    BotTelemetryClient, 
    NullTelemetryClient
)

from botbuilder.dialogs.choices import Choice

from .cancel_and_help_dialog import CancelAndHelpDialog
from .date_resolver_dialog import DateResolverDialog
from booking_details import BookingDetails
from .budget_resolver_dialog import BudgetResolverDialog
from botbuilder.schema import InputHints


import logging
from opencensus.ext.azure.log_exporter import AzureLogHandler, AzureEventHandler
from config import DefaultConfig

#To deal with warning logging
CONFIG = DefaultConfig()

connection_string = CONFIG.CONNECTION_STRING
logger = logging.getLogger(__name__)
logger.addHandler(AzureLogHandler(
    connection_string=connection_string)
)

class BookingDialog(CancelAndHelpDialog):
    """Flight booking implementation."""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(BookingDialog, self).__init__(
            dialog_id or BookingDialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client
        text_prompt = TextPrompt(TextPrompt.__name__)
        text_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__,
            [
                self.destination_step,
                self.destination_verif_step,
                self.origin_step,
                self.origin_verif_step,
                self.dest_ori_identical,
                # change travel date by start date
                self.start_date_step,
                # add end date step
                self.end_date_step,
                self.budget_step,
                self.confirm_step,
                self.final_step,
            ],
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(text_prompt)
        self.add_dialog(ChoicePrompt(
            ChoicePrompt.__name__
        ))
        self.add_dialog(ConfirmPrompt(
            ConfirmPrompt.__name__,
            default_locale="en-us"
            ))
        self.add_dialog(
            DateResolverDialog(
                DateResolverDialog.__name__,
                self.telemetry_client
                )
        )
        self.add_dialog(
            BudgetResolverDialog(
                BudgetResolverDialog.__name__,
                self.telemetry_client
            )
        )
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__

    async def destination_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for destination."""
        booking_details = step_context.options

        if booking_details.destination is None:
            if booking_details.geo_list is not None:
                if len(booking_details.geo_list) > 0:
                    listofchoice = []
                    [listofchoice.append(Choice(i)) for i in booking_details.geo_list]
                    listofchoice.append(Choice("Other"))
                    
                    return await step_context.prompt(
                    ChoicePrompt.__name__,
                    PromptOptions(prompt=MessageFactory.text(
                        #here we put what we want the user to see
                        "I have identified potential destination. Please select an option"),
                        #now we can make the user choose. Input the list prior to this to use it
                        choices=listofchoice
                        )
                )
            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text(f"To what city would you like to travel?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.destination)

    
    
    async def destination_verif_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        # Capture the response to the previous step's prompt
        # if already captured in luis or manually then it is in string
        if type(step_context.result) == str:
            booking_details.destination = step_context.result

        else:
            # if not, it is coming from choice
            booking_details.destination = step_context.result.value
            if booking_details.destination == "Other" : 
                return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("To what city would you like to travel?")
                ),
            )

        return await step_context.next(booking_details.destination)
        

    async def origin_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Prompt for origin city."""
        booking_details = step_context.options
        booking_details.destination = step_context.result
        if booking_details.origin is None:
            if booking_details.geo_list is not None:
                if len(booking_details.geo_list) > 0:
                    listofchoice = []
                    [listofchoice.append(Choice(i)) for i in booking_details.geo_list]
                    listofchoice.append(Choice("Other"))
                    return await step_context.prompt(
                    ChoicePrompt.__name__,
                    PromptOptions(prompt=MessageFactory.text(
                        #here we put what we want the user to see
                        "I have identified potential destination. Please select an option"),
                        #now we can make the user choose. Input the list prior to this to use it
                        choices=listofchoice
                        )
                )

            return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("From what city will you be travelling?")
                ),
            )  # pylint: disable=line-too-long,bad-continuation

        return await step_context.next(booking_details.origin)

    async def origin_verif_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        # Capture the response to the previous step's prompt
        # if already captured in luis or manually then it is in string
        if type(step_context.result) == str:
            booking_details.origin = step_context.result

        else:
            # if not, it is coming from choice
            booking_details.origin = step_context.result.value
            if booking_details.origin == "Other" : 
                return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("From what city would you like to travel?")
                ),
            )

        return await step_context.next(booking_details.origin)

    async def dest_ori_identical(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.origin = step_context.result
        if booking_details.destination == booking_details.origin:
            msg = (
                f"I have understood you want to travel to : {booking_details.destination} "
                f"which is identical to your origin : {booking_details.origin} "
                f"Please confirm you want to proceed.")

            return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(msg)
            )
        )

        else:
            return await step_context.next(booking_details.origin)

    # Change travel_date_step by start_date_step
    async def start_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options
        if step_context.result:

            # Capture the results of the previous step
            booking_details.origin = step_context.result
            if not booking_details.start_date or self.is_ambiguous(
                booking_details.start_date
            ):
                #booking_details.start_date = None
                return await step_context.begin_dialog(
                    DateResolverDialog.__name__,
                    booking_details
                )  # pylint: disable=line-too-long

            return await step_context.next(booking_details.start_date)
        else:
            booking_details.destination = None
            booking_details.origin = None

            return await step_context.begin_dialog(BookingDialog.__name__, booking_details)

    
    # ADd end_date_step
    async def end_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for travel date.
        This will use the DATE_RESOLVER_DIALOG."""

        booking_details = step_context.options

        # Capture the results of the previous step
        if type(step_context.result) == str:
            booking_details.start_date = step_context.result
        else:
            refreshed_details = step_context.result
            booking_details.start_date = refreshed_details.start_date
        
        if not booking_details.end_date or self.is_ambiguous(
            booking_details.end_date
        ):
            #booking_details.end_date = None
            return await step_context.begin_dialog(
                DateResolverDialog.__name__, booking_details
            )  # pylint: disable=line-too-long

        return await step_context.next(booking_details.end_date)

    async def budget_step(self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Confirm the information the user has provided."""
        booking_details = step_context.options

        # Capture the results of the previous step
        if type(step_context.result) == str:
            booking_details.end_date = step_context.result
        else:
            refreshed_details = step_context.result
            booking_details.end_date = refreshed_details.end_date
        # Capture the results of the previous step
        
        #if not booking_details.budget:
        return await step_context.begin_dialog(
                BudgetResolverDialog.__name__,
                booking_details
                ) 
        #return await step_context.next(booking_details.budget)

    


    async def confirm_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Confirm the information the user has provided."""
        booking_details = step_context.options
        if type(step_context.result) == str:
            # Capture the results of the previous step
            booking_details.budget = step_context.result
        else:
            booking_details.budget = f"{step_context.result}"
        msg = (
            f"Please confirm, I have you traveling to: { booking_details.destination }"
            f" from: { booking_details.origin } on: { booking_details.start_date}."
            f" Returning on: { booking_details.end_date } with a budget of : {booking_details.budget}."
        )

        # Offer a YES/NO prompt.
        return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(msg)
            )
        )

    async def final_step(self, step_context: WaterfallStepContext) -> DialogTurnResult:
        """Complete the interaction and end the dialog."""
        if step_context.result:
            booking_details = step_context.options
            #after adding confirm step
            #booking_details.end_date = step_context.result

            return await step_context.end_dialog(booking_details)
        else:
            # If the client says we have not properly record the data
            # problem = we are in an infinite loop till confirmation is given
            line = "Invalid proposal to Client"
            logger.warning(line)
            sorry_text = (
                "Sorry that I misunderstood your request. I will do better next time I promise"
            )
            sorry_message = MessageFactory.text(
                sorry_text, sorry_text, InputHints.ignoring_input
            )
            await step_context.context.send_activity(sorry_message)
            booking_details = None
            return await step_context.end_dialog(booking_details)

    def is_ambiguous(self, timex: str) -> bool:
        """Ensure time is correct."""
        timex_property = Timex(timex)
        return "definite" not in timex_property.types
