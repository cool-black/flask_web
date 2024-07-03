from watchlist import app, db
from watchlist.models import User, Movie
from flask import render_template, request, url_for, redirect, flash
from flask_login import login_user, login_required, logout_user, current_user


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        if not username or not password or not confirm_password:
            flash('Invalid Input!')
            return redirect(url_for('register'))
        elif password != confirm_password:
            flash('Password must equal to confirm password!')
            return redirect(url_for('register'))
        user = User.query.filter_by(username=username).first()
        if user:
            flash('Username already exists!')
            return redirect(url_for('login'))
        user = User(username=username)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        flash('Register success, please login!')
        return redirect(url_for('login'))
        
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if not username or not password:
            flash('Invalid Input!')
            return redirect(url_for('login'))
        user = User.query.filter_by(username=username).first()
        if not user or not user.check_password(password):
            flash('Invalid username or password!')
            return redirect(url_for('login'))
        
        login_user(user)
        flash('Login success')
        return redirect(url_for('movie_list'))
        
    return render_template('login.html')

@app.route('/logout', methods=['GET'])
def logout():
    logout_user()
    flash('Goodbye.')
    return redirect(url_for('index'))

@app.route('/movie_list', methods=['GET', 'POST'])
def movie_list():
    if not current_user.is_authenticated:
        flash('Please login first')
        return render_template(url_for('login'))
    if request.method == 'POST':
        title = request.form.get('title')
        year = request.form.get('year')
        if not title or not year or len(year) > 4 or len(title) > 60:
            flash('Invalid input.')  
            return redirect(url_for('movie_list'))
        movie = Movie(title=title, year=year, user=current_user)
        db.session.add(movie)
        db.session.commit()
        flash('Movie added.')
        movies = current_user.movies
        return redirect(url_for('movie_list', movies=movies))
    movies = current_user.movies
    return render_template('movie_list.html', movies=movies)

@app.route('/delete/<int:movie_id>', methods=['POST'])
def delete(movie_id):
    movie = Movie.query.get(movie_id)
    if not movie:
        flash('Can not delete this item!')
        return redirect(url_for('movie_list'))
    db.session.delete(movie)
    db.session.commit()
    flash('Item deleted.')
    return redirect(url_for('movie_list'))
   
