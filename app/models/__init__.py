# Import Base and User from base models
from .base import Base as Base, User as User

# Import messaging models to register them with SQLAlchemy
from . import messaging as messaging
