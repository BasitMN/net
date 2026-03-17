import typer

app = typer.Typer()

def hello() -> str:
    return "Hello from iot!"

@app.command()
def greet(name: str = typer.Argument("World", help="Name to greet")):
    """Greet someone by name."""
    print(f"Hello, {name}!")

@app.command()
def version():
    """Show the current version."""
    print("iot version 0.2.0")

if __name__ == "__main__":
    app()
