from pydantic import BaseModel

class Victim(BaseModel):
    token: str
    name: str
    surname: str
    email: str
    status: str
    department: str

class UserGroup(BaseModel):
    name: str
    description: str
    members: list

class EmailTemplate(BaseModel):
    name: str
    subject: str
    body: str

class LandingPage(BaseModel):
    name: str
    url: str
    user_group: str
    email_template: str
    landing_page: str
    sending_profile: str

class SendingProfile(BaseModel):
    name: str
    smtp_server: str
    port: int
    username: str
    password: str

class Campaign(BaseModel):
    name: str
    user_group: str
    email_template: str
    landing_page: str
    sending_profile: str