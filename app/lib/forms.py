from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, PasswordField, SubmitField, BooleanField, DateField
from wtforms.validators import DataRequired, Length

class LoginForm(FlaskForm):
    """ Inputs for login form, i.e. username and password. """
    email = StringField('Email', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember = BooleanField('Remember Me')
    submit = SubmitField('Login')


class UpdateProfileForm(FlaskForm):
    """ Lets users update first and last name. """
    from app.main import db, mongo_db
    picture = FileField('Update profile picture', validators=[FileAllowed(['jpg', 'png'])])
    first_name = StringField("First name", validators=[Length(min=2, max=50)])
    last_name = StringField("Last name", validators=[Length(min=2, max=50)])
    date_registered = DateField('Member since', render_kw={'readonly': True})
    submit = SubmitField('Update')
