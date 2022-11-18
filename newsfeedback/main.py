import click
from loguru import logger as log

@click.command()
@click.argument("name", type=str)
def cli(name: str) -> None:
    """ This internal function is called by the click-decorated function.
    The split into two functions is necessary for documentation purposes as pdoc3
    cannot process click-decorated functions.

    Parameters :
        name : str : name argument passed by click
    Returns:
        None: Nada   
    """
    log.info(cli_implementation(name))

def cli_implementation(name: str) -> None:
    """ Greet someone or something by name.

    Parameters:
        name : str : Whom to greet

    Return:
        str : Greeting
    """
    return f"Hello {name}!"

if __name__ == "main":
    cli()
