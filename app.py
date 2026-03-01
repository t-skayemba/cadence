from flask import Flask, render_template, request, session, jsonify, redirect
from datetime import datetime
import uuid
import json
import os

app = Flask(__name__)
app.secret_key = 'cadence-secret-key'
db_url = os.environ.get('DATABASE_URL', 'sqlite:///cadence.db')
if db_url.startswith('postgres://'):
    db_url = db_url.replace('postgres://', 'postgresql://', 1)
app.config['SQLALCHEMY_DATABASE_URI'] = db_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

from models import db, Profile
db.init_app(app)

with app.app_context():
    db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload():
    from parser import parse_health_export
    from analyzer import compute_all_metrics
    from ai import generate_profile

    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

    file = request.files['health_file']
    zip_path = os.path.join('/tmp', session['user_id'] + '_export.zip')
    file.save(zip_path)

    sleep, steps, hr = parse_health_export(zip_path)
    metrics = compute_all_metrics(sleep, steps, hr)
    ai_profile = generate_profile(metrics)

    profile = Profile(
        user_id=session['user_id'],
        created_at=datetime.now(),
        chronotype=ai_profile['chronotype'],
        confidence=ai_profile['confidence'],
        peak_focus_window=ai_profile['peak_focus_window'],
        natural_wake_time=ai_profile['natural_wake_time'],
        recommended_bedtime=ai_profile['recommended_bedtime'],
        crash_window=ai_profile['crash_window'],
        peak_hour=metrics['peak_hour'],
        crash_hour=metrics['crash_hour'],
        avg_duration=metrics['avg_duration'],
        avg_bedtime=metrics['avg_bedtime'],
        avg_wake_time=metrics['avg_wake_time'],
        consistency_score=metrics['consistency_score'],
        low_confidence=metrics['low_confidence'],
        recommendations=json.dumps(ai_profile['recommendations']),
        rulebook=json.dumps(ai_profile['rulebook']),
        schedule=json.dumps(ai_profile['schedule']),
        activity_distribution=json.dumps(metrics['activity_distribution']),
        low_confidence_explanation=ai_profile.get('low_confidence_explanation', ''),
        experiment_protocol=json.dumps(ai_profile.get('experiment_protocol', [])),
        sleep_by_day=json.dumps(metrics['sleep_by_day']),
        heatmap_data=json.dumps(metrics['heatmap_data']),
        is_biphasic=metrics['is_biphasic'],
        nap_metrics=json.dumps(metrics['nap_metrics']),
        sleep_record_count=metrics['sleep_record_count']
    )

    db.session.add(profile)
    db.session.commit()

    if profile.low_confidence:
        session['profile_id'] = profile.id
        target_url = '/quiz/supplement'
    else:
        target_url = f'/profile/{profile.id}'

    return jsonify({
        'success': True,
        'profile_id': profile.id,
        'redirect': target_url
    })

@app.route('/upload')
def upload_page():
    return render_template('upload.html')

@app.route('/profile/<int:profile_id>')
def profile_view(profile_id):
    user_profile = Profile.query.get(profile_id)
    if not user_profile:
        return redirect('/upload')

    json_fields = [
        'recommendations',
        'rulebook',
        'schedule',
        'experiment_protocol',
        'activity_distribution',
        'sleep_by_day',
        'heatmap_data',
        'nap_metrics'
    ]

    for field in json_fields:
        value = getattr(user_profile, field)
        if isinstance(value, str):
            try:
                setattr(user_profile, field, json.loads(value))
            except Exception:
                pass

    return render_template('profile.html', profile=user_profile)

@app.route('/chat', methods=['POST'])
def chat():
    from ai import chat_response
    data = request.get_json()
    message = data.get('message')
    profile_data = data.get('profile')
    history = data.get('history', [])

    response = chat_response(message, profile_data, history)
    return jsonify({'response': response})

@app.route('/chronotypes')
def chronotypes():
    user_id = session.get('user_id')
    latest_profile = None
    if user_id:
        latest_profile = Profile.query.filter_by(user_id=user_id).order_by(Profile.created_at.desc()).first()
    return render_template('chronotypes.html', profile=latest_profile.to_dict() if latest_profile else None)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('404.html'), 404

@app.route('/quiz')
def quiz():
    return render_template('quiz.html')

@app.route('/quiz/submit', methods=['POST'])
def quiz_submit():
    if 'user_id' not in session:
        session['user_id'] = str(uuid.uuid4())

    from ai import generate_profile_from_quiz
    answers = request.json
    ai_result = generate_profile_from_quiz(answers)

    profile = Profile(
        user_id=session['user_id'],
        created_at=datetime.now(),
        chronotype=ai_result.get('chronotype', 'Unknown'),
        confidence=ai_result.get('confidence', 0.5),
        peak_focus_window=ai_result.get('peak_focus_window', ''),
        natural_wake_time=ai_result.get('natural_wake_time', ''),
        recommended_bedtime=ai_result.get('recommended_bedtime', ''),
        crash_window=ai_result.get('crash_window', ''),
        peak_hour=0,
        crash_hour=0,
        recommendations=json.dumps(ai_result.get('recommendations', [])),
        rulebook=json.dumps(ai_result.get('rulebook', [])),
        schedule=json.dumps(ai_result.get('schedule', [])),
        low_confidence_explanation=ai_result.get('low_confidence_explanation', ''),
        experiment_protocol=json.dumps(ai_result.get('experiment_protocol', [])),
        activity_distribution=json.dumps([0] * 24),
        avg_duration=0,
        avg_bedtime='N/A',
        avg_wake_time='N/A',
        consistency_score=0,
        low_confidence=True,
        quiz_based=True,
        quiz_supplemented=False,
        sleep_by_day=json.dumps([0] * 7),
        heatmap_data=json.dumps([[0] * 24 for _ in range(7)]),
        is_biphasic=False,
        nap_metrics=json.dumps({'avg_nap_time': 'N/A', 'avg_nap_duration': 0}),
        sleep_record_count=0
    )

    db.session.add(profile)
    db.session.commit()

    session['profile_id'] = profile.id
    return jsonify({'redirect': f'/profile/{profile.id}'})

