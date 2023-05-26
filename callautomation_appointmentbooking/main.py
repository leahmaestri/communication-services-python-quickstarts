from flask import Flask
from werkzeug.exceptions import HTTPException
from exception.exception_handler import handle_http_exception
from core.config import Config
from controller.event_controller import event_api
from controller.incoming_call_controller import incoming_call_api

if __name__ == "__main__":
    app = Flask(__name__, static_folder=Config.STATIC_FOLDER, static_url_path=Config.STATIC_URL_PATH)
    app.logger.setLevel(Config.LOG_LEVEL)
    app.register_blueprint(incoming_call_api)
    app.register_blueprint(event_api)
    app.register_error_handler(HTTPException, handle_http_exception)
    app.run()
