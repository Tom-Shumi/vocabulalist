from flask import Flask
app = Flask(__name__)

import vocabulalist.views
import vocabulalist.models