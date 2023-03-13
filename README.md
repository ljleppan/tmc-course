# TMC Course creation helper
![linux](https://github.com/ljleppan/tmc-course/actions/workflows/linux.yml/badge.svg?event=push)![windows](https://github.com/ljleppan/tmc-course/actions/workflows/windows.yml/badge.svg?event=push)

`tmc-course` helps with managing (python-based) TestMyCode courses by allowing you to initialize, update and test them.

# Installing
```
pip install tmc-course
```

# Usage

```
usage: tmc-course [-h] [--version] [--quiet | --debug] ACTION ...

Helper for building TestMyCode python programming courses

positional arguments:
  ACTION
    init       Initialize a new course, part or assignment
    test       Test a new course, part or assignment
    update     Update TMC-python-runner embedded in assignments

options:
  -h, --help   show this help message and exit
  --version    show program's version number and exit
  --quiet, -q  Only output warning
  --debug, -d  Output debugging information
```

## `tmc-course init` - Initialize new courses, parts and assignments

Run the `init` command to initialize a new course, part of assignment from a project skeleton that contains the files required by TMC to function correctly.

### Initialize new course
```
usage: tmc-course init course [-h] path [path ...]

positional arguments:
  path        Path(s) of the new course(s)

options:
  -h, --help  show this help message and exit
```

### Initialize new part
Parts are collections of assignments
```
usage: tmc-course init part [-h] path [path ...]

positional arguments:
  path        Path(s) of the new part(s)

options:
  -h, --help  show this help message and exit
```

### Initialize new assignment
Assignments are initialized in either English (`-e`) or Finnish (`-f`). The freshly initialized assignments are built with a skeleton structure which showcases the use of tests and points, and contains the additional files required by TMC.
```
usage: tmc-course init assignment [-h] (-e | -f) path [path ...]

positional arguments:
  path           Path(s) of the new assignment(s)

options:
  -h, --help     show this help message and exit
  -e, --english  Use English language templates
  -f, --finnish  Use Finnish language templates
```

### `tmc-course update` Update TMC files
The `update` command updates the files required by TMC for all assignments
```
usage: tmc-course update [-h] path

positional arguments:
  path        Course root directory

options:
  -h, --help  show this help message and exit
```

### `tmc-course test` Run tests for the course
Use the `test` command to run the tests for a course, part or assignment the same way the TMC server would run them. This verifies your model solutions pass the tests.

```
usage: tmc-course test [-h] [--details] path [path ...]

positional arguments:
  path        Path(s) to test (course, part or assignment)

options:
  -h, --help  show this help message and exit
  --details   Show more details about test results
```

By default, detailed information is only shown about assignments that fail
their tests. Use `--details` to show additional help.

### As a `pre-commit` hook
`tmc-course` can be used as a [`pre-commit`](https://pre-commit.com/#filtering-files-with-types) hook. When set up correctly, `tmc-course test` is ran for the repository on commit.

To use `tmc-course` as a `pre-commit` hook, add the the following config:
```
  - repo: https://github.com/ljleppan/tmc-course
    rev: v1.0.0b4
    hooks:
      - id: tmc-course
```

## Development
### Installing
```
pip install .[dev]
pre-commit install
```

### Pre-commit hooks
The repo comes set up for a combination of `mypy`, `black`, `flake8` and `isort`. These are all set up as `pre-commit` hooks. Assuming you run `pre-commit install` as shown above, these will automatically run whenever you attempt to commit code into git. I suggest running `mypy` using `--strict`.

### Tox and tests
Run `tox` to manually run all pre-commit hooks and tests. Tests fail if test coverage goes below 80 %.
