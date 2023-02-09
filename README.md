# TMC Course creation helper

## Development
### Installing
```
pip install -r requirements-dev.txt
pre-commit install
pip install --editable .
```

### Pre-commit hooks
The repo comes set up for a combination of `mypy`, `black`, `flake8` and `isort`. These are all set up as `pre-commit` hooks. Assuming you run `pre-commit install` as shown above, these will automatically run whenever you attempt to commit code into git. I suggest running `mypy` using `--strict`.

### Tox and tests
Run `tox` to manually run all pre-commit hooks and tests. Tests fail if test coverage goes below 80 %.
