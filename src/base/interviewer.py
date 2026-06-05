import user

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
        for contact in self.contacts.values():
            
            contact: str = contact.lower()
            address: str = self.contacts[contact]
            
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
                    back.sendmail(hanger_no_reply, self.contacts[contact])

                
            elif contact.__contains__('tel'):
                pass
            elif contact == 'ig':
                pass
            
            del address

    def add_user(self, kind: str, contact_address: str):
        '''
            Add a New Contact to Contacts list for
            send steps later
        '''
        self.contacts.__setitem__(contact_address, kind)

class HangerSteps:

    def __init__(self):
        '''
            Web For Make Registration
        '''
        self.new_user: user.Profile = user.Profile()
        
        self.contact: dict[str, str] = {}

        self.app: user.HangerApp = user.HangerApp()

    def register(self):
        pass

    def login(self, username: str, password: str):
        '''
            Log In user for use app
        '''
        pass

    def password_recovery(self):
        '''
            Make New Password for user
            registered with mail.
        '''
        pass