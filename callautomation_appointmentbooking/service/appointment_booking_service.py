from azure.communication.callautomation import DtmfTone
from flask import current_app as app, request, Response
from service.call_automation_service import CallAutomationService
from core.config import Config
from core import constants


class AppointmentBookingService:
    retry_attempt = 0

    def __init__(self, call_connection_id):
        self.call_connection_service = CallAutomationService(call_connection_id)

    # This is our top level menu that will have our greetings menu.
    def invoke_top_level_menu(self, event):
        # call connected returned! Call is now established.
        if event.type == constants.CALL_CONNECTED_EVENT:
            app.logger.info("Call connected, staring workflow")
            self.call_connection_service.start_recording()
            self.call_connection_service.play_audio(Config.PROMPT_RECORDING_STARTED, "START_RECOGNIZE")

        # Send request to recognize tones
        elif event.type == constants.PLAY_COMPLETED_EVENT and event.data['operationContext'] == "START_RECOGNIZE":
            AppointmentBookingService.retry_attempt = AppointmentBookingService.retry_attempt + 1
            app.logger.info("Triggering recognize attempt %s", AppointmentBookingService.retry_attempt)
            caller_id = request.args.get('callerId').replace("4: ", "+")
            self.call_connection_service.single_digit_dtmf_recognition(caller_id, Config.PROMPT_MAIN_MENU)

        elif event.type == constants.RECOGNIZE_COMPLETED_EVENT or event.type == constants.RECOGNIZE_FAILED_EVENT:
            choice = self.call_connection_service.parse_choice_from_recognize_event(event)
            # Option 1:  Play Message 1
            if choice == DtmfTone.ONE:
                self.call_connection_service.play_audio(Config.PROMPT_CHOICE1, "APPOINTMENT_CONFIRMED")
            # Option 2:  Play Message 2
            elif choice == DtmfTone.TWO:
                self.call_connection_service.play_audio(Config.PROMPT_CHOICE2, "APPOINTMENT_CONFIRMED")
            # Option 3:  Play Message 3
            elif choice == DtmfTone.THREE:
                self.call_connection_service.play_audio(Config.PROMPT_CHOICE3, "APPOINTMENT_CONFIRMED")
            # On invalid choice play retry prompt and retry recognize again
            elif AppointmentBookingService.retry_attempt < 3:
                app.logger.info("Retrying due to invalid choice")
                self.call_connection_service.play_audio(Config.PROMPT_RETRY, "START_RECOGNIZE")
            # wrong input too many times, play goodbye message
            else:
                app.logger.info("Exceeded maximum retries")
                self.call_connection_service.play_audio(Config.PROMPT_GOODBYE, "ATTEMPT_EXCEEDED")

        # wait for play to complete, then terminate call
        elif event.type == constants.PLAY_COMPLETED_EVENT and \
                event.data['operationContext'] in ["APPOINTMENT_CONFIRMED", "ATTEMPT_EXCEEDED"]:
            app.logger.info("Terminating call")
            AppointmentBookingService.retry_attempt = 0
            self.call_connection_service.terminate_call()
