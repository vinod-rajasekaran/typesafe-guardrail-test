# Adherence evaluation: Jev vs kaapi judge

**Run:** evaluation 288 in kaapi, 42 questions, SNEHA DIDI system prompt, `jev-latest`, 29 Sep 2026.
**Data:** `adherence_results.csv` in this folder, made by `../evaluate_adherence.py`.

## Question

The team thinks kaapi's LLM judge gives scores that are too high. We scored the same 42 answers with TypeSafe Jev, using the same rubrics as kaapi, to see whether Jev gives lower scores.

## Method

- Two metrics, both taken from kaapi-backend's [`judge_prompts.py`](https://github.com/ProjectTech4DevAI/kaapi-backend/blob/main/backend/app/crud/evaluations/judge_prompts.py):
  - **Adherence to Ground Truth:** Jev sees the question, the assistant answer, and the expected answer.
  - **Adherence to Prompt:** Jev sees the system prompt, the question, and the assistant answer.
- Each metric is a Jev `Score` question with six levels (0 to 5), using kaapi's level descriptions. Each metric is a separate call, so Jev sees only the inputs that kaapi's judge uses for that metric.
- **Adherence to Knowledge Base is not scored.** The export has no retrieved chunks, and 3 rows have no kaapi score for it.
- Jev returns a probability for each level. We compare with kaapi's score in three ways:
  - Jev's **expected score**: the average of the levels, weighted by their probabilities.
  - Jev's **most likely level**: the level with the highest probability.
  - **How much probability Jev gives** to kaapi's score, to the levels below it, and to the levels above it.

## Summary

| | Ground Truth | Prompt |
|---|---|---|
| Average score, kaapi | 3.57 | 4.19 |
| Average expected score, Jev | 3.09 | 3.14 |
| Jev's most likely level vs kaapi's score: lower / same / higher | 19 / 18 / 5 | 32 / 7 / 3 |
| Jev's probability on kaapi's score | 0.39 | 0.22 |
| Jev's probability on levels **below** kaapi's score | **0.48** | **0.66** |
| Jev's probability on levels above kaapi's score | 0.14 | 0.13 |
| Exact match, expected score rounded | 48% | 19% |
| Within 1 point, expected score rounded | 90% | 55% |
| Exact match, most likely level | 43% | 17% |
| Mean absolute error (expected score vs kaapi) | 0.66 | 1.27 |
| Spearman rank correlation | 0.78 | 0.40 |
| Average Jev confidence | 0.59 | 0.36 |

**Finding:** on both metrics, Jev scores lower than kaapi much more often than higher. The evidence is strong for Ground Truth and weaker for Prompt, because Jev scores the Prompt metric unreliably.

## Adherence to Ground Truth

Rows are grouped by kaapi's score:

| Kaapi score | Rows | Jev expected score | Jev's probability on kaapi's score | Jev's probability below kaapi's score |
|---|---|---|---|---|
| 0 | 1 | 0.12 | 0.93 | 0.00 |
| 1 | 2 | 1.47 | 0.37 | 0.29 |
| 2 | 3 | 1.92 | 0.31 | 0.36 |
| 3 | 12 | 2.66 | 0.43 | 0.47 |
| 4 | 14 | 3.40 | 0.19 | 0.61 |
| 5 | 10 | 4.14 | 0.58 | 0.42 |

- **Jev ranks the answers in nearly the same order as kaapi** (Spearman 0.78), and 90% of rows are within 1 point. Both judges agree on which answers are better.
- **The gap is close to zero for poor answers and about 0.5–0.9 points for good ones.** Kaapi is more generous at the top of the scale.
- **The 4s show the gap most clearly.** When kaapi gave a 4, Jev put only 0.19 probability on 4 and 0.61 below it. Jev's most likely level was 4 for only 1 answer out of 42, so its scores split between "3: a material fact missing" and "5: complete". Many of kaapi's 4s look like 3s to Jev.
- **Kaapi's 5s hold up better.** Jev gave them 0.58 probability on 5, but still put 0.42 below.

