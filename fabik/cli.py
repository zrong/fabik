"""  .._fabik_cli:

fabik.cli
----------------------------
    
fabik command line interface implementation
"""

import typer

from fabik.cmd import main_callback, main_init

from fabik.cmd.gen import (
    gen_password,
    gen_fernet_key,
    gen_token,
    gen_uuid,
    gen_requirements,
)

from fabik.cmd.conf import (
    conf_callback,
    conf_tpl,
    conf_make,
)

from fabik.cmd.venv import (
    venv_init,
    venv_update,
    venv_outdated,
)

from fabik.cmd.server import (
    server_callback,
    server_deploy,
    server_start,
    server_stop,
    server_reload,
    server_dar,
)


main: typer.Typer = typer.Typer()

sub_gen: typer.Typer = typer.Typer(name='gen', help='[local] Generate common strings.')
sub_conf: typer.Typer = typer.Typer(name='conf', help='[local/remote] Process configuration files.')
sub_venv: typer.Typer = typer.Typer(
    name='venv', help='[remote] Process Python virtual environment on remote server.'
)
sub_server: typer.Typer = typer.Typer(
    name='server', help='[remote] Process remote server.'
)

main.add_typer(sub_gen)
main.add_typer(sub_conf)
main.add_typer(sub_venv)
main.add_typer(sub_server)


# The method in cmd module may be used as a command by other modules, so it is not decorated with a decorator.
main.callback()(main_callback)
main.command('init')(main_init)

sub_conf.callback()(conf_callback)
sub_conf.command('tpl')(conf_tpl)
sub_conf.command('make')(conf_make)

sub_gen.command('password')(gen_password)
sub_gen.command('fernet-key')(gen_fernet_key)
sub_gen.command('token')(gen_token)
sub_gen.command('uuid')(gen_uuid)
sub_gen.command('requirements')(gen_requirements)
    
    
sub_venv.callback()(server_callback)
sub_venv.command('init')(venv_init)
sub_venv.command('update')(venv_update)
sub_venv.command('outdated')(venv_outdated)


sub_server.callback()(server_callback)
sub_server.command('deploy')(server_deploy)
sub_server.command('start')(server_start)
sub_server.command('stop')(server_stop)
sub_server.command('reload')(server_reload)
sub_server.command('dar')(server_dar)