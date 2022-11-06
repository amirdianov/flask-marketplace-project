from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, IntegerField, TextAreaField, FileField, \
    SelectField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError


class LoginForm(FlaskForm):
    email = StringField("Email: ", validators=[DataRequired(), Email("Incorrect email")])
    password = PasswordField("Password: ", validators=[DataRequired(), Length(min=4, max=100,
                                                                              message="Пароль от 4 до 100 символов")])

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


class MakeOrder(FlaskForm):
    name = StringField('Name', validators=[DataRequired(), Length(min=1, max=100,
                                                                  message="Имя должно содержать не менее одного символа")])
    address = StringField('Address', validators=[DataRequired()])


class ProfileForm(FlaskForm):
    email = StringField('Email: ', validators=[DataRequired(), Email("Некорректный email")])
    password = PasswordField('Password: ')
    password2 = PasswordField("Again password: ",
                              validators=[EqualTo('password', message="Пароли не совпадают")])
    submit = SubmitField('Edit')


class AddEditProduct(FlaskForm):
    product_name = StringField('Name product: ', validators=[DataRequired()])
    price = IntegerField('Price:', validators=[DataRequired()])
    text_info = TextAreaField('Information', validators=[DataRequired()])
    category = SelectField('Select category')
    count = IntegerField('Count:', validators=[DataRequired()])
    submit = SubmitField('Confirm')
    image = FileField('Image', validators=[])
