import typer

app = typer.Typer()


@app.command()
def run() -> None:
    print("hello world")
