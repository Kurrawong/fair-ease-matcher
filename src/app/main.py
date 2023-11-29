import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from src.analyse import run_methods

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main(files: List[Path], methods: List, threshold: float) -> dict:
    """
    processes a list of metadata files to a specified threshold
    """
    results = {}
    for file in files:
        xml_string = file.read_text()
        run_methods(file.stem, methods, results, threshold, xml_string, None)

    # Ensure the 'output' directory exists
    output_dir = Path('output') / file.parent.stem
    output_dir.mkdir(exist_ok=True)

    # Generate the filename based on current date and time
    filename = output_dir / (datetime.now().strftime('%Y-%m-%d_%H-%M-%S') + "_output.json")

    # Dump the results to the generated filename
    with filename.open('w') as json_file:
        json.dump(results, json_file, indent=4)

    logging.info(f"Results written to {filename}")


if __name__ == "__main__":
    # files = Path('data/sdn-xml').glob('*.xml')
    # files = Path('data/emodnet-xml').glob('*.xml')
    # files = Path('data/argo-xml').glob('*.xml')
    # files = [Path('data/argo-xml/C4FCB80C939B2B9DC3E9686BCDB67507780799C3.xml')]
    # files = Path('data/copernicus-xml').glob('*.xml')
    files = [Path('data/copernicus-xml/19ff80f5-5e4e-4e18-9fae-9c5e9cee8a9c.xml')]

    # files = [Path('data/sdn-xml/sdn-open_urn_SDN_CDI_LOCAL_1609-1609-1609-ds04-4.xml')]
    threshold = 0.8
    # methods = ["full"]
    # methods = ["xml"]
    methods = ["xml", "full"]
    main(files, methods, threshold)
