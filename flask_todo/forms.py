from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, DateTimeField, FileField, StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Length, EqualTo, ValidationError
from flask_wtf.file import FileAllowed
from models import User
from datetime import datetime

class TodoForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    description = TextAreaField('Description')
    time = DateTimeField('Date & Time', format='%Y-%m-%d %H:%M', validators=[DataRequired()], default=datetime.now)
    image = FileField('Image', validators=[FileAllowed(['jpg', 'png', 'jpeg'])])


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired(), Length(min=4, max=25)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Username is already in use. Please choose a different one.')