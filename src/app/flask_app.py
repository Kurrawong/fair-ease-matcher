import json
import logging
import time
from pathlib import Path

from flask import Flask, request, jsonify, make_response
from flask_cors import CORS

from src.analyse import run_methods

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = json.load(open(Path(__file__).parent / "config.json"))
app = Flask(__name__)
for k,v in config.items():
    app.config[k] = v


# Allow requests from your UI
CORS(app)



@app.route("/process-metadata", methods=['GET', 'POST'])
def process_metadata():
    start_time = time.time()

    analysis_methods = request.args.get("Methods")
    if analysis_methods:
        analysis_methods = analysis_methods.split(",")

    restrict_to_themes = request.args.get("Restrict to Themes")
    if restrict_to_themes:
        restrict_to_themes = restrict_to_themes.split(",")

    if analysis_methods != ["netcdf"]:
        data = request.json
    else:
        data = request.files
    threshold = data.get('threshold')
    responses = {}
    available_methods = ["xml", "full", "netcdf"]
    if not analysis_methods:
        analysis_methods = available_methods

    # run XML methods
    if ("xml" in analysis_methods) or ("full" in analysis_methods):
        for doc_name, xml in data.get('xml').items():
            try:
                run_methods(doc_name, analysis_methods, responses, threshold, xml, restrict_to_themes, "XML")
            except Exception as e:
                # Handle exceptions and send a 500 response
                return make_response(f"Exception from Python: {str(e)}", 500)

    if "netcdf" in analysis_methods:
        for doc_name in data:
            doc_data = data[doc_name].read()
            try:
                run_methods(doc_name, analysis_methods, responses, threshold, doc_data, restrict_to_themes, "NETCDF")
            except Exception as e:
                # Handle exceptions and send a 500 response
                return make_response(f"Exception from Python: {str(e)}", 500)

    response = jsonify(responses)
    response.headers['Access-Control-Allow-Origin'] = '*'
    logger.info(f"Time taken: {time.time() - start_time}")
    return response


@app.route("/config", methods=['GET'])
def available_methods():
    response = jsonify(config)
    response.headers['Access-Control-Allow-Origin'] = '*'
    return response


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8004)
