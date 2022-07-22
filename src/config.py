import configparser
from src.ui import getConfigFromUser

def create_config():
    api_id, api_hash, phone = getConfigFromUser()
    config = configparser.ConfigParser()
    config.add_section('API_Details')
    config.set('API_Details', 'api_id', api_id)
    config.set('API_Details', 'api_hash', api_hash)
    config.set('API_Details', 'phone', phone)
    with open(r"config.ini", 'w') as configfile:
        config.write(configfile)


def getConfig():
    config_obj = configparser.ConfigParser()
    config_obj.read("config.ini")
    return config_obj['API_Details']['api_id'], config_obj['API_Details']['api_hash'], config_obj['API_Details']['phone']