"""Compatibility imports for the original domain module.

New code should import these records from :mod:`hanger_app.models`.
"""

from hanger_app.models import Message as HangerMessage
from hanger_app.models import Post as HangerPost
from hanger_app.models import User as Profile

__all__ = ["HangerMessage", "HangerPost", "Profile"]
