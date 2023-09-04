import logging
from pathlib import Path
from typing import List

from src.geodab import analyse_from_xml

import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(files: List[Path], threshold: float) -> dict:
    """
    processes a list of metadata files to a specified threshold
    """
    results = {}
    for file in files:
        xml_string = file.read_text()
        results[file.stem] = analyse_from_xml(xml_string, threshold)

    # Ensure the 'output' directory exists
    output_dir = Path('output')
    output_dir.mkdir(exist_ok=True)

    # Generate the filename based on current date and time
    filename = output_dir / (datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + "_output.json")

    # Dump the results to the generated filename
    with filename.open('w') as json_file:
        json.dump(results, json_file, indent=4)

    logging.info(f"Results written to {filename}")



if __name__ == "__main__":
    files = Path('data/sdn-xml').glob('*.xml')
    threshold = 0.8
    main(files, threshold)
