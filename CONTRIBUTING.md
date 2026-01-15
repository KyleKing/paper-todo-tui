# Contributing

## Development

### Running Tests

```bash
uv run pytest -v

# Run tests with coverage
uv run pytest -v --cov=paper_todo --cov-report=term-missing
```

## Demo Recording

The demo GIF in the README is generated using [VHS](https://github.com/charmbracelet/vhs).

### Installing VHS

```bash
# macOS
brew install vhs

# Or with Go
go install github.com/charmbracelet/vhs@latest
```

### Generating the Demo

To regenerate the demo GIF after making changes:

```bash
vhs < .github/assets/demo.tape
```

This will create `.github/assets/demo.gif` which is displayed in the README.

### Updating the Demo

Edit `.github/assets/demo.tape` to modify the demo recording. The file uses VHS tape format with commands like:

- `Type` - Type characters into the terminal
- `Sleep` - Wait for a duration
- `Enter` - Press Enter key
- `Space` - Press Space key
- Configuration options for terminal size, font, theme, etc.

See the [VHS documentation](https://github.com/charmbracelet/vhs) for full syntax.
