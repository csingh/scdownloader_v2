import traceback
import requests
import logging

def download_file(url, file_path):
    try:
        logging.debug("Downloading %(1)s to %(2)s." % {"1" : url, "2" : file_path})
        with open(file_path, 'wb') as f:
            response = requests.get(url, stream=True)

            if not response.ok:
                return False

            for block in response.iter_content(1024):
                if not block:
                    break

                f.write(block)

            return True
    except Exception as ex:
        logging.error("Failed to download file from %s." % url)
        logging.error(ex)
        return False

def load_json_data(json_path):
    try:
        logging.debug("Loading JSON data from %s." % json_path)
        with open(json_path) as f:
            d = json.load(f)
            return d
    except Exception as ex:
        logging.error("Failed to load JSON data from %s" % json_path)
        return None

def save_json_data(data, json_path):
    try:
        logging.debug("Saving JSON data to %s." % json_path)
        with open(json_path, "w") as f:
            json.dump( data, f, sort_keys=True, indent=4, separators=(',', ':') )
            logging.debug("Saved JSON data");
    except:
            logging.error("Failed to save JSON data to %s" % json_path)