import os
import preprocessor

from tools.uploadGCS import upload_blob, save_file

from helpers import helpers
from president import generator as pd_generator

def pipeline_2024(raw_data, is_started: bool=True, is_running: bool=False):
    if raw_data==None:
        print("Don't call pipeline function without providing raw_data")
        return False

    year = 2024
    helper = helpers['2024']
    preprocessing_data = preprocessor.parse_president_cec(raw_data, helper)
    
    country_json = pd_generator.generate_country_json(preprocessing_data, is_started, is_running, helper)
    county_sample_json = pd_generator.generate_county_json(preprocessing_data, '09007', helper) ### Just testing

    ### TODO: Store the data to GCS
    root_path = os.path.join(os.environ['ENV_FOLDER'], '2024', 'president', 'map')
    country_filename = os.path.join(root_path, 'country', 'country.json')
    save_file(country_filename, country_json)
    upload_blob(country_filename, year)

    county_filename = os.path.join(root_path, 'county', '09007.json')
    save_file(county_filename, county_sample_json)
    upload_blob(county_filename, year)

    return True