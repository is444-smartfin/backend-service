import logging
import socket
from is452 import app
from flask import make_response

# Default route
@app.route("/", methods=['GET'])
def default_route():
    response = make_response("Python Flask API endpoint. There's nothing here! 😃")
    response.mimetype = "text/plain"
    return response

# Logger
logger = logging.getLogger(__name__)
logger = logging.getLogger()
handler = logging.StreamHandler()
formatter = logging.Formatter(
        "%(asctime)s %(name)-12s %(levelname)-8s %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.INFO)

if __name__ == "__main__":
    logging.info("Starting microservice app...")
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("localhost", 0))
    port = sock.getsockname()[1]
    sock.close()
    
    app.run(port=5000, debug=True)
