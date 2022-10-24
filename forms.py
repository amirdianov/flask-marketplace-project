from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError


class LoginForm(FlaskForm):
    email = StringField("Email: ", validators=[DataRequired(), Email("Incorrect email")])
    password = PasswordField("Password: ", validators=[DataRequired()])

    def validate_password(form, field):
        if len(field.data) > 100 or len(field.data) < 4:
            raise ValidationError('Name must be less than 100 and more than 4 symbols')

    remember = BooleanField("Remember me: ", default=False)
    submit = SubmitField("Sign in")


class RegistrationForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100,
                                                                  message="Имя должно содержать не менее одного символа")])
    email = StringField('Email: ', validators=[DataRequired(), Email("Некорректный email")])
    password = PasswordField('Password: ', validators=[DataRequired(),
                                                       Length(min=4, max=100,
                                                              message="Пароль должен быть от 4 до 100 символов")])
    password2 = PasswordField("Again password: ",
                              validators=[DataRequired(), EqualTo('password', message="Пароли не совпадают")])
    submit = SubmitField('Sign up')
