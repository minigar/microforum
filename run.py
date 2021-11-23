#imports
from app import app, db
from app.models import User, Post, followers
from app import routes

#decorator for function for shell. can use this varrinable and classes what write  in this function
@app.shell_context_processor
def make_shell_context():
    return {'db': db, 'User': User, 'Post': Post, 'followers': followers}