import logging
import time

from flask import Flask, request, jsonify, make_response

from src.geodab import analyse_from_xml

from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Allow requests from your UI
CORS(app)#, resources={r"/process_metadata": {"origins": "https://kurrawong.github.io"}})

@app.route("/process_metadata", methods=['GET', 'POST'])
def process_metadata():
    start_time = time.time()
    data = request.json
    threshold = data.get('threshold')
    responses = {}
    for doc_name, xml in data.get('xml').items():
        try:
            data = analyse_from_xml(xml, threshold)
            responses[doc_name] = data
            # Set custom headers in the response
        except Exception as e:
            # Handle exceptions and send a 500 response
            return make_response(str(e), 500)
    response = jsonify(responses)
    response.headers['Access-Control-Allow-Origin'] = '*'
    logger.info(f"Time taken: {time.time() - start_time}")
    return response

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
