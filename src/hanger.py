#!/usr/bin/python3
import os
import secrets
from pathlib import Path

from flask import Flask, jsonify, request, send_from_directory, session

import base.interviewer
import base.user


PROJECT_ROOT = Path(__file__).resolve().parents[1]
PAGES_DIR = PROJECT_ROOT / "pages"

web = Flask(__name__)
log = base.user.Profile()
users: list[str] = [base.user.Profile(), base.user.Profile(), base.user.Profile()]
chat_images: list[str] = []

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
    log.name = request.form['hanger-user']
    log.age = hex(hash(request.form['hanger-password']))
    log.contact['mail'] = request.form['hanger-user']
             
    return  log.get_data().__str__()

@web.route('/registered', methods = ['POST'])
def register_ends() -> str:  
    return '<h1>Congrat You\'re Hanger New User.</h1>'

@web.route('/load', methods = ['POST'])
def load_ends() -> str:
    users.append(f"<li>{request.form['contact']}</li>")
    
    return f'<or>{users}</ol>'


@web.route('/interviewer-report', methods = ['GET', 'POST'])
def make_report() -> str:
    reporting = open('/workspaces/hanger/pages/loadUserForm.html', 'r')
    content: str = ''
    
    for line in reporting.readlines():
        content += line

    reporting.close()
    del reporting
    
    return content

@web.route('/hanger-steps', methods = ['POST'])
def steps() -> str:
    content: str = ''
    
    for user in users:
        content += f'Send Page To {user}'
        
    return content
    
@web.route('/chatting', methods = ['POST'])
def chat() -> str:
    chatter = base.user.HangerMessage()
    
    chatter.sender = log
    chatter.sender.name = 'First'
    chatter.sender.contact = {'1' : 'Tel'}
    
    chatter.receiver = users[1]
    chatter.receiver.name = 'Second'
    chatter.receiver.contact = {'2' : 'Tel'}

    messages: str = f'<h1>From {chatter.sender.name} To {chatter.receiver.name}</h1>'
    
    chat_images.append(request.form['chat-image'])
    
    chatter.send(request.form['message'], chat_images)
    
    for message in chatter.chat_messages:
        messages += message
            
    render = base.user.HangerPost()
    render.content = ''.join(chatter.chat_messages)
    render.images = chat_images
    messages += render.give_HTML('hanger.css')
    
    return messages
