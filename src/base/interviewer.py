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
                pass
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