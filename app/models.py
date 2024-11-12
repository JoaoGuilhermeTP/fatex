from app import db, login_manager, app
from flask_login import UserMixin
from datetime import datetime
from itsdangerous.url_safe import URLSafeTimedSerializer as Serializer

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)
    
    # Esse método gera um token contendo o id do usuário
    def get_reset_token(self):
        #  cria um objeto Serializer usando uma chave secreta da configuração do app, garantindo que o conteúdo do token não possa ser alterado por alguém sem essa chave
        s = Serializer(app.config['SECRET_KEY'])
        # serializa (criptografa) o dicionário {'user_id': self.id} em um formato de token. self.id se refere ao ID do usuário que está chamando o método, associando o token a um usuário específico
        return s.dumps({'user_id' : self.id})
    
    # Esse método decodifica e verifica o token para recuperar o ID do usuário.
    def verify_reset_token(token):
        # Cria uma instância de Serializer usando a mesma chave secreta, para que possa decodificar corretamente tokens gerados pelo get_reset_token
        s = Serializer(app.config['SECRET_KEY'])
        try:
            # Tenta descriptografar e decodificar o token, extraindo o user_id dele
            user_id = s.loads(token)['user_id']
        except:
            # Se a decodificação falhar (devido a uma manipulação do token ou expiração), ele lança uma exceção e retorna None
            return None
        # Se for bem-sucedido, ele recupera e retorna o usuário com aquele ID do banco de dados
        return User.query.get(user_id)
    
    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.username}')"
    
class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default = datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"