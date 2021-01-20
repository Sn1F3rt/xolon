from flask import request, render_template, session, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from time import sleep
from xolon.blueprints.auth import auth_bp
from xolon.forms import Register, Login, Delete
from xolon.models import User
from xolon.factory import db, bcrypt
from xolon.library.docker import docker
from xolon.library.helpers import capture_event


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
        )
        db.session.add(user)
        db.session.commit()

        # Capture event, login user and redirect to wallet page
        capture_event(user.id, 'register')
        login_user(user)
        return redirect(url_for('wallet.setup'))

    return render_template("auth/register.html", form=form)


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
