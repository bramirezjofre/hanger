#!/usr/bin/python3
from flask import Flask
from flask import request
import os
import base.user

web = Flask(__name__)
log = base.user.Profile()
users: list[str] = [log, log, log]

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
        try:
            os.system('rm -R /workspaces/hanger/src/__pycache__ && rm -R /workspaces/hanger/src/base/__pycache__')
        except:
            pass    
        
        return  log.get_data().__str__()

@web.route('/registered', methods = ['POST'])
def register_ends() -> str:
    try:
        os.system('rm -R /workspaces/hanger/src/__pycache__ && rm -R /workspaces/hanger/src/base/__pycache__')
    except:
        pass
    
    return '<h1>Congrat You\'re Hanger New User.</h1>'

@web.route('/load', methods = ['POST'])
def load_ends() -> str:
    users.append(f'<li>{request.form['contact']}</li>')
    try:
        os.system('rm -R /workspaces/hanger/src/__pycache__ && rm -R /workspaces/hanger/src/base/__pycache__')
    except:
        pass

    return f'<or>{users}</ol>'


@web.route('/interviewer-report', methods = ['GET', 'POST'])
def make_report() -> str:
    reporting = open('loadUserForm.html', 'r')
    content: str = ''
    
    for line in reporting.readlines():
        content += line

    reporting.close()
    del reporting
    
    try:
        os.system('rm -R /workspaces/hanger/src/__pycache__ && rm -R /workspaces/hanger/src/base/__pycache__')
    except:
        pass

    return content

@web.route('/hanger-steps', methods = ['POST'])
def steps() -> str:
    content: str = ''
    
    for user in users:
        content += f'Send Page To {user}'
        

    try:
        os.system('rm -R /workspaces/hanger/src/__pycache__ && rm -R /workspaces/hanger/src/base/__pycache__')
    except:
        pass
        
    return content    
@web.route('/chatting', methods = ['POST'])
def chat() -> str:
    chatter = base.user.HangerMessage()
    chatter.sender = log
    chatter.receiver = users[1]

    messages: str = f'<h1>From {chatter.sender.name} To {chatter.receiver.name}</h1>'
    
    chatter.chat_messages += request.form['chat']
    try:
        os.system('rm -R /workspaces/hanger/src/__pycache__ && rm -R /workspaces/hanger/src/base/__pycache__')
    except:
        pass
    
    return messages