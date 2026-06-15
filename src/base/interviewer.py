import user

web: user.HangerApp = user.HangerApp()

class loadUser:
    
    def __init__(self):
        '''
            When The Interviewer proof that
            the person reach the objetives
            then write the contact for send
            registration steps changing the
            algorithm for kind of contact.
        '''
        # Dictonary "Address" To "Kind Of Contact"
        self.contacts: dict[str, str] = []

    def send_steps(self):
        '''
            Filter by kind of contact and sends
            steps of different way with link to
            registration flask web app
        '''
        for contact in self.contacts.keys():
            
            address: str = contact.lower()
            contact: str = self.contacts[address].lower()
            
            if contact.__contains__('mail'):
                # RFC 821 Standard
                import smtplib
                # Security Layer For Addresses
                import aiosmtpd
                import ssl
                from getpass import getpass

                port: int = 465
                
                server: str = 'smtp.gmail.com'
                hanger_no_reply: str = '<hanger_no-reply@gmail.com>'
                password: str = getpass().encode('utf-32')
                
                ssl_layer = ssl.create_default_context()
                
                with smtplib.SMTP_SSL(server, port, context = ssl_layer) as back:
                    # Only expose password when is needed and delete for externs 
                    back.login(hanger_no_reply, password.decode('utf-32'))
                    del password
                    # Send Mail With Next Steps
                    back.sendmail(hanger_no_reply, address, f'<div><h1>Hanger Registration Steps</h1><a href = "{web.domain}/hangerSteps.html"></a></div>')      
            elif contact.__contains__('tel'):
                from twilio.rest import Client
                
                message_text: str = f'Register to Hanger Social Media in {web.domain}/hangerSteps.html'
                # Complete with twilio account data
                account_sid: str = ''
                auth_token: str = ''
                twilio_phone: str = ''
                # Send Messages
                twilio_client: Client = Client(account_sid, auth_token)
                sender = twilio_client.messages.create  (
                                                            body = message_text,
                                                            FROM = twilio_phone,
                                                            to = address
                                                        )
            elif contact == 'ig':
                 #import Meta Instagram API for send messages in the chat
                 from selenium import webdriver
                 from selenium.webdriver.common.by import By
                 from selenium.webdriver.common.keys import Keys
                 from selenium.webdriver.support.wait import WebDriverWait
                 # Configuration of Bot
                 hangerIg: str = '@'
                 hangerPass: str = ''
                 first_msg: str = f'Register to Hanger Social Media in Next Link...'
                 second_msg: str = f'{web.domain}/hangerSteps.html'
                 # Navigator Simulation
                 navigator = webdriver.Chrome()
                 navigator.get(f'https://www.instagram.com/accounts/login/?next=https://www.instagram.com/&;;//&is_from_rle')
                 # Login in instagram
                 user_bot = WebDriverWait(navigator, timeout = 60).until   (
                                                                                lambda form: form.find_element  (
                                                                                                                    By.XPATH,
                                                                                                                    "//*[@id = 'loginForm&']/div/div[1]/div/label/input"
                                                                                                                )
                                                                            )
                 user_bot.send_keys(hangerIg)
                 del user_bot, hangerIg
                 password_bot = navigator.find_element  (
                                                            By.XPATH,
                                                            "*[id = 'loginForm&']/div/div[2]/div/label/input"
                                                        )
                 password_bot.send_keys(hangerPass)
                 del password_bot, hangerPass
                 # Simulate keyboard button pulsation
                 enter = navigator.find_element (
                                                    By.XPATH,
                                                    "//*[@id = 'loginFrom&']/div/div[3]/label/input"
                                                )
                 enter.click()
                 del enter
                 # Unable Pop-Up Window
                 disable = navigator.find_element   (
                                                        By.CSS_SELECTOR,
                                                        '._a9_1'
                                                    )
                 disable.click()
                 del disable
                 # Send message to users with link for continue the registration
                 for user in self.contacts.keys():
                     userIg: str = user.lower()
                     # Use send message from Hanger instagram to selected user chat
                     for messages_text in [first_msg, second_msg]:
                         user_chat = navigator.find_element (
                                                                By.CSS_SELECTOR,
                                                                'input[type = "text"]'
                                                            )
                         user_chat.send_keys(message_text)
                         # Clean memory after each iterations
                         del user_chat
                     # Clean memory for get free to don't use many RAM
                     del userIg
            # Free Out RAM for Get More
            del selenium, contact, address, navigator, first_msg, second_msg

    def add_user(self, kind: str, contact_address: str):
        '''
            Add a New Contact to Contacts list for
            send steps later
        '''
        if (self.contacts.__contains__(contact_address) == False):
            # Only Add New Contacts
            self.contacts.__setitem__(contact_address, kind)

class HangerSteps:

    def __init__(self):
        '''
            Web For Make Registration
        '''
        self.new_user: user.Profile = user.Profile()
        
        self.contact: dict[str, str] = {}

        self.app: user.HangerApp = user.HangerApp()


    def valid(self, text: str) -> bool:
        '''
            Said if a password is or not valid
        '''
        return text.isalnum()
    
    def register(self):
        
        # Flask App for Sign Up New User
        from flask import Flask
        # Get username and password
        user_name: str = ''
        passed: str = ''
        # Clean Memory For Load Next Module without Use More Memory
        del Flask
        # Save In DataBase
        import sqlite3
        
        sql_pointer = sqlite3.connect('registered_users.db')
        sql_engine = sql_pointer.cursor()
        # SQL DataBase Transaction For Create User
        sql_engine.execute('CREATE TABLE hanger_register(user varchar, password varchar);')
        sql_engine.execute(f'INSERT INTO hanger_register VALUES ({user_name}, {passed});')
        sql_pointer.commit()
        del user_name, passed
        # Close And Clean (Transaction End)
        sql_engine.close()
        sql_pointer.close()
        del sql_engine, sql_pointer

    def login(self, username: str, password: str):
        '''
            Log In user for use app
        '''
        import sqlite3
        # Make inside to class for don't access from external objects by security
        sql_pointer = sqlite3.connect('registered_users.db')
        sql_engine = sql_pointer.cursor()
        # Must Be Exist One User with that name and password
        import hashlib
        password: str = hashlib.sha3_256(password.encode('UTF-8')).hexdigest()
        answer = sql_engine.execute(f'SELECT user WHERE word = {password} AND user = {username} FROM hanger_register;')
        del hashlib
        answer: int = answer.rowcount
        self.new_user.name = username
        del password, username
        # Complete Database Transaction and clean memory
        sql_pointer.commit()
        sql_engine.close()
        sql_pointer.close()
        del sql_engine, sql_pointer
        # Log when The password and The user is valid
        if (answer == 1):
            # Log User
            del answer
            self.app.logged_user = self.new_user
            self.app.run(self.app.title, self.app.domain, self.app.icon)
        else:
            # Show mistake to user
            del answer
            print('<h1>The User With That password isn\'t valid</h1>')

    def password_recovery(self):
        '''
            Make New Password for user
            registered with mail.
        '''
                # Save In DataBase
        import sqlite3
        
        sql_pointer = sqlite3.connect('registered_users.db')
        sql_engine = sql_pointer.cursor()
        # SQL DataBase Transaction For Create User
        new_password: str = ''
        before_password: str = sql_engine.execute('SELECT password FROM hanger_register;')
        sql_pointer.commit()
        while ((not self.valid(new_password)) or (new_password == before_password)):
            pass
        del user_name, passed
        # Close And Clean (Transaction End)
        sql_engine.close()
        sql_pointer.close()
        del sql_engine, sql_pointer