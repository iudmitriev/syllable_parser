from main import mark_rythmic_text

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

@app.route('/download_text')
def download():
    processed_text = request.args.get('processed_text')

    processed_text_file = StringIO(processed_text)
    
    response = make_response(processed_text_file.getvalue())
    response.headers['Content-Disposition'] = 'attachment; filename=processed_text.txt'
    response.headers['Content-Type'] = 'text/plain'
    
    return response

if __name__ == '__main__':
    app.run(port=8000, debug=True)
