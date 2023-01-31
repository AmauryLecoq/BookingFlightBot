"""Handle budget resolution for booking dialog."""

from botbuilder.core import MessageFactory, BotTelemetryClient, NullTelemetryClient
from botbuilder.dialogs import WaterfallDialog, DialogTurnResult, WaterfallStepContext
from botbuilder.dialogs.prompts import (
    TextPrompt,
    NumberPrompt,
    PromptValidatorContext,
    PromptOptions,
    ChoicePrompt,
    ConfirmPrompt,
    PromptValidatorContext,   
)

from botbuilder.dialogs.choices import Choice

from .cancel_and_help_dialog import CancelAndHelpDialog

from recognizers_number_with_unit import NumberWithUnitRecognizer
from recognizers_text import Culture
from recognizers_number import NumberRecognizer

class BudgetResolverDialog(CancelAndHelpDialog):
    """Resolve the budget"""

    def __init__(
        self,
        dialog_id: str = None,
        telemetry_client: BotTelemetryClient = NullTelemetryClient(),
    ):
        super(BudgetResolverDialog, self).__init__(
            dialog_id or BudgetResolverDialog.__name__, telemetry_client
        )
        self.telemetry_client = telemetry_client

        budget_prompt = TextPrompt(
            TextPrompt.__name__,
            BudgetResolverDialog.budget_prompt_validator
        )

        budget_prompt.telemetry_client = telemetry_client

        waterfall_dialog = WaterfallDialog(
            WaterfallDialog.__name__ + "3", 
            [
                self.budget_step,
                self.verification_step,
                self.currency_step,
                self.final_step]
        )
        waterfall_dialog.telemetry_client = telemetry_client

        self.add_dialog(budget_prompt)
        self.add_dialog(ConfirmPrompt(
            ConfirmPrompt.__name__,
            default_locale="en-us"
            ))
        self.add_dialog(ChoicePrompt(
            ChoicePrompt.__name__
        ))
        self.add_dialog(waterfall_dialog)

        self.initial_dialog_id = WaterfallDialog.__name__ + "3"
    
    async def budget_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        booking_details = step_context.options

        if booking_details.budget is not None:
            return await step_context.next(booking_details.budget)
        elif booking_details.number_list is not None:
            if len(booking_details.number_list) > 0:

                listofchoice = []
                [listofchoice.append(Choice(i)) for i in booking_details.number_list]
                listofchoice.append(Choice("Other"))
                return await step_context.prompt(
                    ChoicePrompt.__name__,
                    PromptOptions(prompt=MessageFactory.text(
                        #here we put what we want the user to see
                        "I have identified potential budget in your request. Please select an option"),
                        #now we can make the user choose. Input the list prior to this to use it
                        choices=listofchoice
                        )
                )
        else:
            return await step_context.prompt(
                    TextPrompt.__name__,
                    PromptOptions(
                        prompt=MessageFactory.text(f"Please provide me with your budget")
                    ),
                )

    async def verification_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        booking_details = step_context.options
        # Capture the response to the previous step's prompt
        # if already captured in luis or manually then it is in string
        if type(step_context.result) == str:
            booking_details.budget = step_context.result

        else:
            # if not, it is coming from choice
            booking_details.budget = step_context.result.value
            if booking_details.budget == "Other" : 
                return await step_context.prompt(
                TextPrompt.__name__,
                PromptOptions(
                    prompt=MessageFactory.text("Please provide me with your budget")
                ),
            )

        return await step_context.next(booking_details.budget)

    async def currency_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        booking_details = step_context.options
        booking_details.budget = step_context.result
        cur_obj = NumberWithUnitRecognizer(Culture.English)
        cur_model = cur_obj.get_currency_model()
        recog_currency = cur_model.parse(booking_details.budget)
        if len(recog_currency) > 0:
            if recog_currency[0].resolution is not None:
                booking_details.budget = f"{recog_currency[0].resolution['value']} {recog_currency[0].resolution['unit']}"
            return await step_context.next(booking_details.budget)
        else:
            listofchoice = [Choice("Dollar"), Choice("Euro"), Choice("Pound"), Choice("Yen")]
            return await step_context.prompt(
                ChoicePrompt.__name__,
                PromptOptions(prompt=MessageFactory.text(
                    #here we put what we want the user to see
                    "Please select a currency"),
                    #now we can make the user choose. Input the list prior to this to use it
                    choices=listofchoice
                    )
            )

    async def final_step(
        self, step_context: WaterfallStepContext
    ) -> DialogTurnResult:
        booking_details = step_context.options
        if type(step_context.result) == str:
            booking_details.budget = step_context.result

        else:
            # if not, it is coming from choice
            booking_details.budget = booking_details.budget + " " + step_context.result.value + "s"
        return await step_context.end_dialog(booking_details.budget)   




    



    @staticmethod
    async def budget_prompt_validator(prompt_context: PromptValidatorContext) -> bool:
        """ Validate the budget provided is in proper form. """
        if (prompt_context.recognized.succeeded is False):
            await prompt_context.context.send_activity("Please enter a budget with currency")
            return False
        else:
            value = prompt_context.recognized.value
            bud_obj = NumberWithUnitRecognizer(Culture.English)
            bud_model = bud_obj.get_currency_model()
            recog_budget = bud_model.parse(value)
            if len(recog_budget) > 0:
                if int(recog_budget[0].resolution["value"]) > 0:
                    return True
        await prompt_context.context.send_activity("Please enter a valid budget including currency")
        return False
