import os
import sys
import click

from flask import Flask, url_for, render_template, request, redirect, flash
from markupsafe import escape
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(os.path.dirname(app.root_path), os.getenv('DATABASE_FILE', 'data.db'))
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # 关闭对模型修改的监控
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev')

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    username = db.Column(db.String(20))
    password_hash = db.Column(db.String(128))
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def validate_password(self, password):
        return check_password_hash(self.password_hash, password)
    

class Movie(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(60))
    year = db.Column(db.String(4))

@login_manager.user_loader
def load_user(user_id):
    user = User.query.get(int(user_id))
    return user

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Invalid input')
            return redirect(url_for('login'))
        
        user = User.query.first()
        
        if username == user.username and user.validate_password(password):
            login_user(user)
            flash('Login success.')
            return redirect(url_for('movie_list', name=user.name))
        
        flash('Invalid username or password.')
        return redirect(url_for('login'))
    
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('movie_list', name=''))

@app.route('/')
def index():
    return '<h1>hello flask</h1><img src ="http://helloflask.com/totoro.gif">'

@app.route('/user/<name>')
def user_page(name):
    return f'User: {escape(name)}'

@app.route('/test')
def test():
    print ("url_for root is: ", url_for('hello'))
    user = "tom"
    print ("url_for user page of %s is: " % user, url_for('user_page', name=user))
    user = "chi"
    print ("url_for user page of %s is: " % user, url_for('user_page', name=user))
    print ("url_for test is: ", url_for('test'))
    return "Test Page"

@app.route('/<name>/movielist', methods=['GET', 'POST'])
def movie_list(name):
    if request.method == 'POST':
        if not current_user.is_authenticated:
            return redirect(url_for('index'))
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')  # 显示错误提示
            return redirect(url_for('movie_list', name=name))  # 重定向回主页
        movie = Movie(title=title, year=year)
        db.session.add(movie)
        db.session.commit()
        flash('Movie added.')
        return redirect(url_for('movie_list', name=name))
    user = User.query.filter_by(name=name).first()
    return render_template('index.html', name=user.name if user else "Unknown")

@app.route('/<name>/movielist/edit/<int:movie_id>', methods=['GET', 'POST'])
@login_required
def edit_movie(name, movie_id):
    movie = Movie.query.get_or_404(movie_id)
    if request.method == 'POST':
        title = request.form['title']
        year = request.form['year']
        
        if not title or not year or len(year) != 4 or len(title) > 60:
            flash('Invalid input.')
            return redirect(url_for('edit_movie', name=name, movie_id=movie_id))
        
        movie.title = title
        movie.year = year
        db.session.commit()
        flash('Item updated.')
        return redirect(url_for('movie_list', name=name))
    
    return render_template('edit.html', name=name, movie=movie)

@app.route('/<name>/movielist/delete/<int:movie_id>', methods=['POST'])
@login_required
def delete(name, movie_id):
    movie = Movie.query.get_or_404(movie_id)
    db.session.delete(movie)
    db.session.commit()  # 提交数据库会话
    flash('Item deleted.')
    return redirect(url_for('movie_list', name=name)) 

@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method ==  'POST':
        name = request.form['name']
        
        if not name or len(name) > 20:
            flash('Invalid input.')
            return redirect(url_for('settings'))
        
        current_user.name = name
        db.session.commit()
        flash('Settings updated.')
        return redirect(url_for('movie_list', name=name))
    
    return render_template('settings.html')

@app.context_processor
def inject_movie():
    movies = Movie.query.all()
    return dict(movies=movies)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.cli.command()  # 注册为命令，可以传入 name 参数来自定义命令
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    """Initialize the database."""
    if drop:  # 判断是否输入了选项
        click.echo('drop all')
        db.drop_all()
    db.create_all()
    click.echo('Initialized database.')  # 输出提示信息
    
@app.cli.command() 
def forge():
    # "generate fake data"
    db.create_all()
    
    names = ["quan", "black"]
    
    for n in names:
        name = User(name=n)
        db.session.add(name)
    
    movies = [
        {'title': 'My Neighbor Totoro', 'year': '1988'},
        {'title': 'Dead Poets Society', 'year': '1989'},
        {'title': 'A Perfect World', 'year': '1993'},
        {'title': 'Leon', 'year': '1994'},
        {'title': 'Mahjong', 'year': '1996'},
        {'title': 'Swallowtail Butterfly', 'year': '1996'},
        {'title': 'King of Comedy', 'year': '1999'},
        {'title': 'Devils on the Doorstep', 'year': '1999'},
        {'title': 'WALL-E', 'year': '2008'},
        {'title': 'The Pork of Music', 'year': '2012'},
    ]
    
    
    for m in movies:
        movie = Movie(title=m['title'], year=m['year'])
        db.session.add(movie)
    
    db.session.commit()
    click.echo("forge db data, done!")

@app.cli.command()
@click.option('--username', prompt=True, help='The ueser name used to login')
@click.option('--password', prompt=True, hide_input=True, confirmation_prompt=True, help='The password used to login.')
def admin(username, password):
    db.create_all()
    
    user = User.query.first()
    if user is not None:
        click.echo('Updating user...')
        user.username = username
        user.set_password(password)
    else:
        click.echo('Creating user...')
        user = User(username=username, name='Admin')
        user.set_password(password)
        db.session.add(user)
    
    db.session.commit()
    click.echo('Done.')


