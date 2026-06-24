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

```python title="main.py" linenums="1" hl_lines="5-7 10"
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

The [`#!py @app.command()` decorator](https://typer.tiangolo.com/tutorial/commands/#a-cli-application-with-multiple-commands) in line 3 tells `typer` that for my command line application stored in the variable `app` (defined in line 1), I want to add a new subcommand using the name of my function (i.e., `cli`).

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

Now consider the architecture decision in `main.py`. There are three commands: `run`, `cli`, and `plot`. The `run` subcommand is more generic than `cli` and `plot` as it allows the game of life to be rendered in either the terminal or a plot. This redundancy has been included to demonstrate how subcommands can be used to eliminate branching logic. In this example, it is fairly trivial, however, in real research code, this can avoid massive nested branching logic.

### The Complex `run` Command

The `run` command accepts a full `RunConfig` that specifies both the game parameters and the view interface (CLI or plotting). It also has an option to specify the number of generations.

```python title="main.py" linenums="1" hl_lines="8 9 11"
@app.command()
def run(
    config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    generations: Annotated[int | None, typer.Option(help="Number of generations", min=1)] = None,
) -> None:
    run_config = RunConfig.from_yaml(config)

    if run_config.interface == DisplayInterface.PLOT and generations is None:
        raise ValueError("Generations must be provided for plot interface")

    view = _create_view(run_config)
    game = create_game_of_life(run_config.gol_config)
    execute_game_of_life(game, view, generations)
```

For the plotting view to work properly, the number of generations must be specified. Thus, additional logic in lines 8 and 9, are needed to ensure that the plotting view can be instantiated. As the view is specified by the config, it delegates this branching logic to instantiate the appropriate child of `BaseView` to the `_create_view()` function,

```python title="main.py"
def _create_view(run_config: RunConfig) -> BaseView:
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

This factory method checks that the instance on the `view_config` field of the `RunConfig` class aligns with the `RunConfig.interface` field and instantiates the appropriate child view class.
The `run` command is general-purpose but complex. It trades complexity for generality to enable it to support multiple paths through its logic.

### The Specialized Subcommands

Contrast this with the specialized `plot` subcommand below and the `cli` command in the [earlier section on using `typer` and `pydantic` to perform validations](#using-typer-and-pydantic-to-perform-validations),

```python title="main.py" hl_lines="7"
@app.command()
def plot(
    gol_config: Annotated[Path, typer.Argument(exists=True, file_okay=True, dir_okay=False, readable=True)],
    generations: Annotated[int, typer.Option(help="Number of generations", min=1)] = 100,
    output_file: Annotated[Path | None, typer.Option(file_okay=True, dir_okay=False, writable=True)] = None,
) -> None:
    plot_view: BaseView = PlotView(output_path=output_file)
    game = create_game_of_life(GameOfLifeConfigFrom.from_yaml(gol_config))
    execute_game_of_life(game, plot_view, generations)
```

This has *no branching logic* when instantiating the view.
The `plot` command knows it's creating a plot view. It takes an output file path and passes it directly to `PlotView`.
There's no match statement, no factory, no type guards.
<!--Similarly, with the `cli` subcommand, the function knows, by definition, that it's creating a CLI view. The `speed` parameter directly controls how fast the animation plays. -->

### When to Use Each Approach

If a user knows they want a CLI animation with specific parameters, they use,

```bash
game-of-life cli config.yaml --speed 0.05
```

This is simple and direct. The command's logic is obvious.

If a user has a complex configuration file that specifies both game parameters and interface settings, they use:

```bash
game-of-life run full-config.yaml
```

This is more general but also more complex internally. A use case where this would be preferred is when we want to have a common interface. For example, if we want to run a large batch of simulations through a script (e.g. on a HPC system that schedules jobs using [PBS](https://en.wikipedia.org/wiki/Portable_Batch_System) or [Slurm](https://slurm.schedmd.com/overview.html)), then it is useful to the script to use the common `run` subcommand and tailoring each of the configuration files accordingly.

!!! tip
    The core idea behind this is deciding what level of abstraction is needed and where to handle the complexity of handling the different views. In the more general `run` subcommand, that complexity is handled *within Python*. In the specialized subcommands, that complexity is handled *by the user*.

The architecture provides both paths without forcing complexity onto users who don't need it.

### Parameter Mapping and Clarity

Subcommands also improve clarity by mapping parameters to their semantic meaning. Compare using the `run` command with a YAML config,

```yaml
interface: cli
view_config:
  speed: 0.1
