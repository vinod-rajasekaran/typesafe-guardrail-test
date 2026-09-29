# typesafe-guardrail-test

Experiments using the TypeSafe SDK (`Jev` model) on a maternal and child health WhatsApp helpline in India. Questions may be in Hindi, Hinglish, or romanised Hindi, often with spelling and voice-transcription errors.

Each use case has its own folder with its script plus `input/` and `output/` subfolders:

| Folder               | Use case                                                                 |
|----------------------|--------------------------------------------------------------------------|
| `sex_determination/` | Flag questions that ask about fetal sex determination (`Noul`)            |
| `adherence_eval/`    | Score chatbot answers for adherence to ground truth and prompt (`Score`) |

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install typesafe-sdk
export TYPESAFE_API_KEY=...
```

Run the scripts from the repo root. Default input and output paths resolve to each script's own folder.

## Sex determination

Flags user questions that ask about **fetal sex determination**, using a `Noul` yes/no question.

### How it works

`check_sex_determination.py` sends each question to TypeSafe with a single `Noul` question, `is_sex_determination`. The question asks whether the message tries to find out, predict, confirm, or choose the sex of a fetus or future baby.

- **True:** asks how to tell the baby's sex from an ultrasound or sonography report, a photo, symptoms, folk signs, or food; or asks how to conceive a boy or a girl.
- **False:** mentions a son or daughter who is already born, counts existing children, or asks about sonography timing, weight, position, heartbeat, or health without mentioning sex.

`Noul` returns P(yes). A question is flagged `True` when P(yes) ≥ `THRESHOLD` (default `0.8`, set in the script).

### Usage

```bash
python sex_determination/check_sex_determination.py sex_determination/input/questions.json
```

| Option          | Default                          | Description                     |
|-----------------|----------------------------------|---------------------------------|
| `input`         | (required)                       | JSON file of questions          |
| `--out`         | `sex_determination/output/sex_determination_results.csv` | Output CSV path (folder is created if missing) |
| `--model`       | `jev-latest`                     | TypeSafe model                  |
| `--concurrency` | `10`                             | Maximum parallel API requests   |

The script prints a summary (checked / True / False / failed) and lists the flagged questions.

### Input format

A JSON object whose keys contain a numeric index in brackets. The index becomes the row `id`:

```json
{
  "example_state[0]": "1.5 saal k bachhe ko oats khila skte h ya nhi",
  "example_state[1]": "Cervix ko normal size me lane ke liye kya kre delivery ke bad"
}
```

`sex_determination/input/questions.json` holds 200 sample questions.

> **Note:** All questions in `sex_determination/input/questions.json` are synthetically generated. They are not real user messages from the helpline.

### Output format

A UTF-8 CSV (with BOM, so it opens correctly in Excel) with these columns:

| Column                 | Description                                   |
|------------------------|-----------------------------------------------|
| `id`                   | Index taken from the input key                |
| `question`             | Question text                                 |
| `probability`          | P(yes) from `Noul`                            |
| `is_sex_determination` | `True` if `probability >= THRESHOLD`          |
| `error`                | Error message if the API call failed          |

### Files

- `sex_determination/check_sex_determination.py`: the classifier script
- `sex_determination/input/questions.json`: sample input (200 synthetic questions)
- `sex_determination/output/results.csv`, `sex_determination/output/sex_determination_results.csv`: outputs from earlier runs

## Adherence evaluation

Re-scores the answers from a kaapi evaluation run with Jev, and compares them with the kaapi LLM-judge scores. The chatbot is SNEHA DIDI; its system prompt is in `adherence_eval/input/sneha_didi_prompt.md`.

### How it works

`evaluate_adherence.py` asks two `Score` questions per row. The instructions and the six levels (0 to 5) come from kaapi-backend's [`judge_prompts.py`](https://github.com/ProjectTech4DevAI/kaapi-backend/blob/main/backend/app/crud/evaluations/judge_prompts.py).

- **`ground_truth`:** does the answer convey the same correct information as the expected answer? Jev sees the question, the assistant answer, and the expected answer.
- **`prompt`:** does the answer follow the system prompt? Jev sees the system prompt, the question, and the assistant answer.

Each metric is a separate API call, so each call sees only the inputs that kaapi's judge uses for that metric. **Adherence to Knowledge Base** is skipped, because the CSV does not include the retrieved chunks.

### Usage

```bash
python adherence_eval/evaluate_adherence.py            # all rows
python adherence_eval/evaluate_adherence.py --limit 3  # quick trial
```

| Option           | Default                                                     | Description                              |
|------------------|-------------------------------------------------------------|------------------------------------------|
| `--input`        | `adherence_eval/input/evaluation-288-question-level-results.csv` | kaapi question-level results CSV    |
| `--instructions` | `adherence_eval/input/sneha_didi_prompt.md`                 | The chatbot's system prompt              |
| `--out`          | `adherence_eval/output/adherence_results.csv`               | Output CSV path                          |
| `--model`        | `jev-latest`                                                | TypeSafe model                           |
| `--concurrency`  | `10`                                                        | Maximum parallel API requests            |
| `--limit`        | (all)                                                       | Only score the first N rows              |
| `--top`          | `5`                                                         | Largest disagreements to list per metric |

For each metric, the script prints how often Jev and kaapi agree exactly and within 1 point, the mean absolute error (MAE), and the Spearman rank correlation. It repeats the agreement figures using Jev's most likely level, counts how often that level is below, equal to, or above kaapi's score, and averages the probability Jev gives to kaapi's score, to levels below it, and to levels above it. It also lists the rows where they disagree most.

### Input format

The kaapi question-level results export, with these columns: `Question`, `Expected answer`, `Assistant answer`, `Adherence to Ground Truth`, `Adherence to Prompt`, `Adherence to Knowledge Base`.

### Output format

A UTF-8 CSV (with BOM) with `id`, `question` and `error`, plus these columns for each metric (`ground_truth`, `prompt`):

| Column                 | Description                                                  |
|------------------------|--------------------------------------------------------------|
| `<metric>_jev_score`   | Expected score from Jev (probability-weighted, can be fractional) |
| `<metric>_jev_rounded` | Jev score rounded to the nearest integer                     |
| `<metric>_jev_mode`    | Level with the highest probability (Jev's most likely level) |
| `<metric>_jev_confidence` | Jev's confidence in the score (0 to 1)                    |
| `<metric>_jev_probabilities` | Probability of each level 0 to 5, as JSON              |
| `<metric>_kaapi`       | Score from the kaapi judge                                   |
| `<metric>_diff`        | `jev_rounded - kaapi`                                        |
| `<metric>_mode_diff`   | `jev_mode - kaapi`                                           |
| `<metric>_p_kaapi`     | Probability Jev gives to kaapi's score                       |
| `<metric>_p_below_kaapi` | Probability Jev gives to levels below kaapi's score        |
