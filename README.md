# TMC Course creation helper
![linux](https://github.com/ljleppan/tmc-course/actions/workflows/linux.yml/badge.svg?event=push)![windows](https://github.com/ljleppan/tmc-course/actions/workflows/windows.yml/badge.svg?event=push)

## TODO for version 1.0.0:
- [x] `init course`
- [x] `init part`
- [x] `init assignment`
- [x] `update`
- [ ] `test`
- [ ] Support Windows

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