Largest disagreements:

| Row | Question | Jev | Kaapi |
|---|---|---|---|
| 35 | Meri ladki dhai sal ki hai usko Paisa nahin mila hai ab | 2.62 | 5 |
| 31 | Mera babu kamzor h use kanch m rakha h | 3.29 | 5 |
| 21 | pregnancy me mujhe konsi yojana ka labh milega | 2.33 | 4 |
| 9 | bache ka wajan kitna hona chahiye | 2.38 | 4 |
| 4 | Tikkaran kyu jaruri hai | 2.66 | 4 |
| 37 | 8 months pregnancy diet chart do | 0.85 | 2 |

## Adherence to Prompt

Rows are grouped by kaapi's score:

| Kaapi score | Rows | Jev expected score | Jev's probability on kaapi's score | Jev's probability below kaapi's score |
|---|---|---|---|---|
| 1 | 2 | 3.25 | 0.05 | 0.01 |
| 3 | 9 | 2.71 | 0.27 | 0.50 |
| 4 | 8 | 3.15 | 0.20 | 0.62 |
| 5 | 23 | 3.30 | 0.22 | 0.78 |

- **Kaapi gave a 5 to 23 of the 42 answers. Jev puts 0.78 of its probability below 5 on those rows.** Jev's most likely level was 2 for 19 answers and 3 for 16, so it rarely thinks an answer follows the prompt fully.
- **But Jev hardly tells answers apart on this metric.** Its expected scores range only from 2.27 to 4.49, the average barely changes across kaapi's score groups (2.71 to 3.30), and its confidence is low (0.36 on average, as low as 0.03).
- **On the 2 answers kaapi scored 1, Jev scores higher (3.25).** So Jev is not simply a stricter version of kaapi here.
- **Conclusion for this metric:** Jev's scores suggest kaapi gives too many 5s, but Jev's Prompt scores are too unreliable to prove it. A single score doesn't capture a prompt with about 15 separate rules.

Largest disagreements:

| Row | Question | Jev | Kaapi |
|---|---|---|---|
| 39 | Mera 15 January ko date aaya tha uske bad se kitne mahine hue hain | 3.49 | 1 |
| 14 | bacha kis month me movement karta hai | 2.70 | 5 |
| 0 | Mera Khoon 7 point hain khoon badhane ke liye kya karna hai | 2.77 | 5 |
| 16 | Caeser delivery k baad kya kha sakte hai or kya nahi kha sakte hai | 2.79 | 5 |
| 21 | pregnancy me mujhe konsi yojana ka labh milega | 2.84 | 5 |
| 26 | Abhi mujhe 1 month hua hai to mujhe khoon janch kab karni padegi | 2.88 | 5 |

## Caveats

- **Neither judge is the ground truth.** Jev scoring lower doesn't prove that kaapi is wrong. It only means two independent judges using the same rubric disagree in a consistent direction.
- **42 rows is a small sample.** Some kaapi score groups have only 1 to 3 rows.
- **Jev's results vary slightly between runs.** An earlier run of the same data gave Spearman 0.80 (Ground Truth) and 26% exact match (Prompt), compared with 0.78 and 19% here.
- **Knowledge Base adherence was not tested.**

## Next steps

- **Score by hand the rows where the judges disagree most** (the tables above) to see whether kaapi's high scores are earned. This is the only way to settle which judge is right.
- **Split the Prompt metric into specific rule checks**, using a `Noul` yes/no question for each rule. Examples: a numbered list was used; the English words "baby" or "iron" were used; the language and script match the user's; a refusal matched rule 7; the answer is longer than 5 lines. Then combine them into one score. We expect this to separate good answers from bad ones better, and it shows which rule was broken.
- **Rows where Jev's confidence is low** are a good shortlist for human review.
- **Include the retrieved chunks in the kaapi export** so that Knowledge Base adherence can also be compared.
