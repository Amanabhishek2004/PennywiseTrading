from sqlalchemy import event
from sqlalchemy.orm import Session
from ..models   import * # Import your models

# Function to create a UserProfile when a new User is added
def create_user_profile(mapper, connection, target):
    session = Session(bind=connection)
    profile = UserProfile(user_id=target.id)
    session.add(profile)
    session.commit()

# Register the event listener for the "User" model
event.listen(User, "after_insert", create_user_profile)