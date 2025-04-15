# Contributing to PyDevCheat

First off, thank you for considering contributing to PyDevCheat! It's people like you that make PyDevCheat such a great tool.

## Code of Conduct

This project and everyone participating in it is governed by our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code.

## How Can I Contribute?

### Reporting Bugs

Before creating bug reports, please check the issue list as you might find out that you don't need to create one. When you are creating a bug report, please include as many details as possible:

* Use a clear and descriptive title
* Describe the exact steps which reproduce the problem
* Provide specific examples to demonstrate the steps
* Describe the behavior you observed after following the steps
* Explain which behavior you expected to see instead and why
* Include screenshots if possible
* Include the output of `pydevcheat --version`

### Suggesting Enhancements

Enhancement suggestions are tracked as GitHub issues. When creating an enhancement suggestion, please include:

* Use a clear and descriptive title
* Provide a step-by-step description of the suggested enhancement
* Provide specific examples to demonstrate the steps
* Describe the current behavior and explain which behavior you expected to see instead
* Explain why this enhancement would be useful
* List some other applications where this enhancement exists

### Pull Requests

* Fill in the required template
* Do not include issue numbers in the PR title
* Include screenshots and animated GIFs in your pull request whenever possible
* Follow the Python and JavaScript styleguides
* Include thoughtfully-worded, well-structured tests
* Document new code
* End all files with a newline

## Development Process

1. Fork the repo and create your branch from `main`
2. If you've added code that should be tested, add tests
3. If you've changed APIs, update the documentation
4. Ensure the test suite passes
5. Make sure your code lints
6. Issue that pull request!

### Setting up the development environment

```bash
# Clone your fork
git clone https://github.com/your-username/pydevcheat.git
cd pydevcheat

# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install development dependencies
pip install -r requirements-dev.txt

# Install the package in development mode
pip install -e .
```

### Running Tests

```bash
# Run all tests
pytest

# Run tests with coverage
pytest --cov=pydevcheat

# Run specific test file
pytest tests/test_main.py
```

### Code Style

* Python code should follow [PEP 8](https://www.python.org/dev/peps/pep-0008/)
* Use [Black](https://github.com/psf/black) for code formatting
* Use [flake8](https://flake8.pycqa.org/) for linting

```bash
# Format code
black .

# Run linter
flake8
```

## Git Commit Messages

* Use the present tense ("Add feature" not "Added feature")
* Use the imperative mood ("Move cursor to..." not "Moves cursor to...")
* Limit the first line to 72 characters or less
* Reference issues and pull requests liberally after the first line
* Consider starting the commit message with an applicable emoji:
    * 🎨 `:art:` when improving the format/structure of the code
    * 🐎 `:racehorse:` when improving performance
    * 🚱 `:non-potable_water:` when plugging memory leaks
    * 📝 `:memo:` when writing docs
    * 🐛 `:bug:` when fixing a bug
    * 🔥 `:fire:` when removing code or files
    * 💚 `:green_heart:` when fixing the CI build
    * ✅ `:white_check_mark:` when adding tests
    * 🔒 `:lock:` when dealing with security
    * ⬆️ `:arrow_up:` when upgrading dependencies
    * ⬇️ `:arrow_down:` when downgrading dependencies
    * 👕 `:shirt:` when removing linter warnings
    * 🏗️ `:building_construction:` when making architectural changes
    * 📈 `:chart_with_upwards_trend:` when improving analytics or telemetry
    * ♻️ `:recycle:` when refactoring code
    * ➕ `:heavy_plus_sign:` when adding a dependency
    * ➖ `:heavy_minus_sign:` when removing a dependency
    * 🔧 `:wrench:` when changing configuration files
    * 🌐 `:globe_with_meridians:` when dealing with internationalization
    * ✏️ `:pencil2:` when fixing typos
    * 💩 `:poop:` when writing bad code that needs to be improved
    * ⏪ `:rewind:` when reverting changes
    * 🔀 `:twisted_rightwards_arrows:` when merging branches
    * 📦 `:package:` when updating compiled files or packages
    * 👽 `:alien:` when updating code due to external API changes
    * 🚚 `:truck:` when moving or renaming files
    * 📄 `:page_facing_up:` when adding or updating license
    * 💥 `:boom:` when introducing breaking changes
    * 🍱 `:bento:` when adding or updating assets
    * ♿️ `:wheelchair:` when improving accessibility
    * 💡 `:bulb:` when adding or updating comments in the code
    * 🍻 `:beers:` when writing code drunkenly
    * 💬 `:speech_balloon:` when updating text and literals
    * 🗃️ `:card_file_box:` when performing database related changes
    * 🔊 `:loud_sound:` when adding logs
    * 🔇 `:mute:` when removing logs
    * 👥 `:busts_in_silhouette:` when adding or updating contributor(s)
    * 🚸 `:children_crossing:` when improving UX/UI
    * 🏗️ `:building_construction:` when making architectural changes
    * 📱 `:iphone:` when working on responsive design
    * 🤡 `:clown_face:` when mocking things
    * 🥚 `:egg:` when adding or updating an easter egg
    * 🙈 `:see_no_evil:` when adding or updating a .gitignore file
    * 📸 `:camera_flash:` when adding or updating snapshots
    * ⚗️ `:alembic:` when performing experiments
    * 🔍 `:mag:` when improving SEO
    * 🏷️ `:label:` when adding or updating types
    * 🌱 `:seedling:` when adding or updating seed files
    * 🚩 `:triangular_flag_on_post:` when adding or updating feature flags
    * 🥅 `:goal_net:` when catching errors
    * 💫 `:dizzy:` when adding or updating animations and transitions
    * 🗑️ `:wastebasket:` when deprecating code that needs to be cleaned up 