# Bringing It Together

We've explored the Model, View, and Controller in isolation. Each layer has clear responsibilities and well-defined interfaces. But how do users actually run the simulation? How is all this wired together into a working application? The answer lies in the command-line interface. Thanks to our architecture, this integration layer is simple and elegant.

This focuses on the use of [`typer`](https://typer.tiangolo.com/).
Typer is a modern Python CLI framework that translates Python functions into command-line commands. In addition, Typer validates inputs, generates help text, and enables a pattern that eliminates large branching logic from your code. These enable it to fail fast should there be any issues with the information provided to the command line application and makes it easy for your user to use it.

## Validation at the Boundary

For users, the entry point is not the Python code or the configuration objects. Instead, it is the command line where users would type commands like,

```bash
game-of-life cli basic-config.yaml
```

One critical principle in software design is fail fast at the boundary. Before data enters your application logic, it should be validated. This is where `typer` and `pydantic` work together.

### Using `typer` and `pydantic` to Perform Validations

In the example above,

- `game-of-life` is the [command](https://en.wikipedia.org/wiki/Command_(computing)) that is being run
- `cli` is a [subcommand](https://typer.tiangolo.com/tutorial/commands/#command-or-subcommand) which specifies the view to be the command line interface
- `basic-config.yaml` is an argument to the subcommand

!!! note
    This is analogous to `git`. When making a commit using `git commit -m "my commit message"`, `git` is the command being invoked, `commit` is the subcommand and `-m "my commit message"` is the argument being passed to it.

This `cli` subcommand is implemented in the `cli()` method,

```python title="main.py" linenums="1"
app = typer.Typer()

@app.command()
def cli(
    gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    speed: Annotated[float, typer.Option(help="Seconds between generations", min=0)] = 0.1,
    generations: Annotated[int | None, typer.Option(help="Number of generations", min=1)] = None,
) -> None:
    cli_view: BaseView = CliView(speed)
    game = create_game_of_life(GameOfLifeConfigFrom.from_yaml(gol_config))
    execute_game_of_life(game, cli_view, generations)
```

The [`#!py @app.command()` decorator](https://typer.tiangolo.com/tutorial/commands/#a-cli-application-with-multiple-commands) in line 3 tells `typer` that for my command line application stored in the variable `app` (defined in line 1), I want to add a new command using the name of my function (i.e., `cli`).

1. The first argument of the function is `gol_config` (line 5) and is an argument of the subcommand by specifying it as a [`typer.Argument`](https://typer.tiangolo.com/tutorial/arguments/). As the type for this has been specified as a `Path` (i.e., path to the config file), additional [`Path` based validations](https://typer.tiangolo.com/tutorial/parameter-types/path/#path-validations) are performed. In this case, it checks that: the file exists; is a file and not a directory; and is readable.
2. The second argument of the function is `speed` (line 6) and is an option to the subcommand by specifying it [`typer.Option`](https://typer.tiangolo.com/tutorial/options/). This means that it is optional, specified with a flag, and a default value will be used if it is not provided. As the type for this is a `float` and an additional check has been specified (i.e. `min=0` kwarg in `typer.Option`), it will enforce that it is a non-negative float. If the user types `--speed -5`, `typer` rejects it immediately with a clear error message.
3. Similarly for `generations`, `typer` will enforce that it is larger than 1 and that it is an integer.

If all these check pass, `pydantic` validates the *contents* of the YAML file when `GameOfLifeConfigFrom.from_yaml()` is called in line 10, catching malformed configurations before they reach game logic.

This layered validation enables invalid input to be caught close to where it entered, preventing cascading errors deep in the application. Users get clear, actionable error messages. Developers can trust that data inside functions is valid.

### Type Annotations as Documentation

Notice the `Annotated` type hints. As mentioned earlier, these aren't just for type checkers, `typer` reads them to generate CLI behavior,

```python
gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)]
```

This single line tells `typer`,

- This is a positional argument (not an option)
- It must be a valid file path
- It must be readable
- Generate appropriate help text

The information is in one place, so it's easy to maintain and modify. Change the validation requirements? Update the annotation, and `typer` automatically adjusts its behavior and help text.

## Eliminating Branching Logic with Subcommands

Now consider the architecture decision in `main.py`. There are three commands: `run`, `cli`, and `plot`. Why three? This is where subcommands become powerful as a design pattern.

### The Complex `run` Command

The `run` command accepts a full `RunConfig` that specifies both the game parameters and the interface (CLI or PLOT):

```python title="main.py"
@app.command()
def run(
    config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    generations: Annotated[int | None, typer.Option(help="Number of generations", min=1)] = None,
) -> None:
    """Run the Game of Life with configuration from a YAML file."""
    run_config = RunConfig.from_yaml(config)

    if run_config.interface == DisplayInterface.PLOT and generations is None:
        raise ValueError("Generations must be provided for plot interface")

    view = _create_view(run_config)
    game = create_game_of_life(run_config.gol_config)
    execute_game_of_life(game, view, generations)
```

This function needs branching logic: it must handle both CLI and PLOT interfaces. The `_create_view` function contains the branching:

```python title="main.py"
def _create_view(run_config: RunConfig) -> BaseView:
    """Create the appropriate view based on configuration using the Factory Pattern."""
    match run_config.interface:
        case DisplayInterface.CLI:
            if not isinstance(run_config.view_config, CLIViewConfig):
                raise ValueError("View config must be of type CLIViewConfig for CLI interface")
            return CliView(run_config.view_config.speed)
        case DisplayInterface.PLOT:
            if not isinstance(run_config.view_config, PlotViewConfig):
                raise ValueError("View config must be of type PlotViewConfig for PLOT interface")
            return PlotView(output_path=run_config.view_config.output_dir / run_config.view_config.output_filename)
        case _ as unreachable:
            assert_never(unreachable)
```

The `run` command is general-purpose but complex. It must support multiple paths through its logic.

### The Simple `cli` Command

Contrast this with the specialized `cli` command:

```python title="main.py"
@app.command()
def cli(
    gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    speed: Annotated[float, typer.Option(help="Seconds between generations", min=0)] = 0.1,
    generations: Annotated[int | None, typer.Option(help="Number of generations", min=1)] = None,
) -> None:
    """Run the Game of Life with a command-line interface display."""
    cli_view: BaseView = CliView(speed)
    game = create_game_of_life(GameOfLifeConfigFrom.from_yaml(gol_config))
    execute_game_of_life(game, cli_view, generations)
```

Notice: **no branching logic**. The function knows, by definition, that it's creating a CLI view. The `speed` parameter directly controls how fast the animation plays. There's no match statement, no factory, no type guards.

The `plot` command is similarly straightforward:

```python title="main.py"
@app.command()
def plot(
    gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    generations: Annotated[int, typer.Option(help="Number of generations", min=1)] = 100,
    output_file: Annotated[Path | None, typer.Option(file_okay=True, dir_okay=False, writable=True)] = None,
) -> None:
    """Run the Game of Life and save visualization plots."""
    plot_view: BaseView = PlotView(output_path=output_file)
    game = create_game_of_life(GameOfLifeConfigFrom.from_yaml(gol_config))
    execute_game_of_life(game, plot_view, generations)
```

Again, no branching. The `plot` command knows it's creating a plot view. It takes an output file path and passes it directly to `PlotView`.

### The Key Insight

This demonstrates a crucial architectural principle: **subcommands can eliminate branching logic by making decisions at the entry point**.

Instead of one general `run` command that must branch internally, we have three specialized commands:

- `run`: Full configuration from YAML, supports any interface (needs branching)
- `cli`: Simplified entry point for CLI visualization (no branching)
- `plot`: Simplified entry point for plotting (no branching)

Each specialized command has a clear, linear flow. No match statements. No factory patterns. Just straightforward orchestration.

### When to Use Each Approach

If a user knows they want a CLI animation with specific parameters, they use:
```bash
game-of-life cli config.yaml --speed 0.05
```

This is simple and direct. The command's logic is obvious.

If a user has a complex configuration file that specifies both game parameters and interface settings, they use:
```bash
game-of-life run full-config.yaml
```

This is more general but also more complex internally. That's acceptable because it's solving a genuinely more complex problem.

The architecture provides both paths without forcing complexity onto users who don't need it.

## Parameter Mapping and Clarity

Subcommands also improve clarity by mapping parameters to their semantic meaning. Compare:

**Using the `run` command** (with a YAML config):
```yaml
interface: cli
view_config:
  speed: 0.1
gol_config:
  num_rows: 100
  num_cols: 100
```

**Using the `cli` command** (direct CLI parameters):
```bash
game-of-life cli config.yaml --speed 0.1
```

The `cli` command exposes only the parameters relevant to CLI visualization. Users don't see `interface` or `view_config`—those are implicit in choosing the `cli` subcommand. This reduces cognitive load.

## Validation Strategy Across Layers

The validation architecture spans multiple layers, each appropriate to its level:

1. **CLI Layer (Typer)**: Path existence, type conversion, numeric ranges, required/optional status
2. **Configuration Layer (Pydantic)**: YAML parsing, field type validation, constraint enforcement, cross-field validation
3. **Application Logic**: Business rule validation (e.g., "Pattern must be specified if pattern initialiser is selected")

Each layer knows about concerns at its level and delegates upward. Typer doesn't validate YAML syntax—that's Pydantic's job. Pydantic doesn't check file paths—that's Typer's job. This separation prevents duplication and keeps concerns localized.

## User Experience Through Architecture

Users benefit from this architecture without knowing it exists:

- **Clear, hierarchical commands**: `game-of-life cli`, `game-of-life plot`, `game-of-life run` immediately signal different use cases
- **Automatic help**: `game-of-life --help`, `game-of-life cli --help` generate comprehensive documentation from docstrings and type annotations
- **Fast feedback**: Invalid inputs are caught instantly, with specific error messages
- **Simple workflows**: Common use cases (CLI animation, plot generation) have simple command syntax without exposing complexity

Behind the scenes, sophisticated architecture—configuration composition, factory patterns, abstract base classes—enables this simplicity.

## Extensibility Through Subcommands

Consider what happens when you want to add a new visualization mode (say, web-based). With good CLI design using subcommands, you have options:

**Option 1**: Add a new subcommand:
```python
@app.command()
def web(
    gol_config: Annotated[Path, typer.Argument(...)],
    port: Annotated[int, typer.Option(help="Port to serve on")] = 8000,
    generations: Annotated[int | None, typer.Option(...)] = None,
) -> None:
    web_view: BaseView = WebView(port=port)
    game = create_game_of_life(GameOfLifeConfigFrom.from_yaml(gol_config))
    execute_game_of_life(game, web_view, generations)
```

This is clean, follows the established pattern, and doesn't require modifying existing commands.

**Option 2**: Extend the `run` command to support web in full configurations:
```yaml
interface: web
view_config:
  port: 8000
gol_config:
  num_rows: 100
  num_cols: 100
```

Then update the factory:
```python
case DisplayInterface.WEB:
    if not isinstance(run_config.view_config, WebViewConfig):
        raise ValueError(...)
    return WebView(port=run_config.view_config.port)
```

Both approaches work because the architecture is modular. The choice depends on your users' needs.

## Bringing It All Together

The complete flow from user input to simulation is:

1. **User runs command**: `game-of-life cli config.yaml --speed 0.1`
2. **Typer parses**: Validates arguments, converts types, calls the `cli` function
3. **cli function loads config**: `GameOfLifeConfigFrom.from_yaml(config)` validates the YAML
4. **Create model and view**: Straightforward instantiation with validated parameters
5. **Controller orchestrates**: `execute_game_of_life` loops through generations, calling `view.render()` and `game.step()`
6. **View displays**: CliView renders the grid to the terminal
7. **Model computes**: GameOfLife computes next generation
8. **Exit cleanly**: Context manager cleans up resources

Each layer does one thing well. The result is an application that is simultaneously:

- **Powerful**: Supports multiple interfaces, flexible configuration, extensible architecture
- **Simple**: Users see only what they need; internal complexity is hidden
- **Maintainable**: Changes to one layer don't cascade; new features can be added in isolation
- **Robust**: Validation at multiple layers catches errors early

This is the promise of good architecture made concrete: complexity in service of simplicity.
