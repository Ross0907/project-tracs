import os
import time
from flask import Flask, render_template, request, redirect, url_for, send_from_directory, flash
from werkzeug.utils import secure_filename

from image_processing import analyze_dent

app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 32 * 1024 * 1024  # 32MB upload limit
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(__file__), 'uploads')
app.config['STATIC_RESULT_FOLDER'] = os.path.join(os.path.dirname(__file__), 'static', 'results')
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret')

os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
os.makedirs(app.config['STATIC_RESULT_FOLDER'], exist_ok=True)


@app.get('/healthz')
def healthz():
    return {'status': 'ok'}, 200


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        # The user requested: first = with defects, second = without defects
        dented_file = request.files.get('with_defects')
        perfect_file = request.files.get('without_defects')

        if not dented_file or not perfect_file:
            flash('Please provide both images (with defects and without defects).', 'error')
            return redirect(url_for('index'))

        # Save uploads
        timestamp = str(int(time.time()))
        dented_name = secure_filename(f"dented_{timestamp}_" + (dented_file.filename or 'dented.jpg'))
        perfect_name = secure_filename(f"perfect_{timestamp}_" + (perfect_file.filename or 'perfect.jpg'))
        dented_path = os.path.join(app.config['UPLOAD_FOLDER'], dented_name)
        perfect_path = os.path.join(app.config['UPLOAD_FOLDER'], perfect_name)
        dented_file.save(dented_path)
        perfect_file.save(perfect_path)

        # Output goes to static results so it can be served
        out_name = f"profile_comparison_{timestamp}.jpg"
        out_path = os.path.join(app.config['STATIC_RESULT_FOLDER'], out_name)

        # NOTE: analyze_dent expects (perfect_image_path, dented_image_path)
        # Mapping per the user's instruction (first input is with defects)
        try:
            result_path, processing_time = analyze_dent(
                perfect_image_path=perfect_path,
                dented_image_path=dented_path,
                show_plot=False,
                output_path=out_path,
            )
        except Exception as e:
            flash(f'Processing failed: {e}', 'error')
            return redirect(url_for('index'))

        # Render the page with the generated image
        result_url = url_for('static', filename=f'results/{out_name}')
        return render_template('poc.html',
                               result_url=result_url,
                               processing_time=f"{processing_time:.2f}")

    # GET
    return render_template('poc.html')


if __name__ == '__main__':
    # Run on localhost:5000
    app.run(host='127.0.0.1', port=5000, debug=True)
