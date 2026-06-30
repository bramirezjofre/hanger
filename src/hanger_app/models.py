from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Application:
    id: int
    username: Optional[str]
    contact_address: str
    contact_kind: str
    answers: dict
    reviewer_notes: Optional[str]
    reviewer_id: Optional[int]
    status: str
    interview_contact_method: Optional[str]
    interview_preferred_times: Optional[str]
    interviewer_id: Optional[int]
    interviewer_username: Optional[str]
    interview_status: str
    decided_at: Optional[int]
    created_at: int
    updated_at: int


@dataclass(frozen=True)
class InterviewNote:
    id: int
    application_id: int
    author_id: Optional[int]
    author_username: Optional[str]
    category: str
    content: str
    created_at: int


@dataclass(frozen=True)
class InstallationSetting:
    key: str
    value: object
    is_public: bool
    updated_at: int


@dataclass(frozen=True)
class User:
    id: int
    username: str
    password_hash: str
    age: Optional[int]
    contact_kind: Optional[str]
    contact_address: Optional[str]
    role: str


@dataclass(frozen=True)
class Job:
    id: int
    kind: str
    payload: dict
    attempts: int
    lease_id: str


@dataclass(frozen=True)
class Message:
    id: int
    sender: str
    receiver: str
    content: str
    created_at: int


@dataclass(frozen=True)
class Post:
    id: int
    author: str
    content: str
    created_at: int
