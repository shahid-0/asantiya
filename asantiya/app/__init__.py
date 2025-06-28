import typer
from asantiya.app.remove import app as delete_app
from asantiya.app.stop import app as stop_app
from asantiya.app.start import app as start_app


app = typer.Typer()

app.add_typer(delete_app)
app.add_typer(stop_app)
app.add_typer(start_app)