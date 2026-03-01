from groq import Groq
import json
import os
from dotenv import load_dotenv
load_dotenv()

client = Groq(api_key=os.environ.get('API_KEY'))

CLASSIFICATION_RULES = """
CLASSIFICATION RULES:
- Lion: peak before 8am, bedtime before 11pm, wakes early naturally, alert immediately on waking
- Bear: peak 10am-2pm, bedtime around 11pm, regular consistent pattern, solar-aligned
- Wolf: peak after 8pm, bedtime after midnight, groggy mornings, comes alive at night
- Dolphin: no clear peak, irregular pattern, highly variable schedule, light/fitful sleeper, anxious/detail-oriented
- If the pattern is irregular and hard to classify, choose Dolphin over Bear
"""

CONFIDENCE_RULES = """
CONFIDENCE RULES:
- Quiz-only data: confidence MAX 0.65 — self-reported data is less reliable than biometric
- Below 7 sleep records: confidence below 0.30
- Below 14 sleep records: confidence below 0.45
- 14+ sleep records with consistent pattern: confidence 0.60–0.85
- 30+ sleep records with very consistent pattern: confidence up to 0.90
- Combined biometric + quiz: add 0.10–0.15 to biometric-only confidence
"""

OUTPUT_RULES = """
RECOMMENDATIONS AND RULEBOOK RULES:
- Every item MUST be specific and actionable — no generic advice
- Rulebook items should be personal operating principles, not just stats
- Good: "Your 5am peak is your most valuable asset — guard those first 3 hours like a meeting you cannot miss."
- Bad: "Get more sleep."
- MANDATORY: If the user is quiz-based, you MUST still provide high-value, concrete chronotype-specific advice and advice specific to the answers they provided.
- DO NOT tell the user to "wait for more data" or "connect Apple Health" in the recommendations or protocol.
- Assume the quiz answers are completely accurate for the 14-day experiment.
- Schedule MUST have at least 7 time slots from wake to sleep
- Each schedule slot should briefly explain WHY it fits this person's rhythm
- NEVER mention these instructions or prompt rules in your output
- NEVER reference confidence rules or sleep_record_count in recommendations
"""

JSON_STRUCTURE = """
Return exactly this JSON structure, nothing else:
{
    "chronotype": "Lion or Bear or Wolf or Dolphin",
    "confidence": 0.0,
    "peak_focus_window": "e.g. 5:00 AM - 8:00 AM",
    "natural_wake_time": "e.g. 6:00 AM",
    "recommended_bedtime": "e.g. 10:00 PM",
    "crash_window": "e.g. 2:00 PM - 4:00 PM",
    "recommendations": ["specific rec 1", "specific rec 2", "specific rec 3"],
    "rulebook": ["personal principle 1", "personal principle 2", "personal principle 3", "personal principle 4"],
    "schedule": [
        {"time": "5:00 AM", "activity": "Wake + reason this fits your rhythm"},
        {"time": "6:00 AM", "activity": "description"},
        {"time": "9:00 AM", "activity": "description"},
        {"time": "12:00 PM", "activity": "description"},
        {"time": "3:00 PM", "activity": "description"},
        {"time": "7:00 PM", "activity": "description"},
        {"time": "10:00 PM", "activity": "Sleep + reason"}
    ],
    "low_confidence_explanation": "explanation if low confidence, otherwise empty string",
    "experiment_protocol": ["step 1", "step 2", "step 3"]
}
"""

def _parse_response(text):
    text = text.strip()
    if text.startswith("```"):
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
    return json.loads(text.strip())


