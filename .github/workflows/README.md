# Github Actions

## Entry

1. Set on what actions github will trigeer a check
```
on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]
```

## Jobs
Specify the jobs to be executed. Steps are ordered, meaning the succeeding steps
must have all the requirements ready, any preceding dependencies should be already
installed
### integration-tests
```
  integration-tests:
    runs-on: ubuntu-latest
    
    env:
        PYTHONPATH: ${{ github.workspace }}/src

    steps:
      # Clones your repository into the runner so future steps can access your files.
      - name: ⬇️ Checkout code
        uses: actions/checkout@v4

      # Installs Python 3.11 on the GitHub runner, ready for Poetry and pytest to use.
      - name: 🐍 Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: 📦 Install Poetry
        run: |
          # install poetry and input the output to python3
          curl -sSL https://install.python-poetry.org | python3 -
          # makes the installed poetry command available to all later steps in your workflow.
          echo "$HOME/.local/bin" >> $GITHUB_PATH

      - name: 📦 Install dependencies
        run: poetry install

      - name: 🧪 Run Integration Tests (with retries)
        # short tracebacks on failure, -q: quiet mode (fewer dots, cleaner output).
        run: poetry run pytest integration_test/ --tb=short -q --reruns 3

```


## Other Notes
1. Configure Integration tests to skip Errors such as 451, where the endpoint may
be blocking Github's linux IP to make a WS or REST API to its server due to security concerns
2. Remove src folder from test directory to prevent Github from confusing where the actual
src should be
3. For installing dependencies, do not use --no-root. We want to install our src as a package into
the virtualenv as well. This makes your src pacakge in importable packaage for pytests.
```
[tool.poetry]
name = "crypto-prices-rt"
packages = [
  { include = "src" }
]
```

