from base.user import HangerApp, HangerMessage, HangerPost, Profile


def test_message_keeps_complete_text_and_escapes_html():
    message = HangerMessage()
    rendered = message.send("<script>alert(1)</script>", ["../avatar.png"])

    assert message.chat_messages == ["<script>alert(1)</script>"]
    assert "<script>" not in rendered
    assert "&lt;script&gt;" in rendered
    assert "../" not in rendered


def test_post_escapes_content_and_comments():
    post = HangerPost()
    post.content = "<img src=x onerror=alert(1)>"
    post.comments = ["<script>alert(1)</script>"]

    rendered = post.give_HTML("hanger.css")

    assert "onerror=alert(1)>" not in rendered
    assert "&lt;img" in rendered
    assert "&lt;script&gt;" in rendered


def test_app_sends_messages_without_flask_globals():
    app = HangerApp()
    app.logged_user.name = "Alice"
    receiver = Profile()
    receiver.name = "Bob"

    chat = app.send_message(receiver, "Hello")

    assert chat.sender.name == "Alice"
    assert chat.receiver.name == "Bob"
    assert chat.chat_messages == ["Hello"]
