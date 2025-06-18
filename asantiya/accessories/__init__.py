import typer
from asantiya.accessories.up import app as up_accessories
from asantiya.accessories.down import app as down_accessories

app = typer.Typer()

app.add_typer(up_accessories)
app.add_typer(down_accessories)