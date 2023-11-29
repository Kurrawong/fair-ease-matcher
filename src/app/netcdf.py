import asyncio
from pathlib import Path

from netCDF4 import Dataset

from src.analyse import run_all_queries, get_query_args, generate_queries
from src.sparql_queries import find_vocabs_sparql, tabular_query_to_dict






# if __name__ == '__main__':
#     run_extraction()
