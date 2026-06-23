import html
import subprocess
from pathlib import Path
from typing import List, Optional
from urllib.parse import quote


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PAGES_DIR = PROJECT_ROOT / "pages"


class Profile:
    def __init__(self):
        self.name: str = "New"
        self.age: int = 0
        self.contact: dict[str, str] = {}

    def get_data(self) -> dict[str, str]:
        contact = ""
        if self.contact:
            kind, address = next(iter(self.contact.items()))
            contact = f"Use {address} To {kind}"
        return {
            "name": self.name,
            "age": str(self.age),
            "contact": contact,
        }


class HangerMessage:
    def __init__(self):
        self.sender: Profile = Profile()
        self.receiver: Profile = Profile()
        self.chat_messages: List[str] = []
        self.chat_images: List[str] = []

    def send(self, chat: str, images: Optional[List[str]] = None) -> str:
        message = chat.strip()
        if message:
            self.chat_messages.append(message)
        if images:
            self.chat_images.extend(
                Path(image).name for image in images if image and Path(image).name
            )
        return self.give_HTML()

    def give_HTML(self) -> str:
        rendered = ["<div class=\"chat\">"]
        for message in self.chat_messages:
            rendered.append(f"<div><span>{html.escape(message)}</span>")
            for image in self.chat_images:
                safe_image = quote(Path(image).name)
                rendered.append(
                    f'<img src="/pages/images/{safe_image}" alt="Chat attachment">'
                )
            rendered.append("</div>")
        rendered.append("</div>")
        return "".join(rendered)


class HangerPost:
    def __init__(self):
        self.content: str = ""
        self.images: List[str] = []
        self.comments: List[str] = []
        self.likes: int = 0

    def give_HTML(self, style: str) -> str:
        style_path = PAGES_DIR / Path(style).name
        style_text = style_path.read_text(encoding="utf-8")
        text = [
            "<!DOCTYPE html><html><head><title>Hanger Post</title>",
            f"<style>{style_text}</style></head><body>",
            f'<div class="post">{html.escape(self.content)}',
        ]
        for image in self.images:
            safe_image = quote(Path(image).name)
            text.append(
                '<br><img '
                f'src="/pages/images/users/{safe_image}" '
                'alt="Post image"><br>'
            )
        text.append("</div><div class=\"comments\">")
        for comment in self.comments:
            text.append(f'<div class="comment">{html.escape(comment)}</div>')
        text.append("</div></body></html>")
        return "".join(text)


class HangerApp:
    def __init__(self):
        self.title: str = "Hanger Social Media"
        self.domain: str = "http://127.0.0.1:5000"
        self.icon: str = "/pages/images/hanger_june_second.svg"
        self.logged_user: Profile = Profile()

    def run(self, title: str, domain: str, icon: str):
        '''
            Start Flask App with first word
            in lower letters as name
        '''
        # Start App
        import os
        os.system(f"flask --app {title.split(' ')[0].lower()} run")
        del os
        # Update All Data In The Object With Parameters
        self.title = title
        self.domain = domain
        self.icon = icon

    def upload_post(self, post: HangerPost) -> Path:
        output = Path(f"post_{hash(post)}.html")
        output.write_text(post.give_HTML("hanger.css"), encoding="utf-8")
        return output

    def send_message(
        self,
        receiver: Profile,
        message: str,
        images: Optional[List[str]] = None,
    ) -> HangerMessage:
        chat = HangerMessage()
        chat.sender = self.logged_user
        chat.receiver = receiver
        chat.send(message, images)
        return chat

    def make_group(
        self,
        members: List[Profile],
        message: str,
        images: Optional[List[str]] = None,
    ) -> List[HangerMessage]:
        return [self.send_message(member, message, images) for member in members]

    @staticmethod
    def give_like(post: HangerPost) -> None:
        post.likes += 1

    def write_comment(self, content: HangerPost):
        '''
            Add New Comment To 
            post comments list.
        '''
        content.comments.append(f"<h3>{self.logged_user.name}<h3><div class = 'comment'>{content.give_HTML('hanger.css')}</div")