gol_config:
  num_rows: 100
  num_cols: 100
```

To using the `cli` command through direct CLI parameters,

```bash
game-of-life cli config.yaml --speed 0.1
```

The `cli` command exposes only the parameters relevant to CLI visualization. Users don't see `interface` or `view_config`, those are implicit in choosing the `cli` subcommand. This reduces cognitive load.

### Extensibility and Drawbacks of Subcommands

Our MVC architecture allows us to easily add new visualization mode (say, web-based). With the subcommands, adding a new view would require adding another function, for example,

```python title="example new subcommand for web view" hl_lines="8-9"
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

This follows the same structure of instantiating the view, then creating and executing the game. It is trivial to add another view and doesn't require modifying existing commands or functions. However, this pattern has a drawback - code repetition. The last two lines are identical to the `cli()` and `plot()` functions.

This is where we have to make a design decision - do we want to have code repetition or additional complexity in our code? The "correct" answer depends on specifics of the problem, experience and personal coding style.

For this specific problem, my personal preference would be to abandon the specialized subcommand. This would require adding complexity to the `run()` function and updating the factory,

```python title="example case to add to the factory"
    case DisplayInterface.WEB:
        if not isinstance(run_config.view_config, WebViewConfig):
            raise ValueError(...)
        return WebView(port=run_config.view_config.port)
```

This preference is due to my aversion to [code duplication](https://en.wikipedia.org/wiki/Duplicate_code) as it can bring more [technical debt](https://en.wikipedia.org/wiki/Technical_debt). This means that repeating code twice feels acceptable to me, but not three times. In particular, if I expect to add more views.

!!! note
    Code duplication is a [code smell](https://en.wikipedia.org/wiki/Code_smell#Application-level_smells) that hints at a deeper issue in the source code. However, it is subjective and varies based on the context. This is contrary to an [anti-pattern](https://en.wikipedia.org/wiki/Anti-pattern) which is a counterproductive solution to a class of problem.


## Validation Strategy Across Layers

The validation architecture spans multiple layers, each appropriate to its level:

1. *CLI Layer (`typer`)*: Path existence, type conversion, numeric ranges, required/optional status
2. *Configuration Layer (`pydantic`)*: YAML parsing, field type validation, constraint enforcement, cross-field validation
3. *Application Logic*: "Business" rule validation (e.g., pattern must be specified if pattern initializer is selected)

Each layer knows about concerns at its level and delegates accordingly. `typer` doesn't validate YAML data, that's `pydantic`'s job. `pydantic` doesn't check file paths at the user interface, that's `typer`'s job. This separation prevents duplication and keeps concerns localized.

## How Everything Fits Together

The complete flow from user input to simulation for the `cli` subcommand is,

1. *User runs command*: `game-of-life cli config.yaml --speed 0.1`
2. *Typer parses*: Validates arguments, converts types, calls the `cli` function
3. *Pydantic validates configuration*: `GameOfLifeConfigFrom.from_yaml(config)`
4. *Controller creates model and view*: Instantiation with validated parameters
5. *Controller orchestrates*: `execute_game_of_life` loops through generations, calling `view.render()` and `game.step()`
6. *View displays*: `CliView` renders the grid to the terminal
7. *Model computes*: `GameOfLife` computes next generation
8. *Context manager cleans up*: Resources are freed on program exit

Each layer does one thing. The result is an application that is,

- **Extendable**: The code supports multiple interfaces, flexible configuration, extensible architecture
- **Simple**: Users see only what they need; internal complexity is hidden
- **Maintainable**: Changes to one layer don't cascade; new features can be added in isolation
- **Robust**: Validation at multiple layers catches errors early

The abstractions used allow the construction of an architecture where the complexity is placed at the most appropriate level and hidden from those who don't need it.
