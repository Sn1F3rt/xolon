from re import match as re_match
from flask_wtf import FlaskForm
from wtforms import StringField, BooleanField
from wtforms.validators import DataRequired, Optional, Email, EqualTo, ValidationError


class Register(FlaskForm):
    email = StringField('Email Address:', validators=[DataRequired(), Email()],
                        render_kw={"placeholder": "Email", "class": "form-control", "type": "email"})
    password = StringField('Password:', validators=[DataRequired()],
                           render_kw={"placeholder": "Password", "class": "form-control", "type": "password"})
    confirm = StringField('Password:', validators=[DataRequired(),
                                                   EqualTo('password', message='Passwords must match.')],
                          render_kw={"placeholder": "Confirm Password", "class": "form-control", "type": "password"})
    faq_reviewed = BooleanField('FAQ Reviewed:', validators=[DataRequired()],
                                render_kw={"class": "form-control-span"})
    terms_reviewed = BooleanField('Terms of Service Reviewed:', validators=[DataRequired()],
                                  render_kw={"class": "form-control-span"})
    privacy_reviewed = BooleanField('Privacy Policy Reviewed:', validators=[DataRequired()],
                                    render_kw={"class": "form-control-span"})


class Login(FlaskForm):
    email = StringField('Email Address:', validators=[DataRequired()],
                        render_kw={"placeholder": "Email", "class": "form-control", "type": "email"})
    password = StringField('Password:', validators=[DataRequired()],
                           render_kw={"placeholder": "Password", "class": "form-control", "type": "password"})


class Reset(FlaskForm):
    email = StringField('Email Address:', validators=[DataRequired(), Email()],
                        render_kw={"placeholder": "Email", "class": "form-control", "type": "email"})


class ResetPassword(FlaskForm):
    password = StringField('Password:', validators=[DataRequired()],
                           render_kw={"placeholder": "New Password", "class": "form-control", "type": "password"})
    confirm = StringField('Password:', validators=[DataRequired(),
                                                   EqualTo('password', message='Passwords must match.')],
                          render_kw={"placeholder": "Confirm Password", "class": "form-control", "type": "password"})


class Restore(FlaskForm):
    seed = StringField('Seed Phrase', validators=[DataRequired()],
                       render_kw={"placeholder": "25 word mnemonic seed phrase", "class": "form-control"})
    risks_accepted = BooleanField('I agree:', validators=[DataRequired()],
                                  render_kw={"class": "form-control-span"})

    # noinspection PyUnusedLocal
    def validate_seed(self, seed):
        regex = '^[\\w\\s]+$'
        if bool(re_match(regex, self.seed.data)) is False:
            raise ValidationError('Invalid seed provided; must be alpha-numeric characters only')
        if len(self.seed.data.split()) != 25:
            raise ValidationError("Invalid seed provided; must be standard Xolentum 25 word format")


class Send(FlaskForm):
    address = StringField('Destination Address:', validators=[DataRequired()],
                          render_kw={"placeholder": "Xolentum address", "class": "form-control"})
    amount = StringField('Amount:', validators=[DataRequired()],
                         render_kw={"placeholder": "Amount to send or \"all\"", "class": "form-control"})
    payment_id = StringField('Payment ID (Optional):', validators=[Optional()],
                             render_kw={"placeholder": "16 or 32 character payment ID", "class": "form-control"})


class Delete(FlaskForm):
    confirm = BooleanField('Confirm Wallet Deletion:', validators=[DataRequired()],
                           render_kw={"class": "form-control-span"})
