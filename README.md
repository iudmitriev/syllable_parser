# Automatic rythmic text marker

## Description

This application provides a way to automatically mark rythmic words in a text in a way used by "Прозиметрон" system. 

## Installation and usage

Install the m2m-aligner from https://github.com/letter-to-phoneme/m2m-aligner/ following instructions

This project uses [uv](https://docs.astral.sh/uv/) for dependency management. Install dependencies with:

```bash
uv sync
```

You may run the application as a Flask server using server.py

```bash
uv run gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

Alternatively, you may use main.py file. You should paste the necessary text in text.txt file and then run the following command with the necessary rythm suggestion

```bash
uv run main.py --rythm=iamb
```

The resulting text will appear in the result.txt file

## License

This code is available under the terms of MIT license
