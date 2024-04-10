# Automatic rythmic text marker

## Description

This application provides a way to automatically mark rythmic words in a text in a way used by "Прозиметрон" system. 

## Installation and usage

Install the m2m-aligner from https://github.com/letter-to-phoneme/m2m-aligner/ following instructions

Install necessary requirements from requirements.txt:

```bash
pip install -r requirements.txt
```

You may run the application as a Flask server using server.py

```bash
gunicorn -w 4 -b 0.0.0.0:5000 server:app
```

Alternatively, you may use main.py file. You should paste the necessary text in text.txt file and then run the following command with the necessary rythm suggestion

```bash
python3 main.py --rythm=iamb
```

The resulting text will appear in the result.txt file

## License

This code is available under the terms of MIT license