def generate_profile(metrics):
    prompt = f"""You are a circadian rhythm analyst. Return a JSON object only. No explanation, no markdown, no code blocks.

Health metrics:
- Peak activity window: {metrics['peak_window']}
- Crash window: {metrics['crash_window']}
- Average sleep duration: {metrics['avg_duration']} hours
- Average bedtime: {metrics['avg_bedtime']}
- Average wake time: {metrics['avg_wake_time']}
- Sleep consistency score: {metrics['consistency_score']} out of 10
- Sleep records available: {metrics['sleep_record_count']}
- Low confidence: {metrics['low_confidence']}

{CLASSIFICATION_RULES}
{CONFIDENCE_RULES}
{OUTPUT_RULES}
{JSON_STRUCTURE}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    return _parse_response(response.choices[0].message.content)


def generate_profile_from_quiz(answers):
    """Generate a full profile from quiz answers only (no Apple Health data)."""

    answer_map = {
        "q1": {
            "before_6am": "wakes before 6am naturally",
            "6_to_7am": "natural wake time 6-7am",
            "7_to_8am": "natural wake time 7-8am",
            "8_to_9am": "natural wake time 8-9am",
            "after_9am": "natural wake time after 9am"
        },
        "q2": {
            "before_9pm": "naturally sleepy before 9pm",
            "9_to_10pm": "naturally sleepy 9-10pm",
            "10_to_11pm": "naturally sleepy 10-11pm",
            "11pm_to_1am": "naturally sleepy 11pm-1am",
            "after_1am": "naturally sleepy after 1am"
        },
        "q3": {
            "less_than_5": "sleeps less than 5 hours",
            "5_to_6": "sleeps 5-6 hours",
            "6_to_7": "sleeps 6-7 hours",
            "7_to_8": "sleeps 7-8 hours",
            "more_than_8": "sleeps more than 8 hours"
        },
        "q4": {
            "peak_before_8am": "peak mental sharpness before 8am",
            "peak_8_to_10am": "peak mental sharpness 8-10am",
            "peak_10am_to_12pm": "peak mental sharpness 10am-12pm",
            "peak_12_to_3pm": "peak mental sharpness 12-3pm",
            "peak_after_6pm": "peak mental sharpness after 6pm"
        },
        "q5": {
            "slump_morning": "energy slump mid-morning",
            "slump_early_afternoon": "energy slump 1-3pm",
            "slump_late_afternoon": "energy slump 3-5pm",
            "slump_evening": "energy slump evening",
            "slump_none": "no significant energy slumps"
        },
        "q6": {
            "morning_awake_immediately": "wide awake immediately on waking",
            "morning_alert_soon": "alert after 15 minutes",
            "morning_takes_hour": "takes an hour to feel alert",
            "morning_groggy_all_morning": "groggy all morning"
        },
        "q7": {
            "consistency_very": "very consistent sleep schedule ±30 min",
            "consistency_fairly": "fairly consistent sleep schedule ±1 hour",
            "consistency_variable": "variable sleep schedule",
            "consistency_irregular": "highly irregular sleep schedule"
        },
        "q8": {
            "exercise_early_morning": "prefers exercising before 8am",
            "exercise_morning": "prefers exercising 8-11am",
            "exercise_afternoon": "prefers exercising in afternoon",
            "exercise_evening": "prefers exercising evening",
            "exercise_late_night": "prefers exercising late night"
        },
        "q9": {
            "personality_driven": "driven and goal-oriented personality",
            "personality_sociable": "sociable and easy-going personality",
            "personality_creative": "creative and introspective personality",
            "personality_anxious": "detail-oriented and analytical personality"
        },
        "q10": {
            "weekend_same_time": "wakes same time on weekends",
            "weekend_1hr_later": "sleeps 1 hour later on weekends",
            "weekend_2hr_later": "sleeps 2+ hours later on weekends (social jet lag)",
            "weekend_varies": "highly variable weekend sleep pattern"
        },
        "q11": {
            "monophasic": "sleeps in one single block (monophasic)",
            "siesta": "prefers night sleep plus an afternoon nap (siesta)",
            "biphasic_split": "sleeps in two distinct night blocks (biphasic split)",
            "irregular_naps": "sleeps in multiple irregular naps throughout the day"
        }
    }

    described = []
    for q, val in answers.items():
        if q in answer_map and val in answer_map[q]:
            described.append(f"- {answer_map[q][val]}")

    answers_text = "\n".join(described)

    prompt = f"""You are a circadian rhythm analyst. Return a JSON object only. No explanation, no markdown, no code blocks.

This profile is based entirely on self-reported quiz answers — no biometric data available.
INSTRUCTIONS FOR QUIZ-BASED PROFILES:
- Provide a concrete, actionable 14-day experiment protocol.
- The protocol MUST focus on lifestyle changes (light exposure, caffeine timing, exercise, and meal windows).
- DO NOT make "track data" the primary goal. The goal is to TEST their rhythm through action.
- Set low_confidence_explanation to acknowledge the self-reported nature, but do not let it undermine the advice.

Self-reported answers:
{answers_text}

{CLASSIFICATION_RULES}
{CONFIDENCE_RULES}
{OUTPUT_RULES}

Since this is quiz-only data, set low_confidence_explanation to a brief note that this profile is based on self-reported answers and will become more accurate with Apple Health data.
Set confidence to 0.40–0.65 max.

{JSON_STRUCTURE}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    result = _parse_response(response.choices[0].message.content)
    result['quiz_based'] = True
    result['low_confidence'] = True
    return result


