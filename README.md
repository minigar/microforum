# flask_microblog

commands to start
python -m smtpd -n -c DebuggingServer localhost:8025 # virtual email 
export FLASK_APP=run.py
export MAIL_SERVER=localhost
export MAIL_PORT=8025
FLASK_APP=run flask run --reload


for me ^<:^:>^
if i want up to date database:(when i change someone in models.py)
flask db stamp head
flask db migrate
flask db upgrade