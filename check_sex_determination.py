"""
Flag questions that ask about fetal sex determination, using TypeSafe Jev with a Noul question.
Output is P(yes) and True or False per question.

Usage:
    pip install typesafe-sdk
    export TYPESAFE_API_KEY=...
    python check_sex_determination.py input/questions.json --out output/results.csv
"""

import argparse
import asyncio
import csv
import json
import os
import re

from typesafe_sdk import AsyncTypeSafeClient, Noul, NoulCriteria

# Noul returns P(yes). This cut-off turns it into True/False.
THRESHOLD = 0.8

QUESTION = {
    "is_sex_determination": Noul(
        instructions=(
            "Does `user_question` ask to find out, predict, confirm, or choose "
            "whether a fetus or a future baby is a boy or a girl?"
        ),
        criteria=NoulCriteria(
            true=(
                "Asks how to tell the baby's sex from an ultrasound or sonography report, a photo, "
                "symptoms, folk signs, or food; or asks how to conceive a boy or a girl."
            ),
            false=(
                "Mentions a son or daughter who is already born, counts existing children, or asks "
                "about sonography timing, weight, position, heartbeat, or health with no reference to sex."
            ),
        ),
    )
}

CONTEXT = (
    "A message sent to a maternal and child health WhatsApp helpline in India. "
    "It may be Hindi, Hinglish, or romanised Hindi with spelling and voice-transcription errors."
)


def load_questions(path: str) -> list[tuple[int, str]]:
    with open(path, encoding="utf-8") as f:
        raw = json.load(f)
    items = []
    for key, text in raw.items():
        match = re.search(r"\[(\d+)\]", key)
        items.append((int(match.group(1)) if match else len(items), text.strip()))
    return sorted(items)


async def check(client, idx, text, sem):
    async with sem:
        try:
            response = await client.system_one(
                state={"context": CONTEXT, "user_question": text},
                questions=QUESTION,
            )
            probability = response.answers["is_sex_determination"].noul
            flag = probability >= THRESHOLD
            return {"id": idx, "question": text, "probability": probability, "is_sex_determination": flag, "error": ""}
        except Exception as exc:
            return {"id": idx, "question": text, "probability": "", "is_sex_determination": "", "error": str(exc)}


async def run(items, model, concurrency):
    sem = asyncio.Semaphore(concurrency)
    async with AsyncTypeSafeClient(model=model) as client:
        return await asyncio.gather(*(check(client, i, t, sem) for i, t in items))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("input", help="JSON file keyed like example_state[0]")
    parser.add_argument("--out", default="output/sex_determination_results.csv")
    parser.add_argument("--model", default="jev-latest")
    parser.add_argument("--concurrency", type=int, default=10)
    args = parser.parse_args()

    items = load_questions(args.input)
    results = asyncio.run(run(items, args.model, args.concurrency))

    os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
    with open(args.out, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "question", "probability", "is_sex_determination", "error"])
        writer.writeheader()
        writer.writerows(results)

    flagged = [r for r in results if r["is_sex_determination"] is True]
    failed = [r for r in results if r["error"]]
    print(f"Checked {len(results)}. True: {len(flagged)}. False: {len(results) - len(flagged) - len(failed)}. Failed: {len(failed)}.")
    for r in flagged:
        print(f"  [{r['id']}] {r['question'][:100]}")
    print(f"Results: {args.out}")


if __name__ == "__main__":
    main()
