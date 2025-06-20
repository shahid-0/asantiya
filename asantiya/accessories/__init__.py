import typer
from asantiya.accessories.up import app as up_accessories
from asantiya.accessories.down import app as down_accessories
from asantiya.accessories.restart import app as restart_accessories
from asantiya.accessories.ls import app as ls_accessories
from asantiya.accessories.logs import app as logs_accessories
from asantiya.accessories.reboot import app as reboot_accessories

app = typer.Typer()

app.add_typer(up_accessories)
app.add_typer(down_accessories)
app.add_typer(restart_accessories)
app.add_typer(ls_accessories)
app.add_typer(logs_accessories)
app.add_typer(reboot_accessories)