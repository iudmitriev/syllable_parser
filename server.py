import nltk

def _ensure_nltk_resources():
    required = [
        ('taggers/averaged_perceptron_tagger_eng', 'averaged_perceptron_tagger_eng'),
        ('taggers/averaged_perceptron_tagger', 'averaged_perceptron_tagger'),
        ('corpora/cmudict', 'cmudict'),
    ]
    for path, pkg in required:
        try:
            nltk.data.find(path)
        except LookupError:
            nltk.download(pkg, quiet=True)

_ensure_nltk_resources()

from main import mark_rythmic_text
from src.iamb_analyzer import analyze_iamb

from flask import Flask, render_template, request, send_file, make_response
from io import StringIO, BytesIO
import base64

import pandas as pd
from src.cluster import run_clustering, compute_cluster_means, compute_author_cluster_counts

app = Flask(__name__)


def is_htmx(req):
    return req.headers.get('HX-Request') == 'true'


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
    text_input = request.form.get('text_input', '')
    file_input = request.files.get('file_input')
    selected_option = request.form.get('option_selector', 'prose')

    if file_input and file_input.filename:
        text_input = file_input.read().decode("utf-8")
    processed_text = process_text(text_input, selected_option)

    if is_htmx(request):
        return render_template('_index_result.html', processed_text=processed_text)
    return render_template('index.html', processed_text=processed_text)

@app.route('/iamb', methods=['GET', 'POST'])
def iamb():
    default_feminine_weight = 0.1
    default_variant = 1
    default_weak_stress_weight = 1.0
    default_shift_weight = 1.0
    if request.method == 'GET':
        return render_template(
            'iamb.html',
            feminine_weight=default_feminine_weight,
            variant=default_variant,
            weak_stress_weight=default_weak_stress_weight,
            shift_weight=default_shift_weight,
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
    if variant not in (0, 1, 2, 3, 4):
        variant = default_variant

    try:
        weak_stress_weight = float(request.form.get('weak_stress_weight', default_weak_stress_weight))
    except ValueError:
        weak_stress_weight = default_weak_stress_weight
    weak_stress_weight = max(0.0, weak_stress_weight)

    try:
        shift_weight = float(request.form.get('shift_weight', default_shift_weight))
    except ValueError:
        shift_weight = default_shift_weight
    shift_weight = max(0.0, shift_weight)

    result = analyze_iamb(
        text_input,
        feminine_weight=feminine_weight,
        variant=variant,
        weak_stress_weight=weak_stress_weight,
        shift_weight=shift_weight,
    )

    if is_htmx(request):
        return render_template('_iamb_result.html', result=result)
    return render_template(
        'iamb.html',
        result=result,
        submitted_text=text_input,
        feminine_weight=feminine_weight,
        variant=variant,
        weak_stress_weight=weak_stress_weight,
        shift_weight=shift_weight,
    )


@app.route('/cluster', methods=['GET', 'POST'])
def cluster():
    if request.method == 'GET':
        return render_template('cluster.html')

    file_input = request.files.get('file_input')
    if not file_input or not file_input.filename:
        return render_template('cluster.html', error='Пожалуйста, загрузите файл.'), 400

    try:
        df = pd.read_excel(file_input, engine='openpyxl')
    except Exception:
        return render_template('cluster.html', error='Не удалось прочитать файл. Убедитесь, что загружен корректный .xlsx файл.'), 400

    n_clusters = None
    raw_k = request.form.get('n_clusters', '').strip()
    if raw_k:
        try:
            n_clusters = int(raw_k)
        except ValueError:
            return render_template('cluster.html', error='Число кластеров должно быть целым числом.'), 400

    try:
        df_result, scores, chosen_k = run_clustering(df, n_clusters=n_clusters)
    except ValueError as e:
        return render_template('cluster.html', error=str(e)), 400

    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        df_result.to_excel(writer, index=False)
    output.seek(0)
    file_b64 = base64.b64encode(output.read()).decode('ascii')

    stem = file_input.filename.rsplit('.', 1)[0]
    download_name = f'{stem}_clustered.xlsx'
    chosen_score = next(s['score'] for s in scores if s['k'] == chosen_k)
    cluster_means = compute_cluster_means(df_result, chosen_k)
    author_cluster_data = (
        compute_author_cluster_counts(df_result, chosen_k)
        if 'author' in df_result.columns else []
    )

    means_df = pd.DataFrame([{
        'Кластер': r['cluster'],
        'I (iktus_1)': r['iktus_1'],
        'II (iktus_2)': r['iktus_2'],
        'III (iktus_3)': r['iktus_3'],
        'IV (iktus_4)': r['iktus_4'],
    } for r in cluster_means])
    means_output = BytesIO()
    with pd.ExcelWriter(means_output, engine='openpyxl') as writer:
        means_df.to_excel(writer, index=False)
    means_output.seek(0)
    means_b64 = base64.b64encode(means_output.read()).decode('ascii')

    ctx = dict(
        scores=scores, chosen_k=chosen_k, chosen_score=chosen_score,
        file_b64=file_b64, download_name=download_name,
        cluster_means=cluster_means,
        author_cluster_data=author_cluster_data,
        means_b64=means_b64,
        means_download_name=f'{stem}_cluster_means.xlsx',
    )

    if is_htmx(request):
        return render_template('_cluster_result.html', **ctx)
    return render_template('cluster.html', result=ctx, n_clusters=n_clusters)


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
