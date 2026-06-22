#!/usr/bin/python3
from flask import Flask
from flask import request
import os
import base.interviewer

loads = Flask(__name__)
# Cache data for don't read the file with each page reload
loader_form: str = ''
new_user = base.interviewer.loadUser()

with open('/workspaces/hanger/pages/loadUserForm.html', 'r') as reader:
    for tags_line in reader.readlines():
        loader_form += tags_line
# Decorator for each web reload
@loads.route('/load', methods = ['GET', 'POST'])
def load_user() -> str:
    
    if request.method == 'POST':
        
        new_user.add_user(request.form['kind'], request.form['contact'])
        new_user.send_steps()
    
    return loader_form
# Main Program for execute web app in this server
if __name__ == '__main__':
    os.system(f'flask --app {loads.name} run')
# Clean cache and data after use when the web app was finished
del load_user, new_user, loader_form, loads, base.interviewer, os, request, Flask