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
                            'contact': f'Use {list(self.contact.values())[0]} To {list(self.contact.keys())[0]}'
                        }

        return data

class HangerApp:

    def __init__(self):
        '''
            Data about the flask app
            for customization.
        '''
        self.title: str = 'Hanger Social Media'

        self.domain: str = '.app.github.dev'

        self.icon: str = '/workspaces/pages/images/hanger_june_second.svg'

        self.logged_user: Profile = Profile()

    def run(self, title: str, domain: str, icon: str):
        '''
            Start Flask App with first word
            in lower letters as name
        '''
        # Start App
        import os
        os.system(f'flask --app {title.split(' ')[0].lower()} run')
        del os
        # Update All Data In The Object With Parameters
        self.title = title
        self.domain = domain
        self.icon = icon

    def upload_post(post: HangerPost):
        '''
            Use generated post and write 
            post to post folders for 
            could be shows to every user.
        '''
        # Make An Original and Predictible name for post page
        upload = open(f'post_{hash(post)}.html', 'w')

        upload.write(post.give_HTML('hanger.css'))

        upload.close()

        del upload