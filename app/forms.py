from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from flask_login import current_user
from wtforms import StringField, PasswordField, SubmitField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from app.models import User

# Create classes that will represent forms for our HTML files
# We crete the classes, and they inherit from the FlaskFrom class, thats why we pass it in the paranthesis


# Class for the registration form

class RegistrationForm(FlaskForm):
    username = StringField('Nome de Usuário', validators = [DataRequired(), Length(min=2, max=20)])
    email = StringField('Email', validators = [DataRequired(), Email()])
    password = PasswordField('Senha', validators = [DataRequired()])
    confirm_password = PasswordField('Confirme a sua senha', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Registrar-se')


    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('Já existe uma conta com este nome de usuário.')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Já existe uma conta registrada com este e-mail.')
        if not email.data.endswith('@fatec.sp.gov.br'):
            raise ValidationError('O e-mail precisa terminar com @fatec.sp.gov.br.')


# Class for the login form

class LoginForm(FlaskForm):
    email = StringField('E-mail', validators = [DataRequired(), Email()])
    password = PasswordField('Senha', validators = [DataRequired()])
    remember = BooleanField('Lembrar-se de mim')
    submit = SubmitField('Login')


# Class for the update profile form

class UpdateAccountForm(FlaskForm):
    username = StringField('Nome de Usuário', validators = [DataRequired(), Length(min=2, max=20)])
    email = StringField('E-mail', validators = [DataRequired(), Email()])
    picture = FileField('Atualizar foto', validators = [FileAllowed(['jpg', 'png', 'jpeg'])])
    submit = SubmitField('Atualizar')

    def validate_username(self, username):
        # If the user changes their username, query the database to see if the new username is already taken
        if username.data != current_user.username:
            user = User.query.filter_by(username=username.data).first()
            if user:
                raise ValidationError('Já existe uma conta com este nome de usuário.')
    def validate_email(self, email):
        # If the user changes their email, query the database to see if the new email is already taken
        if email.data != current_user.email:
            user = User.query.filter_by(email=email.data).first()
            if user:
                raise ValidationError('Já existe uma conta registrada com este e-mail.')


class PostForm(FlaskForm):
    title = StringField('Título', validators = [DataRequired()])
    content = TextAreaField('Conteúdo', validators = [DataRequired()])
    submit = SubmitField('Post')


class RequestResetForm(FlaskForm):
    email = StringField('E-mail', validators = [DataRequired(), Email()])
    submit = SubmitField('Solicitar redefinição de senha')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('Não existe uma conta com o e-mail informado. Você precisa se cadastrar.')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Nova Senha', validators = [DataRequired()])
    confirm_password = PasswordField('Confirmar Nova Senha', validators = [DataRequired(), EqualTo('password')])
    submit = SubmitField('Enviar')