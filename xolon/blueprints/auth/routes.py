from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from time import sleep
import datetime
import requests
from xolon.blueprints.auth import auth_bp
from xolon.forms import Register, Login, Delete, Reset, ResetPassword
from xolon.models import User
from xolon.factory import db, bcrypt, policy
from xolon.library.docker import docker
from xolon.library.helpers import capture_event
from xolon.token import generate_token, validate_token
from xolon.email import send_email


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = Register()
    if current_user.is_authenticated:
        return redirect(url_for('wallet.dashboard'))

    if form.validate_on_submit():
        redirect_url = url_for('auth.register') + '#register'

        # Check if email already exists
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            flash('This email is already registered.')
            return redirect(url_for('auth.login'))

        # Check and block temporary email addresses
        r = requests.get(f'https://block-temporary-email.com/check/email/{form.email.data}')

        if r.status_code == 200:
            if r.json()['temporary']:
                flash('Registrations with temporary disposable emails are not allowed on Xolon, '
                      'as they pose a substantial risk to a user\'s funds. Please take two '
                      'minutes to register a valid email address and try again, remember, not '
                      'your keys, not your crypto!')

                return redirect(redirect_url)
        else:
            pass

        # Check if password contains whitespaces
        if ' ' in form.password.data:
            flash('Password cannot have whitespaces!')
            return redirect(redirect_url)

        # Test password policy
        if len(policy.test(form.password.data)) != 0:
            flash('Password must be at least 8 characters, and must contain '
                  'at least one uppercase, one lowercase, one digit and a symbol.')
            return redirect(redirect_url)

        # Check if passwords match
        if not form.password.data == form.confirm_password.data:
            flash('Passwords do not match!')
            return redirect(redirect_url)

        # Save new user
        user = User(
            email=form.email.data,
            password=bcrypt.generate_password_hash(form.password.data).decode('utf8'),
            confirmed=False,
        )
        db.session.add(user)
        db.session.commit()

        # Generate confirmation token and send email
        token = generate_token(user.email)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        html = render_template('auth/email/activate.html', confirm_url=confirm_url)
        subject = 'Xolon : Account Activation'
        send_email(user.email, subject, html)

        # Capture event, login user and redirect to unconfirmed page
        capture_event(user.id, 'register')
        login_user(user)

        flash('A confirmation email has been sent via email.')
        return redirect(url_for('auth.unconfirmed'))

    return render_template("auth/register.html", form=form)


@auth_bp.route('/confirm/<token>')
@login_required
def confirm_email(token):
    # noinspection PyBroadException
    # Validate token
    email = validate_token(token)

    if not email or not User.query.filter_by(email=email).first():
        flash('The confirmation link is either invalid or has expired.')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first()

    # Check if the user has already confirmed his account
    if user.confirmed:
        flash('Account already confirmed.')

    else:
        # Confirm user account, capture event and redirect to wallet setup
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()

        capture_event(user.id, 'confirmed')
        flash('You have successfully confirmed your account!')

    return redirect(url_for('wallet.setup'))


@auth_bp.route('/unconfirmed')
@login_required
def unconfirmed():
    # Check if user is already confirmed
    if current_user.confirmed:
        return redirect('wallet.setup')

    return render_template('auth/unconfirmed.html')


@auth_bp.route('/resend')
@login_required
def resend_confirmation():
    # Re-generate token and send email
    token = generate_token(current_user.email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('auth/email/activate.html', confirm_url=confirm_url)
    subject = 'Xolon : Account Activation'
    send_email(current_user.email, subject, html)
    flash('A new confirmation email has been sent.')

    # Capture event and redirect to unconfirmed page
    capture_event(current_user.id, 'resend_confirm_email')
    return redirect(url_for('auth.unconfirmed'))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = Login()

    # Check if user is already authenticated
    if current_user.is_authenticated:
        return redirect(url_for('wallet.setup'))

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
            flash('Invalid email or password.')
            return redirect(url_for('auth.login'))

        # Capture event, login user, and redirect to wallet page
        capture_event(user.id, 'login')
        login_user(user)
        return redirect(url_for('wallet.dashboard'))

    return render_template("auth/login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    if current_user.is_authenticated:
        # Stop container, capture events, and logout user
        docker.stop_container(current_user.wallet_container)
        capture_event(current_user.id, 'stop_container')
        current_user.clear_wallet_data()
        capture_event(current_user.id, 'logout')
        logout_user()

    return redirect(url_for('meta.index'))


@auth_bp.route('/reset', methods=["GET", "POST"])
def reset():
    form = Reset()

    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()

        # Check if a user with the specified email exists
        if not user:
            flash('No such email exists in our database.')
            return redirect(url_for('auth.reset'))

        # Check if the user has confirmed their email yet
        if not user.confirmed:
            flash('Please confirm your email first.')
            return redirect(url_for('auth.reset'))

        # Generate reset token
        token = generate_token(user.email)
        reset_url = url_for('reset_with_token', token=token, _external=True)
        html = render_template('auth/email/reset_password.html', reset_url=reset_url)
        subject = ' Xolon : Reset Password'
        send_email(user.email, subject, html)

        # Capture event and redirect to home page
        flash('An email with a link to reset your password has been sent to your inbox.')
        capture_event(user.id, 'pass_reset_email_sent')
        return redirect(url_for('meta.index'))

    return render_template('auth/reset.html', form=form)


@auth_bp.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    # Validate reset token
    email = validate_token(token)

    if not email:
        flash('The reset password link is either invalid or has expired.')

    form = ResetPassword()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()

        # Change user password
        user.password = bcrypt.generate_password_hash(form.password.data).decode('utf8')

        db.session.add(user)
        db.session.commit()

        # Capture event and redirect user to login page
        flash('Your password has been changed successfully!')
        capture_event(user.id, 'pass_change')
        return redirect(url_for('auth.login'))

    return render_template('auth/change_password.html', form=form, token=token)


@auth_bp.route("/delete", methods=["GET", "POST"])
@login_required
def delete():
    form = Delete()
    if form.validate_on_submit():
        # Stop container, delete wallet data, capture event, and redirect to wallet setup
        docker.stop_container(current_user.wallet_container)
        capture_event(current_user.id, 'stop_container')
        sleep(1)
        docker.delete_wallet_data(current_user.id)
        capture_event(current_user.id, 'delete_wallet')
        current_user.clear_wallet_data(reset_password=True, reset_wallet=True)
        flash('Successfully deleted wallet data')
        return redirect(url_for('wallet.setup'))
    else:
        flash('Please confirm deletion of the account!')
        return redirect(url_for('wallet.dashboard'))