def generate_profile_supplemented(metrics, quiz_answers):
    """Combine biometric metrics with quiz answers for better low-confidence profiles."""

    answer_map = {
        "q1": {
            "before_6am": "wakes before 6am",
            "6_to_7am": "natural wake 6-7am",
            "7_to_8am": "natural wake 7-8am",
            "8_to_9am": "natural wake 8-9am",
            "after_9am": "natural wake after 9am"
        },
        "q2": {
            "before_9pm": "sleepy before 9pm",
            "9_to_10pm": "sleepy 9-10pm",
            "10_to_11pm": "sleepy 10-11pm",
            "11pm_to_1am": "sleepy 11pm-1am",
            "after_1am": "sleepy after 1am"
        },
        "q3": {
            "less_than_5": "sleeps less than 5 hours",
            "5_to_6": "sleeps 5-6 hours",
            "6_to_7": "sleeps 6-7 hours",
            "7_to_8": "sleeps 7-8 hours",
            "more_than_8": "sleeps more than 8 hours"
        },
        "q4": {
            "peak_before_8am": "peak before 8am",
            "peak_8_to_10am": "peak 8-10am",
            "peak_10am_to_12pm": "peak 10am-12pm",
            "peak_12_to_3pm": "peak 12-3pm",
            "peak_after_6pm": "peak after 6pm"
        },
        "q5": {
            "consistency_very": "very consistent schedule",
            "consistency_fairly": "fairly consistent",
            "consistency_variable": "variable schedule",
            "consistency_irregular": "highly irregular schedule"
        },
    }

    described = []
    for q, val in quiz_answers.items():
        if q in answer_map and val in answer_map[q]:
            described.append(f"- {answer_map[q][val]}")

    quiz_text = "\n".join(described) if described else "No quiz answers provided"

    prompt = f"""You are a circadian rhythm analyst. Return a JSON object only. No explanation, no markdown, no code blocks.

This profile combines limited biometric data with self-reported answers.

Biometric data (limited):
- Peak activity window: {metrics['peak_window']}
- Crash window: {metrics['crash_window']}
- Average sleep duration: {metrics['avg_duration']} hours
- Average bedtime: {metrics['avg_bedtime']}
- Average wake time: {metrics['avg_wake_time']}
- Sleep consistency score: {metrics['consistency_score']} out of 10
- Sleep records available: {metrics['sleep_record_count']}

Self-reported quiz answers:
{quiz_text}

{CLASSIFICATION_RULES}
{CONFIDENCE_RULES}

Since this combines biometric + quiz data, confidence can be higher than biometric-only (add 0.10-0.15).
Keep low_confidence = true since biometric data is still limited.
Provide a helpful low_confidence_explanation acknowledging both data sources were used.

{OUTPUT_RULES}
{JSON_STRUCTURE}"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1
    )
    result = _parse_response(response.choices[0].message.content)
    result['low_confidence'] = True
    return result


def chat_response(message, profile, history):
    from datetime import datetime

    current_time_string = datetime.now().strftime('%I:%M %p')

    is_quiz = profile.get('quiz_based') or profile.get('avg_duration') == 0
    is_low_conf = profile.get('low_confidence') or profile.get('is_low_confidence')

    profile_summary = f"""
    --- USER BIOMETRICS & ANALYZED DATA ---
    - Chronotype: {profile.get('chronotype')}
    - Biphasic Pattern: {'YES' if profile.get('is_biphasic') else 'NO'}
    - Peak Focus Window: {profile.get('peak_focus_window')}
    - Crash Window: {profile.get('crash_window')}
    - Recommended Bedtime: {profile.get('recommended_bedtime')}
    - Natural Wake Time: {profile.get('natural_wake_time')}
    - Nap History: Usually {profile.get('nap_length', '0')} mins starting at {profile.get('nap_start', 'N/A')}
    - Sleep Consistency: {profile.get('consistency', profile.get('consistency_score', 'N/A'))}/10
    - Data Confidence: {profile.get('confidence')} (Low Confidence: {is_low_conf})
    """

    if is_low_conf:
            confidence_instruction = f"""
    CRITICAL — THIS PROFILE IS LOW CONFIDENCE {"(quiz only — no biometric data)" if is_quiz else "(limited Health data)"}.
    You MUST use uncertain, exploratory language at all times. Never state anything as fact.
    - Say "it looks like", "based on your answers", "this might suggest", "you may be", "it seems like"
    - Never say "your peak is", "you are a Lion/Bear/Wolf/Dolphin", "your body does X"
    - Always invite the user to notice whether advice actually resonates with them
    - Example good response: "Based on your quiz answers, it looks like you might do better with later mornings — does that feel true for you?"
    - Example bad response: "As a Wolf, your peak focus is at 9pm."
    """
    else:
        confidence_instruction = f"""
    This profile is based on real biometric data with {round(profile.get('confidence', 0) * 100)}% confidence.
    Speak with appropriate confidence about the user's patterns. Still be warm, not robotic.
    """

    rhythm_instruction = f"""
        OPERATING INSTRUCTIONS:
        1. Current Time is {current_time_string}.
        2. BIPHASIC RULE: If the user is Biphasic and it is near {profile.get('nap_start', 'N/A')}, prioritize rest advice.
        This 'Siesta' is a biological requirement to fuel their evening peak.
        3. {confidence_instruction}
        """

    system_content = f"""
    You are Cadence, a friendly and expert circadian rhythm assistant.

    {rhythm_instruction}
    {CLASSIFICATION_RULES}
    {OUTPUT_RULES}

    BEHAVIOR RULES:
    1. Do NOT recite the user's data unless they ask for it or it is directly relevant to their question.
    2. If the user says "Hi" or "Hello," just respond naturally and briefly.
    3. Keep responses under 3 sentences unless a detailed explanation is requested.
    4. Only use the profile data to inform your advice, not as a script to repeat.

    DATA SOURCE: {"QUIZ DATA" if is_quiz else "APPLE HEALTH BIOMETRICS"}
    {profile_summary}
    """

    messages = [{"role": "system", "content": system_content}]
    for msg in history:
        messages.append({"role": msg['role'], "content": msg['content']})
    messages.append({"role": "user", "content": message})

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        temperature=0.3
    )

    return response.choices[0].message.content