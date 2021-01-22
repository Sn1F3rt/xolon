from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from time import sleep
import datetime
from xolon.blueprints.auth import auth_bp
from xolon.forms import Register, Login, Delete
from xolon.models import User
from xolon.factory import db, bcrypt
from xolon.library.docker import docker
from xolon.library.helpers import capture_event
from xolon.token import generate_confirmation_token, confirm_token
from xolon.email import send_email


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = Register()
    if current_user.is_authenticated:
        flash('Already registered and authenticated.')
        return redirect(url_for('wallet.dashboard'))

    if form.validate_on_submit():
        # Check if email already exists
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('This email is already registered.')
            return redirect(url_for('auth.login'))

        # Save new user
        user = User(
            email=form.email.data,
            password=bcrypt.generate_password_hash(form.password.data).decode('utf8'),
            confirmed=False,
        )
        db.session.add(user)
        db.session.commit()

        token = generate_confirmation_token(user.email)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        html = render_template('auth/activate.html', confirm_url=confirm_url)
        subject = "Please confirm your email"
        send_email(user.email, subject, html)

        # Capture event, login user and redirect to wallet page
        capture_event(user.id, 'register')
        login_user(user)

        flash('A confirmation email has been sent via email.', 'success')
        return redirect(url_for('auth.unconfirmed'))

    return render_template("auth/register.html", form=form)


@auth_bp.route('/confirm/<token>')
@login_required
def confirm_email(token):
    # noinspection PyBroadException
    try:
        email = confirm_token(token)
    except:
        return flash('The confirmation link is invalid or has expired.', 'danger')

    user = User.query.filter_by(email=email).first_or_404()

    if user.confirmed:
        flash('Account already confirmed.', 'success')

    else:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have confirmed your account. Thanks!', 'success')

    return redirect(url_for('auth.login'))


@auth_bp.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect('wallet.dashboard')
    return render_template('auth/unconfirmed.html')


@auth_bp.route('/resend')
@login_required
def resend_confirmation():
    token = generate_confirmation_token(current_user.email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('auth/activate.html', confirm_url=confirm_url)
    subject = "Please confirm your email"
    send_email(current_user.email, subject, html)
    flash('A new confirmation email has been sent.', 'success')
    return redirect(url_for('auth.unconfirmed'))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = Login()
    if current_user.is_authenticated:
        flash('Already registered and authenticated.')
        return redirect(url_for('wallet.dashboard'))

    if form.validate_on_submit():
        # Check if user doesn't exist
        user = User.query.filter_by(email=form.email.data).first()
        if not user:
            flash('Invalid username or password.')
            return redirect(url_for('auth.login'))

        # Check if password is correct
        password_matches = bcrypt.check_password_hash(
            user.password,
            form.password.data
        )
        if not password_matches:
            flash('Invalid username or password.')
            return redirect(url_for('auth.login'))

        # Capture event, login user, and redirect to wallet page
        capture_event(user.id, 'login')
        login_user(user)
        return redirect(url_for('wallet.dashboard'))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
def logout():
    if current_user.is_authenticated:
        docker.stop_container(current_user.wallet_container)
        capture_event(current_user.id, 'stop_container')
        current_user.clear_wallet_data()
        capture_event(current_user.id, 'logout')
        logout_user()
    return redirect(url_for('meta.index'))


@auth_bp.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    form = Delete()
    if form.validate_on_submit():
        docker.stop_container(current_user.wallet_container)
        capture_event(current_user.id, 'stop_container')
        sleep(1)
        docker.delete_wallet_data(current_user.id)
        capture_event(current_user.id, 'delete_wallet')
        current_user.clear_wallet_data(reset_password=True, reset_wallet=True)
        flash('Successfully deleted wallet data')
        return redirect(url_for('wallet.setup'))
    else:
        flash('Please confirm deletion of the account')
        return redirect(url_for('wallet.dashboard'))
