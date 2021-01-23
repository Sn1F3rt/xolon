from flask import render_template, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from time import sleep
import datetime
from xolon.blueprints.auth import auth_bp
from xolon.forms import Register, Login, Delete, Reset, ResetPassword
from xolon.models import User
from xolon.factory import db, bcrypt
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

        token = generate_token(user.email)
        confirm_url = url_for('auth.confirm_email', token=token, _external=True)
        html = render_template('auth/email/activate.html', confirm_url=confirm_url)
        subject = 'Xolon : Account Activation'
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
        email = validate_token(token)
    except:
        flash('The confirmation link is either invalid or has expired.')
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(email=email).first_or_404()

    if user.confirmed:
        flash('Account already confirmed.')

    else:
        user.confirmed = True
        user.confirmed_on = datetime.datetime.now()
        db.session.add(user)
        db.session.commit()
        flash('You have successfully confirmed your account!')

    return redirect(url_for('wallet.setup'))


@auth_bp.route('/unconfirmed')
@login_required
def unconfirmed():
    if current_user.confirmed:
        return redirect('wallet.dashboard')
    return render_template('auth/unconfirmed.html')


@auth_bp.route('/resend')
@login_required
def resend_confirmation():
    token = generate_token(current_user.email)
    confirm_url = url_for('auth.confirm_email', token=token, _external=True)
    html = render_template('auth/email/activate.html', confirm_url=confirm_url)
    subject = 'Xolon : Account Activation'
    send_email(current_user.email, subject, html)
    flash('A new confirmation email has been sent.')
    return redirect(url_for('auth.unconfirmed'))


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = Login()
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

        if not user:
            flash('No such email exists in our database.')
            return redirect(url_for('auth.reset'))

        if not user.confirmed:
            flash('Please confirm your email first.')
            return redirect(url_for('auth.reset'))

        token = generate_token(user.email)
        reset_url = url_for('reset_with_token', token=token, _external=True)
        html = render_template('auth/email/reset_password.html', reset_url=reset_url)
        subject = 'Xolon : Reset Password'
        send_email(user.email, subject, html)

        flash('An email with a link to reset your password has been sent to your inbox.')
        return redirect(url_for('meta.index'))

    return render_template('auth/reset.html', form=form)


@auth_bp.route('/reset/<token>', methods=["GET", "POST"])
def reset_with_token(token):
    email = validate_token(token)

    if not email:
        flash('The reset password link is either invalid or has expired.')

    form = ResetPassword()

    if form.validate_on_submit():
        user = User.query.filter_by(email=email).first()

        user.password = bcrypt.generate_password_hash(form.password.data).decode('utf8')

        db.session.add(user)
        db.session.commit()

        flash('Your password has been changed successfully!')

        return redirect(url_for('auth.login'))

    return render_template('auth/change_password.html', form=form, token=token)


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
