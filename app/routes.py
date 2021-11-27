# -*- coding: utf-8 -*-
# imports
from flask import *
from flask_login import current_user, login_user, logout_user, login_required
from werkzeug.urls import url_parse
from app.models import User, Post, followers
from app.forms import EditProfileForm
from app import app, db
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm, EmptyForm, DeletePostForm
from app.email import send_password_reset_email
from datetime import datetime
from app.forms import PostForm 
from flask_babel import _, get_locale


# create a var (if user is logged in) what include user's last seen
@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.utcnow()
        db.session.commit()
    g.locale = str(get_locale())


# regist decorate func as route
@app.route('/index', methods=['GET', 'POST'])
@app.route('/', methods=['GET', 'POST'])
@login_required
def index():
    print('')
    print('')
    print(current_user.is_authenticated)
    print(url_for('index'))
    

    form = PostForm()
    
    if form.validate_on_submit():
        post = Post(body=form.post.data, author=current_user)
    
        db.session.add(post)
        db.session.commit()
    
        return redirect(url_for('index'))
    
    page = request.args.get('page', 1, type=int)
    
    posts = current_user.followed_posts().paginate(page, app.config['POSTS_PER_PAGE'], False)
    
    next_url = url_for('index', page=posts.next_num) if posts.has_next else None
    
    prev_url = url_for('index', page=posts.prev_num) if posts.has_prev else None
    
    return render_template('index.html', form = form, posts = posts.items, next_url = next_url, prev_url = prev_url, title='General')



# regist decorate func as route
@app.route('/static/<path:path>')
def send_js(path):
    return send_from_directory('static', path)


# regist decorate func as route
@app.route('/login', methods=['GET', 'POST'])
def login():
    print()
    print()
    print(url_for('login'))    
    print(request.form)
    print(current_user.is_authenticated)

    if current_user.is_authenticated:
        return redirect(url_for('index'))

    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()

        if user is None or not user.check_password(form.password.data):
            flash(_('Invalid username or password'))
            return redirect(url_for('login'))

        print('login_user:', login_user(user, remember=form.remember_me.data))
        next_url = request.args.get('next')

        if not next_url or url_parse(next_url).netloc != '':
            next_url = url_for('index')

        return redirect(next_url)

    return render_template('login.html', form=form, title='Sign in')


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = ResetPasswordRequestForm()
    
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        
        if user:
            send_password_reset_email(user)
        flash(_('Check your email for the instructions to reset your password'))
        return redirect(url_for('login'))
    return render_template('reset_password_request.html', form = form, title = 'Reset Password')


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    print()
    print()
    print(url_for('reset_password', token=token))
    
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    user = User.verify_reset_password_token(token)
    
    if not user:
        return redirect(url_for('index'))
    
    form = ResetPasswordForm()
    
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


# regist decorate func as route
@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


# regist decorate func as route
@app.route('/register', methods=['GET', 'POST'])
def register():
    print()
    print()
    print(url_for('register'))
    print(request.form)

    if current_user.is_authenticated:
        return redirect(url_for('user', username = current_user.username))

    form = RegistrationForm()

# here we add user's name, password hash in db # email don't use yet
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()

        flash('Congratulations, you are now a registered user!')

        return redirect(url_for('login'))

    return render_template('register.html', form = form, title = 'Register')


# regist decorate func as route for user's profile page
@app.route('/user/<username>')
@login_required
def user(username):
    print('')
    print('')
    print( url_for('user', username=username))

    # serch a user in db
    user = User.query.filter_by(username=username).first_or_404()
    page = request.args.get('page', 1, type=int)
    posts = user.posts.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    
    next_url = url_for('user', username=user.username, page=posts.next_num) if posts.has_next else None
    
    prev_url = url_for('user', username=user.username, page=posts.prev_num) if posts.has_prev else None

    form = EmptyForm()

    return render_template('user.html', user = user, posts = posts.items, next_url = next_url, prev_url = prev_url, form = form, title='Profile')


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    print()
    print()
    print(url_for('edit_profile'))
    print(current_user.is_authenticated)
    
    form = EditProfileForm(current_user.username)
    
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
    
        flash('Your changes have been saved.')
    
        return redirect(url_for('edit_profile'))
    
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me

    return render_template('edit_profile.html', form=form, title='Edit Profile')


@app.route('/follow/<username>', methods=['POST'])
@login_required
def follow(username):
    form = EmptyForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=username).first()
        if user is None:
            flash(_('User %(username)s not found.', username=username))
            return redirect(url_for('index'))
        if user == current_user:
            flash('You cannot follow yourself!')
            return redirect(url_for('user', username=username))
        current_user.follow(user)
        db.session.commit()
        flash('You are following {}!'.format(username))
        return redirect(url_for('user', username=username))
    else:
        return redirect(url_for('index'))


@app.route('/unfollow/<username>', methods=['POST'])
@login_required
def unfollow(username):
    print()
    print()

    user = User.query.filter_by(username=username).first()
    
    if user is None:
        flash(f'User {username} not found')
        return redirect(url_for('index'))
    
    if user == current_user:
        flash('You cannot unfollow yourself')
        return redirect(url_for('user', username=username))
    current_user.unfollow(user)
    db.session.commit()
    flash(f'You are not following {username}')
    return redirect(url_for('user', username = username))


@app.route('/explore')
@login_required
def explore():
    print()
    print()
    
    page = request.args.get('page', 1, type=int)
    posts = Post.query.order_by(Post.timestamp.desc()).paginate(
        page, app.config['POSTS_PER_PAGE'], False)
    
    next_url = url_for('explore', page=posts.next_num)     if posts.has_next else None # next_num is num for next page  has_next is metod what check if have next page after that
    prev_url = url_for('explore', page=posts.prev_num)     if posts.has_prev else None # prev_num is num for next page  has_prev is metod what check if have prev page prev that
    
    return render_template('index.html', posts=posts.items, next_url = next_url, prev_url = prev_url, title='Explore')


@app.route('/delete_post', methods=['POST', 'GET'])
@login_required
def delete_post():
    form = DeletePostForm()
    post = Post.query.filter_by(body = form.post.data).first()

    if form.validate_on_submit():

        if not post:
            flash('not found this post')
            return redirect(url_for('delete_post'))

        if post.author == current_user:
            db.session.delete(post)
            db.session.commit()

            return redirect(url_for('index'))
    return render_template('delete_post.html', post = post, title='Delete Post', form = form)


# call general func
if __name__ == '__main__':
    app.run(debug=True)

