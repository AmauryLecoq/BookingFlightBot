# Copyright (c) Microsoft Corporation. All rights reserved.
# Licensed under the MIT License.
"""Handle date/time resolution for booking dialog."""

from datatypes_date_time.timex import Timex

from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import WaterfallDialog, DialogTurnResult, WaterfallStepContext
from botbuilder.dialogs.prompts import (
    DateTimePrompt,
    PromptValidatorContext,
    PromptOptions,
    DateTimeResolution,
    ConfirmPrompt
)
from .cancel_and_help_dialog import CancelAndHelpDialog


class DateResolverDialog(CancelAndHelpDialog):
    """Resolve the date"""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(DateResolverDialog, self).__init__(
            dialog_id or DateResolverDialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client

        date_time_prompt = DateTimePrompt(
            DateTimePrompt.__name__, DateResolverDialog.datetime_prompt_validator
        )
        date_time_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__ + "2", 
            [
                self.start_date_step,
                self.end_date_step,
                self.verification_step,
                self.final_step]
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(date_time_prompt)
        self.add_dialog(ConfirmPrompt(
            ConfirmPrompt.__name__,
            default_locale="en-us"
            ))
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__ + "2"

    async def start_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for the date."""
        booking_details = step_context.options

        if not booking_details.start_date :

            prompt_msg = f"On what date would you like to start your travel?"
            reprompt_msg = (
                "I'm sorry, for best results, please enter your travel "
                "date including the month, day and year."
            )

            return await step_context.prompt(
                DateTimePrompt.__name__,
                PromptOptions(  # pylint: disable=bad-continuation
                    prompt=MessageFactory.text(prompt_msg),
                    retry_prompt=MessageFactory.text(reprompt_msg),
                ),
            )

        # We have a Date we just need to check it is unambiguous.
        if "definite" in Timex(booking_details.start_date).types:
            # This is essentially a "reprompt" of the data we were given up front.
            return await step_context.prompt(
                DateTimePrompt.__name__, PromptOptions(prompt=reprompt_msg)
            )

        return await step_context.next(DateTimeResolution(timex=booking_details.start_date))

    async def end_date_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        """Prompt for the date."""
        booking_details = step_context.options
        booking_details.start_date = step_context.result[0].timex
        if not booking_details.end_date :

            prompt_msg = f"On what date would you like to return from your travel?"
            reprompt_msg = (
                "I'm sorry, for best results, please enter your travel "
                "date including the month, day and year."
            )

            return await step_context.prompt(
                DateTimePrompt.__name__,
                PromptOptions(  # pylint: disable=bad-continuation
                    prompt=MessageFactory.text(prompt_msg),
                    retry_prompt=MessageFactory.text(reprompt_msg),
                ),
            )

        # We have a Date we just need to check it is unambiguous.
        if "definite" in Timex(booking_details.end_date).types:
            # This is essentially a "reprompt" of the data we were given up front.
            return await step_context.prompt(
                DateTimePrompt.__name__, PromptOptions(prompt=reprompt_msg)
            )

        return await step_context.next(DateTimeResolution(timex=booking_details.end_date))

    async def verification_step(self, step_context: WaterfallStepContext):
        """Cleanup - set final return value and end dialog."""
        booking_details = step_context.options
        booking_details.end_date = step_context.result[0].timex

        if booking_details.start_date > booking_details.end_date:
            msg = (
                f"You have indicated wanting to start your on travel on : {booking_details.start_date} "
                f"which is after your return date requested on : {booking_details.start_date} "
                f"Please confirm you want to proceed.")

            return await step_context.prompt(
            ConfirmPrompt.__name__,
            PromptOptions(prompt=MessageFactory.text(msg)
            )
        )

        else:
            return await step_context.end_dialog(booking_details)

    async def final_step(self, step_context: WaterfallStepContext):
        """Cleanup - set final return value and end dialog."""
        if step_context.result:
            booking_details = step_context.options
            return await step_context.end_dialog(booking_details)
        else:
            # If the client says we have not properly record the data
            booking_details = step_context.options
            booking_details.start_date = None
            booking_details.end_date = None
            return await step_context.begin_dialog(DateResolverDialog.__name__, booking_details)

    @staticmethod
    async def datetime_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        """ Validate the date provided is in proper form. """
        if prompt_context.recognized.succeeded:
            timex = prompt_context.recognized.value[0].timex.split("T")[0]

            # TODO: Needs TimexProperty
            return "definite" in Timex(timex).types

        return False
