# Cadence

**Your phone has been tracking your body for years. It's time to listen**

Cadence analyzes your Apple Health data to discover your chronotype - your biological sleep-wake preference - and builds a personalized profile showing when your body is primed to focus, rest, and recover.

---

## Try It Live

🚀 **[cadence-chronotype.up.railway.app](https://cadence-chronotype.up.railway.app)** - no setup required!

---

## What It Does

Upload your Apple Health export and Cadence will:

- **Classify your chronotype** - Lion, Bear, Wolf, or Dolphin - based on your actual biometric patterns
- **Map your 24-hour energy curve** from step records
- **Analyze your sleep** - consistency, duration, bedtime pattern, and wake times
- **Detect biphasic sleep** -  if you're a natural napper, Cadence identifies it and optimizes your nap window
- **Generate a personalized profile** - recommendations, rulebook, and optimized daily schedule tailored to your rhythm
- **Handle low confidence data** - if your data is sparse, Cadence gives you a 2-week experiment to establish your rhythm
- **Chat with Cadence** - ask follow-up questions about your results using an AI assistant trained on your profile.
- **No Apple Health?** - take the chronotype quiz for a self-reported profile

---

## Chronotypes

|    Type    | Population | Peak Hours |    Bedtime    |
|------------|------------|------------|---------------|
|   🦁 Lion  |     15%    | 5am - 10am |    9-10:30pm  |
|   🐻 Bear  |     50%    | 10am - 2pm | 10:30-11:30pm |
|   🐺 Wolf  |     15%    | 7pm - 12am |   12-1:30am   |
| 🐬 Dolphin |     10%    | 10am - 2pm |     12-1am    |

---

## Tech Stack

- **Backend** - Python, Flask, SQLAlchemy, SQLite (local) / PostgreSQL (production)
- **AI** - Groq AI (LLaMA 3.3 70B) for chronotype classification and chat
- **Parsing** - Iterative XML parsing for large Apple Health exports (800MB+)
- **Frontend** - Vanilla HTML/CSS/JS, Chart.js, Tailwind CSS
- **Fonts** - Cormorant Garamond + Inter

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/t-skayemba/cadence.git
cd cadence
```

### 2. Install dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Set environment variables

Get a free API key at [console.groq.com](https://console.groq.com)

Copy the template file

```bash
cp .env.example .env
```
Open .env and replace your_groq_api_key_here with your actual key.


### 4. Run the app

```bash
python3 app.py
```

Visit `http://127.0.0.1:5000`

---

## How to Export Your Apple Health Data

1. Open the **Health** app on your iPhone
2. Tap your profile picture (top right)
3. Scroll down and tap **Export All Health Data**
4. Save the ZIP and upload it to Cadence

---

## Test Data
Sample exports are included in the `test_data/` folder:

## Test Data

|                       File                        | Chronotype |                   Notes                |
|---------------------------------------------------|-----------------|-----------------------------------|
|             `lion_high_confidence.zip`            |       Lion      |        90 days, early riser       |
|             `bear_high_confidence.zip`            |       Bear      |       90 days, solar-aligned      |
|             `wolf_high_confidence.zip`            |       Wolf      |         90 days, night owl        |
|           `bear_biphasic_short_naps.zip`          | Bear + Biphasic |          20–35 min naps           |
|           `lion_biphasic_long_naps.zip`           | Lion + Biphasic |          60–120 min naps          |
| `wolf_biphasic_medium_naps_medium_confidence.zip` | Wolf + Biphasic |     30 days, medium confidence    |
|            `bear_medium_confidence.zip`           |       Bear      |     21 days, medium confidence    |
|            `low_confidence_sparse.zip`            |     Unknown     | Triggers Mode 2 + quiz supplement |


## Project Structure

```
cadence/
├── app.py                    # Flask routes
├── parser.py                 # Apple Health XML parser
├── analyzer.py               # Metric computation
├── ai.py                     # Groq API integration
├── models.py                 # SQLAlchemy models
├── templates/
│   ├── index.html            # Landing page
│   ├── upload.html           # Upload page
│   ├── profile.html          # Profile dashboard
│   ├── chronotypes.html      # Chronotypes explainer
│   ├── quiz.html             # Chronotype quiz for non-Apple Health users
│   ├── quiz_supplement.html  # Supplement quiz for low confidence profiles
│   └── 404.html              # 404 error page
├── static/
│   ├── lion.png
│   ├── bear.png
│   ├── wolf.png
│   └── dolphin.png
├── test_data/                # Sample Apple Health exports
├── requirements.txt
└── .env                      # API key (not committed)
```
---

Built by [Tiana Shashi Kayemba](https://github.com/t-skayemba)

## License
MIT
