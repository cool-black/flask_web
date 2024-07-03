import click
from watchlist import app, db

@app.cli.command()
@click.option('--drop', is_flag=True, help='Create after drop.')  # 设置选项
def initdb(drop):
    if drop:
        click.echo('drop all')
    db.create_all()
    click.echo('Initialized database.')