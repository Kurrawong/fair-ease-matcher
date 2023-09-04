import logging

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
    data = request.json
    xml = data.get('xml')
    threshold = data.get('threshold')

    try:
        data = analyse_from_xml(xml, threshold)
        response = jsonify(data)
        # Set custom headers in the response
        # response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except Exception as e:
        # Handle exceptions and send a 500 response
        return make_response(str(e), 500)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)
