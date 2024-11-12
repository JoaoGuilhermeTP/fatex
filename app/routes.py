import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request,abort
from app import app, db, bcrypt, mail
from app.forms import RegistrationForm, LoginForm, UpdateAccountForm, PostForm, RequestResetForm, ResetPasswordForm  # Import the form classes that we've created
from app.models import User, Post
from flask_login import login_user, current_user, logout_user, login_required
from flask_mail import Message

@app.route("/")
@app.route("/home")
# Redirect user to the /login route if they are not logged in
@login_required
def home():
    # Get the current page in pagination. Set default page to 1, and type to int
    page = request.args.get('page', 1, type=int)
    # Query database using pagination, show 5 posts per page
    posts = Post.query.order_by(Post.date_posted.desc()).paginate(page = page, per_page=15)
    return render_template('home.html', posts = posts)


@app.route("/about")
def about():
    return render_template('about.html', title = 'About')


@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash(f'Conta criada com sucesso. Você já pode realizar o login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            else:
                return redirect(url_for('home'))
        else:
            flash('Usuário ou senha inválido(s). Por favor, verifique e tente novamente.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('home'))


def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    f_name, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)
    i = Image.open(form_picture)
    output_size = (125, 125)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Your accound has been updated!', 'success')
        return redirect(url_for('account'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title = 'Account', image_file = image_file, form=form)


@app.route('/post/new', methods=['GET', 'POST'])
@login_required
def new_post():
    form = PostForm()
    if form.validate_on_submit():
        post = Post(title=form.title.data, content=form.content.data, author=current_user)
        db.session.add(post)
        db.session.commit()
        flash('O seu post foi criado com sucesso!', 'success')
        return redirect(url_for('home'))
    return render_template('create_post.html', title='New Post', form=form, legend="New Post")


# Route that takes to the editing page of a specific post
# Passing the post id as a varible to the route
@app.route('/post/<int:post_id>')
@login_required
def post(post_id):
    # Get post by id, or return 404 error if post doesn't exist
    post = Post.query.get_or_404(post_id)
    return render_template('post.html', title=post.title, post=post)


@app.route('/post/<int:post_id>/update', methods=['GET', 'POST'])
@login_required
def update_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    form = PostForm()
    if form.validate_on_submit():
        post.title = form.title.data
        post.content = form.content.data
        db.session.commit()
        flash('Seu post foi atualizado com sucesso!', 'success')
        return redirect(url_for('post', post_id=post.id))
    elif request.method == 'GET':
        form.title.data = post.title
        form.content.data = post.content
    return render_template('create_post.html', title='Update Post', form=form, post=post, legend="Update Post")


@app.route('/post/<int:post_id>/delete', methods=['POST'])
@login_required
def delete_post(post_id):
    post = Post.query.get_or_404(post_id)
    if post.author != current_user:
        abort(403)
    db.session.delete(post)
    db.session.commit()
    flash('Seu post foi deletado com sucesso!', 'success')
    return redirect(url_for('home'))



@app.route("/user/<string:username>")
# Redirect user to the /login route if they are not logged in
@login_required
def user_posts(username):
    # Get the current page in pagination. Set default page to 1, and type to int
    page = request.args.get('page', 1, type=int)
    # Get user
    user = User.query.filter_by(username=username).first_or_404()
    # Get posts by this user
    posts = Post.query.filter_by(author=user)
    # Order posts from newer to oldest
    posts = posts.order_by(Post.date_posted.desc())
    # Paginate posts
    posts = posts.paginate(page=page, per_page=5)
    return render_template('user_posts.html', posts = posts, user=user)


# Função para enviar e-mail de redefinição ao usuário
# Recebe o usuário vindo de uma query no banco de dados
def send_reset_email(user):
    token = user.get_reset_token()
    msg = Message('Password Reset Request',
                  sender='fatex.adm@gmail.com',
                  recipients=[user.email])
    msg.body = f'''To reset your password, visit the following link:
{url_for('reset_token', token=token, _external=True)}

If you did not make this request then simply ignore this email and no changes will be made.
'''
    mail.send(msg)



# Rota para solicitar reset de senha
@app.route('/reset_password', methods=['GET', 'POST'])
def reset_request():
    # Se usuário estiver logado, redirecionar para página inicial
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RequestResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        send_reset_email(user)
        flash('Um e-mail foi enviado com as instruções para redefinir sua senha.', 'info')
        return redirect(url_for('login'))
    return render_template('reset_request.html', title='Reset Password', form=form)


# Rota para resetar senha do usuário
@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_token(token):
    # Se usuário estiver logado, redirecionar para página inicial
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    # Se o token for válido, armazenar id do  (retornado pelo método "verify_reset_token") na variável "user"
    user = User.verify_reset_token(token)
    # Se token não for válido, exibir mensagem ao usuário
    if not user:
        flash('That is an inalid or expired token', 'warning')
        return redirect(url_for('reset_request'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user.password = hashed_password
        db.session.commit()
        flash(f'Sua senha foi alterada com sucesso!.', 'success')
        return redirect(url_for('login'))
    return render_template('reset_token.html', title='Reset Password', form=form)