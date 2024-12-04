from pymongo import MongoClient
import yaml

with open('./config.yml', 'r') as file:
    config = yaml.safe_load(file)

client = MongoClient(config['database']['uri'])
db = client[config['database']['name']]
licenses = db.licenses 