import os
import yaml
from flask import Flask

VERSION = '0.4.0'
app = Flask(__name__)

with open("config.yml", 'r') as yamlFile:
    cfg = yaml.load(yamlFile)
