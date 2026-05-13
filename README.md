# Automatic rythmic text marker

## Description

This application provides a way to automatically mark rythmic words in a text in a way used by "Прозиметрон" system. 

## Installation and usage

### Prerequisites

- `git`, `make`, a C++ compiler (for building m2m-aligner)
- [`uv`](https://docs.astral.sh/uv/) for Python dependency management

### Setup

Install everything (m2m-aligner binary, Python deps, NLTK resources) with a single command:

```bash
make setup
```

### Running

Production server (gunicorn, daemonized on port 80):

```bash
make run
```

Development server (Flask debug mode on port 5000):

```bash
make dev
```

### CLI usage

Alternatively, use `main.py` directly. Paste the input text into `text.txt`, then run with the desired rythm:

```bash
uv run main.py --rythm=iamb
```

The result will appear in `result.txt`.

### Cleanup

Remove the m2m-aligner clone and Python caches:

```bash
make clean
```

## License

This code is available under the terms of MIT license
