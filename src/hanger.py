#!/usr/bin/python3
from flask import Flask
from flask import request
import os
import base.user

web = Flask(__name__)
log = base.user.Profile()

@web.route('/', methods = ['GET', 'POST'])
def main() -> str:
    '''
        The hanger Social Media main GUI
    '''
    content: str = ''
    
    if request.method == 'GET':
        # Show The Web for login with the registered user
        page = open('/workspaces/hanger/pages/hanger.html')
        for line in page.readlines():
            content += line
        # Clear The Extra Objects When Aren't needed    
        page.close()
        del page
        
    return content

@web.route('/hanger-app', methods = ['POST'])
def logged() -> str:
    '''
        Show The App after login    
    '''
    if request.method == 'POST':
        log.name = request.form['hanger-user']
        log.age = hex(hash(request.form['hanger-password']))
        log.contact['mail'] = request.form['hanger-user']
        os.system('rm -R /workspaces/hanger/src/__pyc* && rm -R /workspaces/hanger/base/__pyc*')
        del os
        return  log.get_data().__str__()

#@web.route('/registered', methods = ['POST'])
#@web.route('/load', methods = ['POST'])
#@web.route('/interviewer-report', methods = ['POST'])
#@web.route('/hanger-steps', methods = ['POST'])
#@web.route('/chatting', methods = ['POST'])