class Profile:

    def __init__(self):
        '''
            Strtucture user
            data
        '''
        self.name: str = 'New'
        
        self.age: int = 0

        self.contact: dict[str, str] = {}

    def get_data(self) -> dict[str, str]:
        '''
            Give user data as a dict 
            for could be used as JSON
        '''
        data: dict  =   {
                            'name': self.name,
                            'age': self.age.__str__(),
                            # Kind Contact to Contact Address
                            'contact': f'Use {self.value()[0]} To {self.key()[0]}'
                        }

class HangerApp:

    def __init__(self):
        '''
            Data about the flask app
            for customization.
        '''
        pass