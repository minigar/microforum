from flask  import render_template
from app import app, db
from flask_babel import _

# regist decorate func as route for erroe404
@app.errorhandler(404)
def not_found_error(error):
    return render_template('error404.html', title='404 Error'), 404


@app.errorhandler(500)
def internal_error(error):
    db.session.rollback()
    return render_template('error500.html', title='500 Internal Error'), 500