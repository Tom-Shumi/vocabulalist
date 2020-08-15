from flask.views import MethodView
from flask import Flask
from vocabulalist import app

if __name__ == '__main__':
  app.run(debug=True, port=5000, threaded=True)