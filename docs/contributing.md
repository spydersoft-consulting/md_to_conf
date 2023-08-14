# Contribution Guidelines


## Environment Configuration

It is recommended that you use a virtual environment for development.

### VENV

Create a new python virtualenv and activate it:

```less
python3 -m venv venv
source venv/bin/activate
```

### Anaconda

[Installation Guide](https://conda.io/projects/conda/en/latest/user-guide/install/download.html)

```bash
  conda create --name md_to_conf python=3.11 --yes
  conda activate md_to_conf
```

## Requirements

Install the requirements for the application:

```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt
```


## Install the Module

Install the module in an editable mode:

```bash
pip install -e .
```

Run `md-to-conf -h` and verify that the help is displayed.

## Contributing

Contributions are what make the open source community such an amazing place to be learn, inspire, and create. Any contributions you make are **greatly appreciated**.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


### Formatting and Linting

This repository is configured to use [pre-commit](https://pre-commit.com/) to check code, including [Black](https://black.readthedocs.io/en/stable/) and [Flake8](https://flake8.pycqa.org/en/latest/) to format and lint code.  It is always good to format before commiting changes.

To format:

```bash
> black .
```

To execute flake8 across your changes

```bash
> flake8 .
```

To check your files before committing:
```bash
> pre-commit run
```

## Documentation

This repository uses [mkdocs](https://www.mkdocs.org/) to generate the documentation site, along with [mkdocsstrings-python](https://mkdocstrings.github.io/python/) to extract documentation from code comments.  This project uses [Google-formatted docstrings](https://sphinxcontrib-napoleon.readthedocs.io/en/latest/example_google.html) to generate, so please follow that standard when documenting code.

Your contribution should be documented.  You can generate documentation locally using the following commands.

```bash
> pip install -r requirements-mkdocs.txt
> mkdocs serve
```

The documentation site is updated when new releases are published in Github.
