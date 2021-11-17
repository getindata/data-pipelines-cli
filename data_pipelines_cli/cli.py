import click


@click.group()
def cli() -> None:
    pass


@cli.command()
def hello() -> None:
    print("Hello world!")


if __name__ == "__main__":
    cli()
