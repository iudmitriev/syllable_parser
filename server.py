from main import mark_rythmic_text
from src.iamb_analyzer import analyze_iamb

from flask import Flask, render_template, request, send_file, make_response
from io import StringIO

app = Flask(__name__)

def process_text(text, selected_option):
    text = text.split('\n')
    text = [line + '\n' for line in text]
    text = mark_rythmic_text(text, selected_option)
    return text

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/explanations')
def explanations():
    return render_template('explanations.html')

@app.route('/process_text', methods=['POST'])
def process():
    text_input = request.form['text_input']
    file_input = request.files['file_input']
    selected_option = request.form['option_selector']

    
    if file_input:
        text_input = file_input.read().decode("utf-8")
    processed_text = process_text(text_input, selected_option)
    
    return render_template('index.html', processed_text=processed_text)

@app.route('/iamb', methods=['GET', 'POST'])
def iamb():
    default_feminine_weight = 0.1
    default_variant = 1
    if request.method == 'GET':
        return render_template(
            'iamb.html',
            feminine_weight=default_feminine_weight,
            variant=default_variant,
        )

    text_input = request.form.get('text_input', '')
    file_input = request.files.get('file_input')
    if file_input and file_input.filename:
        text_input = file_input.read().decode('utf-8')

    try:
        feminine_weight = float(request.form.get('feminine_weight', default_feminine_weight))
    except ValueError:
        feminine_weight = default_feminine_weight
    feminine_weight = max(0.0, min(1.0, feminine_weight))

    try:
        variant = int(request.form.get('variant', default_variant))
    except ValueError:
        variant = default_variant
    if variant not in (0, 1, 2, 3):
        variant = default_variant

    result = analyze_iamb(text_input, feminine_weight=feminine_weight, variant=variant)
    return render_template(
        'iamb.html',
        result=result,
        submitted_text=text_input,
        feminine_weight=feminine_weight,
        variant=variant,
    )


@app.route('/download_text')
def download():
    processed_text = request.args.get('processed_text')

    processed_text_file = StringIO(processed_text)
    
    response = make_response(processed_text_file.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=processed_text.txt'
    response.headers['Content-Type'] = 'text/plain'
    
    return response

if __name__ == '__main__':
    app.run(port=5000, debug=True)
