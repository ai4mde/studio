#!/usr/bin/env python3
"""
Generate and publish an evaluation study on Maze.co.

The study mirrors the six questionnaire categories from the thesis
(Section 3.5):
  1. Object-centric navigation
  2. Role separation
  3. Workflow support
  4. Overall usability
  5. AI candidate diversity
  6. Human-in-the-loop regeneration

Usage
-----
Publish to Maze (requires a Maze API key):
    python scripts/create_maze_evaluation.py \\
        --api-key YOUR_MAZE_API_KEY \\
        --prototype-url https://your-platform.com/prototype/123/

Write JSON to disk without calling Maze:
    python scripts/create_maze_evaluation.py \\
        --dry-run \\
        --prototype-url https://your-platform.com/prototype/123/ \\
        --output evaluation_maze.json

Maze API reference:  https://api.maze.co/
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from typing import Any

try:
    import requests
except ImportError:
    requests = None  # type: ignore[assignment]

# ---------------------------------------------------------------------------
# Maze API helpers
# ---------------------------------------------------------------------------

MAZE_API_BASE = "https://api.maze.co/v1"
MAZE_API_VERSION = "2024-01-01"


def _headers(api_key: str) -> dict[str, str]:
    return {
        "api-key": api_key,
        "maze-version": MAZE_API_VERSION,
        "Content-Type": "application/json",
    }


def _post(api_key: str, path: str, body: dict) -> dict:
    if requests is None:
        raise RuntimeError("Install 'requests' to upload: pip install requests")
    url = f"{MAZE_API_BASE}{path}"
    resp = requests.post(url, headers=_headers(api_key), json=body, timeout=30)
    if not resp.ok:
        raise RuntimeError(f"Maze API error {resp.status_code}: {resp.text}")
    return resp.json()


# ---------------------------------------------------------------------------
# Questionnaire definition
# ---------------------------------------------------------------------------

STUDY_TITLE = "AI-driven UI Generation from UML Models — Evaluation"

INTRODUCTION_TEXT = (
    "Thank you for participating in this study.\n\n"
    "You will interact with an AI-generated web prototype that was produced "
    "from a UML model, then answer a short questionnaire about your experience.\n\n"
    "Please complete the assigned tasks in the prototype first, then proceed "
    "to the questions below.\n\n"
    "All responses are anonymous and used only for academic research."
)

SCALE_LABELS = {
    "left_label":  "Strongly disagree",
    "right_label": "Strongly agree",
    "steps": 5,
}

# Each entry: (category_heading, [statement, ...])
LIKERT_CATEGORIES: list[tuple[str, list[str]]] = [
    (
        "Object-Centric Navigation",
        [
            "The interface was organised around the domain objects I needed to work with "
            "(e.g. orders, books, applications).",
            "It was easy to navigate between related objects in the system.",
            "The interface made clear which domain object I was currently interacting with.",
            "Related objects were reachable from the relevant page without unnecessary steps.",
        ],
    ),
    (
        "Role Separation",
        [
            "The interface showed only the features and data relevant to my role.",
            "I could easily identify which actions were available to me as this type of user.",
            "Role-specific views were clear and did not contain irrelevant information.",
        ],
    ),
    (
        "Workflow Support",
        [
            "The interface guided me through the workflow steps in a logical order.",
            "It was clear what the next step was during the workflow.",
            "The interface provided appropriate inputs and forms at each workflow stage.",
            "Completing a multi-step workflow felt natural in this interface.",
        ],
    ),
    (
        "Overall Usability",
        [
            "I found the interface easy to use overall.",
            "The layout of information on each page was clear and well-organised.",
            "I could complete my tasks without confusion or errors.",
            "I would be comfortable using an interface like this for daily work.",
        ],
    ),
    (
        "AI Candidate Diversity",
        [
            "The generated interface candidates were visually distinct from each other.",
            "The different candidates offered meaningful variation in layout and style.",
            "The range of generated candidates gave me useful options to choose from.",
        ],
    ),
    (
        "Human-in-the-Loop Regeneration",
        [
            "The feedback-based regeneration produced results that reflected my input.",
            "I was able to guide the interface in the direction I wanted through natural language.",
            "The regenerated candidates improved upon the previous version.",
            "The human-in-the-loop mechanism was a useful way to refine the interface.",
        ],
    ),
]

OPEN_ENDED_QUESTIONS: list[str] = [
    "Which elements of the generated interface were confusing or unclear? (optional)",
    "Which features or aspects of the interface did you find most useful? (optional)",
    "What limitations did you notice in the generated interfaces? (optional)",
    "Any additional comments or suggestions? (optional)",
]


# ---------------------------------------------------------------------------
# Block builders
# ---------------------------------------------------------------------------

def _context_block(title: str, text: str) -> dict[str, Any]:
    return {
        "type": "context_screen",
        "title": title,
        "content": text,
    }


def _opinion_scale_block(question: str) -> dict[str, Any]:
    return {
        "type": "opinion_scale",
        "question": question,
        "left_label": SCALE_LABELS["left_label"],
        "right_label": SCALE_LABELS["right_label"],
        "steps": SCALE_LABELS["steps"],
        "required": True,
    }


def _open_question_block(question: str) -> dict[str, Any]:
    return {
        "type": "open_question",
        "question": question,
        "required": False,
    }


def _prototype_task_block(prototype_url: str) -> dict[str, Any]:
    return {
        "type": "prototype_task",
        "prototype": {
            "type": "web",
            "url": prototype_url,
        },
        "task_description": (
            "Explore the generated web interface. "
            "Complete the following tasks:\n"
            "1. Navigate through the main pages of the interface.\n"
            "2. Use the role-specific sections that apply to your assigned role.\n"
            "3. Complete one full workflow if available (e.g. submitting a form or "
            "processing an item through its stages).\n"
            "4. Inspect the AI-generated candidate variants and select one you prefer.\n"
            "5. Use the feedback panel to request one regeneration.\n\n"
            "When you have finished exploring, click the button below to continue."
        ),
    }


# ---------------------------------------------------------------------------
# Full study assembly
# ---------------------------------------------------------------------------

def build_maze_payload(prototype_url: str) -> dict[str, Any]:
    """Return the full study payload as a dict."""
    blocks: list[dict[str, Any]] = []

    # Introduction
    blocks.append(_context_block("Welcome", INTRODUCTION_TEXT))

    # Prototype task
    blocks.append(_prototype_task_block(prototype_url))

    # Likert categories
    for heading, statements in LIKERT_CATEGORIES:
        blocks.append(_context_block(heading, f"Please rate the following statements about {heading.lower()}."))
        for statement in statements:
            blocks.append(_opinion_scale_block(statement))

    # Open-ended
    blocks.append(_context_block("Open Feedback", "The following questions are optional. Please share any additional thoughts."))
    for question in OPEN_ENDED_QUESTIONS:
        blocks.append(_open_question_block(question))

    # Closing screen
    blocks.append(_context_block(
        "Thank you!",
        "Your responses have been recorded. Thank you for taking part in this evaluation."
    ))

    return {
        "maze": {
            "name": STUDY_TITLE,
            "status": "draft",
        },
        "blocks": blocks,
    }


# ---------------------------------------------------------------------------
# Maze API upload
# ---------------------------------------------------------------------------

def upload_to_maze(api_key: str, prototype_url: str) -> str:
    """Create the maze and all blocks. Returns the maze share URL."""
    payload = build_maze_payload(prototype_url)

    print("Creating maze...")
    maze_resp = _post(api_key, "/mazes", payload["maze"])
    maze_uid = maze_resp["maze"]["uid"]
    print(f"  Created maze uid: {maze_uid}")

    print(f"Adding {len(payload['blocks'])} blocks...")
    for i, block in enumerate(payload["blocks"], 1):
        _post(api_key, f"/mazes/{maze_uid}/blocks", block)
        print(f"  Block {i}/{len(payload['blocks'])}: {block['type']} — {block.get('question') or block.get('title', '')[:60]}")
        time.sleep(0.15)  # stay within Maze's rate limit

    share_url = f"https://app.maze.co/mazes/{maze_uid}/share"
    print(f"\nDone! Share URL: {share_url}")
    return share_url


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a Maze evaluation study for the thesis.")
    parser.add_argument("--api-key", help="Maze API key (not needed with --dry-run)")
    parser.add_argument(
        "--prototype-url",
        default="https://example.com/prototype/",
        help="URL of the deployed prototype participants will test",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write JSON to disk instead of uploading to Maze",
    )
    parser.add_argument(
        "--output",
        default="evaluation_maze.json",
        help="Output file for --dry-run (default: evaluation_maze.json)",
    )
    args = parser.parse_args()

    if args.dry_run:
        payload = build_maze_payload(args.prototype_url)
        out_path = args.output
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"Dry-run complete. Study JSON written to: {out_path}")
        print(f"  Blocks: {len(payload['blocks'])}")
        print(f"  Likert items: {sum(len(s) for _, s in LIKERT_CATEGORIES)}")
        print(f"  Open-ended items: {len(OPEN_ENDED_QUESTIONS)}")
        return

    if not args.api_key:
        print("Error: --api-key is required unless --dry-run is used.", file=sys.stderr)
        sys.exit(1)

    upload_to_maze(args.api_key, args.prototype_url)


if __name__ == "__main__":
    main()