@app.route('/quiz/supplement')
def quiz_supplement():
    profile_id = session.get('profile_id')
    if not profile_id:
        return redirect('/upload')
    return render_template('quiz_supplement.html', profile_id=profile_id)

@app.route('/quiz/supplement/submit', methods=['POST'])
def quiz_supplement_submit():
    from ai import generate_profile_supplemented
    data = request.json
    quiz_answers = data.get('answers', {})
    profile_id = data.get('profile_id') or session.get('profile_id')

    profile = Profile.query.get(profile_id)
    if not profile:
        return jsonify({'error': 'Profile not found'}), 404

    metrics = {
        'peak_window': profile.peak_focus_window or 'Unknown',
        'crash_window': profile.crash_window or 'Unknown',
        'avg_duration': profile.avg_duration or 0,
        'avg_bedtime': profile.avg_bedtime or 'No data',
        'avg_wake_time': profile.avg_wake_time or 'No data',
        'consistency_score': profile.consistency_score or 0,
        'sleep_record_count': profile.sleep_record_count or 0,
        'low_confidence': True,
    }

    ai_result = generate_profile_supplemented(metrics, quiz_answers)

    profile.chronotype = ai_result.get('chronotype', profile.chronotype)
    profile.confidence = ai_result.get('confidence', profile.confidence)
    profile.peak_focus_window = ai_result.get('peak_focus_window', profile.peak_focus_window)
    profile.natural_wake_time = ai_result.get('natural_wake_time', profile.natural_wake_time)
    profile.recommended_bedtime = ai_result.get('recommended_bedtime', profile.recommended_bedtime)
    profile.crash_window = ai_result.get('crash_window', profile.crash_window)
    profile.recommendations = json.dumps(ai_result.get('recommendations', []))
    profile.rulebook = json.dumps(ai_result.get('rulebook', []))
    profile.schedule = json.dumps(ai_result.get('schedule', []))
    profile.low_confidence_explanation = ai_result.get('low_confidence_explanation', '')
    profile.experiment_protocol = json.dumps(ai_result.get('experiment_protocol', []))
    profile.quiz_supplemented = True

    db.session.commit()

    return jsonify({'redirect': f'/profile/{profile.id}'})

@app.route('/demo')
def demo_mode():
    from parser import parse_health_export
    from analyzer import compute_all_metrics
    from ai import generate_profile

    if 'user_id' not in session:
        session['user_id'] = "portfolio-demo-user"

    test_file_path = os.path.join(app.root_path, 'test_data', 'biphasic_bear_export.zip')

    if not os.path.exists(test_file_path):
        return "Demo file not found in test_data folder", 404

    sleep, steps, hr = parse_health_export(test_file_path)
    metrics = compute_all_metrics(sleep, steps, hr)
    ai_profile = generate_profile(metrics)

    profile = Profile(
        user_id=session['user_id'],
        created_at=datetime.now(),
        chronotype="Bear",
        is_biphasic=True,
        confidence=0.85,
        peak_focus_window=ai_profile['peak_focus_window'],
        natural_wake_time=ai_profile['natural_wake_time'],
        recommended_bedtime=ai_profile['recommended_bedtime'],
        crash_window=ai_profile['crash_window'],
        peak_hour=metrics['peak_hour'],
        crash_hour=metrics['crash_hour'],
        avg_duration=metrics['avg_duration'],
        avg_bedtime=metrics['avg_bedtime'],
        avg_wake_time=metrics['avg_wake_time'],
        consistency_score=metrics['consistency_score'],
        low_confidence=False,
        quiz_based=False,
        quiz_supplemented=False,
        recommendations=json.dumps(ai_profile['recommendations']),
        rulebook=json.dumps(ai_profile['rulebook']),
        schedule=json.dumps(ai_profile['schedule']),
        low_confidence_explanation=ai_profile.get('low_confidence_explanation', ''),
        experiment_protocol=json.dumps(ai_profile.get('experiment_protocol', [])),
        activity_distribution=json.dumps(metrics['activity_distribution']),
        sleep_by_day=json.dumps(metrics['sleep_by_day']),
        heatmap_data=json.dumps(metrics['heatmap_data']),
        nap_metrics=json.dumps(metrics['nap_metrics']),
        sleep_record_count=metrics['sleep_record_count']
    )

    db.session.add(profile)
    db.session.commit()

    return redirect(f'/profile/{profile.id}')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)