"""  .._fabik_cli:

fabik.cli
----------------------------
    
fabik command line interface implementation
"""

import typer
from fabik.cmd import main_callback, main_init, conf_callback, conf_tpl

main: typer.Typer = typer.Typer()

sub_gen: typer.Typer = typer.Typer(name='gen', help='[local] Generate common strings.')
sub_conf: typer.Typer = typer.Typer(name='conf', help='[local/remote] Process configuration files.')
sub_venv: typer.Typer = typer.Typer(
    name='venv', help='[remote] Process Python virtual environment on remote server.'
)

main.add_typer(sub_gen)
main.add_typer(sub_conf)
# main.add_typer(sub_venv)


# The method in cmd module may be used as a command by other modules, so it is not decorated with a decorator.
main.callback()(main_callback)
main.command('init')(main_init)

sub_conf.callback()(conf_callback)
sub_conf.command('tpl')(conf_tpl)
    