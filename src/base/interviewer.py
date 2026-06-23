"""Compatibility imports for the original interviewer module.

New code should use services from :mod:`hanger_app.services` through the Flask
application factory.
"""

from hanger_app.services import AuthService as HangerSteps
from hanger_app.services import InvitationService as LoadUser

loadUser = LoadUser
__all__ = ["HangerSteps", "LoadUser", "loadUser"]
