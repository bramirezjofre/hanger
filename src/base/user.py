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

class HangerMessage:
    
    def __init__(self):
        '''
            Chat Between users
        '''
        self.sender: Profile = Profile()

        self.receiver: Profile = Profile()

        self.chat_messages: list[str] = []

        self.chat_images: list[str] = []

    def send(self, chat: str, images: list[str]):
        '''
            Send Message from sender
            to receiver
        '''
        message: str = f'<span>{chat}</span><br />'
        origin: str = list(self.sender.contact.keys())[0]
        destiny: str = list(self.receiver.contact.keys())[0]
        # Add Message
        self.chat_messages.extend(chat)
        # Add Images
        self.chat_images.extend(images)
        # Clear from unneeded data
        del message, origin, destiny
        
class HangerPost:
    
    def __init__(self):
        '''
            Define Data For User
            Post and give HTML view
        '''
        self.content: str = ''

        self.images: list[str] = []

        self.comments: list[str] = []

        self.likes: int = 0

    def give_HTML(self, style: str) -> str:
        '''
            Give HTML text with style to use
        '''
        text: str = '<!DOCTYPE html>\n\t<head>\n\t\t<title>Hanger Post</title>\n\t\t'
        style_text: str = ''
        with open(f'/workspaces/hanger/pages/{style}', 'r') as handler:
            for line in handler.readlines():
                style_text += line
        text += f'<style>{style_text}</style>\n\t'
        del style_text
        text += '</head>\n\t'
        text += '<body>\n\t\t'
        # Post Generation Start
        text += f'<div class = post>{self.content}'
        for image in self.images:
            text += f'<br /><img src = "https://github.com/martina-pauer/hanger/raw/main/pages/images/users/{image}" alt = "Post Image"/><br />'
        text += '</div>\n'
        # Post Generation End
        # Add Comments
        text += '\n\t\t<div class = comment>'
        for comment in self.comments:
            text += comment
        text += '\n\t\t</div>\n\t</body>\n</html>'

        return text

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

    def upload_post(self, post: HangerPost):
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

    def send_message(self, rec: Profile):
        '''
            Chat With An Receiver User
        '''
        chat: HangerMessage = HangerMessage()
        chat.sender = self.logged_user
        chat.receiver = rec
        # This Works Because Will Be Used in 'hanger.py' Context
        chat.send(request.form['chat-image'], chat_images) 

    def make_group(self, members: list[Profile]):
        '''
            Use Many Profile objects for
            create a chat group with many
            users.
        '''
        for member in members:
            # Send The Sama Message From An User To All
            self.send_message(member)

    def give_like(self, post: HangerPost):
        '''
            Increase like counting 
            for post analising 
            and recomendations.
        '''
        # Leave of this way for simplicity (One User Could give more likes to same post)
        post.likes += 1

    def write_comment(self, content: HangerPost):
        '''
            Add New Comment To 
            post comments list.
        '''
        content.comments.append(f'<h3>{self.logged_user.name}<h3><div class = "comment">{content.give_HTML('hanger.css')}</div')