from typing import Dict
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends, Request
from jose import JWTError, jwt
from pymongo import MongoClient
from dynaconf import Dynaconf
import logging
from typing import List

logging.basicConfig(level=logging.INFO)

# Initialize Dynaconf with settings from settings.toml
try:
    settings = Dynaconf(settings_file="settings.toml")
except Exception as e:
    logging.error(f"Failed to load settings from settings.toml: {e}")
    raise

class AuthHandler:
    def __init__(self):
        self.secret_key = settings.jwt.secret_key
        self.algorithm = settings.jwt.algorithm
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        self.client = MongoClient(settings.database.uri)
        self.db = self.client[settings.database.database]  # Note: Fixed key to `database`
        self.users_collection = self.db['users']
        self.sessions_collection = self.db['sessions']
        self.initialize_admin_user()  # Ensure admin user is initialized

    def create_access_token(self, data: Dict[str, str]):
        encoded_jwt = jwt.encode(data, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt

    def verify_password(self, plain_password: str, hashed_password: str):
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)

    def authenticate_user(self, username: str, password: str):
        user = self.users_collection.find_one({"username": username})
        if not user or not self.verify_password(password, user.get('password', '')):
            return False
        return user

    def store_session_token(self, token: str, username: str):
        self.sessions_collection.update_one(
            {"username": username},
            {"$set": {"token": token}},
            upsert=True
        )

    def remove_session_token(self, token: str):
        self.sessions_collection.delete_one({"token": token})

    def get_current_user(self, token: str):
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            username: str = payload.get("sub")
            if username is None:
                raise credentials_exception
            user = self.users_collection.find_one({"username": username})
            if user is None:
                raise credentials_exception
            return user
        except JWTError:
            raise credentials_exception

    def initialize_admin_user(self):
        admin_username = "admin"
        admin_password = "admin123"  # Default password, consider using a more secure method
        admin_user = self.users_collection.find_one({"username": admin_username})

        if not admin_user:
            hashed_password = self.get_password_hash(admin_password)
            self.users_collection.insert_one({
                "username": admin_username,
                "password": hashed_password,
                "role": "admin"
            })
            logging.info("Admin user created.")
        else:
            logging.info("Admin user already exists.")

    def is_admin(self, username: str) -> bool:
        user = self.users_collection.find_one({"username": username})
        if user and user.get("role") == "admin":
            return True
        return False

    def is_authenticated(self, username: str) -> bool:
        user = self.users_collection.find_one({"username": username})
        if user and user.get("role") is not None:
            return True
        return False