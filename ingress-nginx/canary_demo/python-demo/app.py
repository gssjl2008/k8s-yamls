from flask import Flask,request
import socket
from os import environ

'''
Use environ variable version to change version
'''

app=Flask(__name__)

@app.route("/")
def index():
    try:
        version = environ['version']
    except KeyError:
        version = 'v1'
    hostname = 'hostname: ' + socket.gethostname() + ', version: ' + version
    return hostname

if __name__ == '__main__':
    # must be 0.0.0.0, because default 127.0.0.1, can't access out of docker
    app.run(host="0.0.0.0")