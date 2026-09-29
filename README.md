# typesafe-guardrail-test

Flags user questions that ask about **fetal sex determination**, using the TypeSafe SDK (`Jev` model with a `Noul` yes/no question).

The questions come from a maternal and child health WhatsApp helpline in India. They may be in Hindi, Hinglish, or romanised Hindi, often with spelling and voice-transcription errors.

## How it works

`check_sex_determination.py` sends each question to TypeSafe with a single `Noul` question, `is_sex_determination`. The question asks whether the message tries to find out, predict, confirm, or choose the sex of a fetus or future baby.

- **True:** asks how to tell the baby's sex from an ultrasound or sonography report, a photo, symptoms, folk signs, or food; or asks how to conceive a boy or a girl.
- **False:** mentions a son or daughter who is already born, counts existing children, or asks about sonography timing, weight, position, heartbeat, or health without mentioning sex.

`Noul` returns P(yes). A question is flagged `True` when P(yes) ≥ `THRESHOLD` (default `0.8`, set in the script).

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install typesafe-sdk
export TYPESAFE_API_KEY=...
```

## Usage

```bash
python check_sex_determination.py input/questions.json --out output/sex_determination_results.csv
```

| Option          | Default                          | Description                     |
|-----------------|----------------------------------|---------------------------------|
| `input`         | (required)                       | JSON file of questions          |
| `--out`         | `output/sex_determination_results.csv` | Output CSV path (folder is created if missing) |
| `--model`       | `jev-latest`                     | TypeSafe model                  |
| `--concurrency` | `10`                             | Maximum parallel API requests   |

The script prints a summary (checked / True / False / failed) and lists the flagged questions.

## Input format

A JSON object whose keys contain a numeric index in brackets. The index becomes the row `id`:

```json
{
  "example_state[0]": "1.5 saal k bachhe ko oats khila skte h ya nhi",
  "example_state[1]": "Cervix ko normal size me lane ke liye kya kre delivery ke bad"
}
```

`input/questions.json` holds 200 sample questions.

> **Note:** All questions in `input/questions.json` are synthetically generated. They are not real user messages from the helpline.

## Output format

A UTF-8 CSV (with BOM, so it opens correctly in Excel) with these columns:

| Column                 | Description                                   |
|------------------------|-----------------------------------------------|
| `id`                   | Index taken from the input key                |
| `question`             | Question text                                 |
| `probability`          | P(yes) from `Noul`                            |
| `is_sex_determination` | `True` if `probability >= THRESHOLD`          |
| `error`                | Error message if the API call failed          |

## Files

- `check_sex_determination.py`: the classifier script
- `input/questions.json`: sample input (200 synthetic questions)
- `output/results.csv`, `output/sex_determination_results.csv`: outputs from earlier runs
