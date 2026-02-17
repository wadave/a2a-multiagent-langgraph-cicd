#!/usr/bin/env python3
# Copyright 2025 Google LLC
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Run agent evaluation tests."""

import argparse
import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


def load_evalset(evalset_path: Path) -> Dict:
    """Load an evaluation set."""
    with open(evalset_path) as f:
        return json.load(f)


def load_eval_config(config_path: Path) -> Dict:
    """Load evaluation configuration."""
    with open(config_path) as f:
        return json.load(f)


def calculate_rubric_score(example: Dict, response: str) -> Dict[str, float]:
    """Calculate rubric-based scores for a response.

    Args:
        example: The evaluation example
        response: The agent's response

    Returns:
        Dictionary of rubric scores
    """
    scores = {}

    # Simple heuristic-based scoring
    # In production, this would use LLM-based evaluation

    # Relevance: Check if response contains expected content
    if "expected_response_contains" in example:
        expected_terms = example["expected_response_contains"]
        found_count = sum(1 for term in expected_terms if term.lower() in response.lower())
        scores["relevance"] = found_count / len(expected_terms) if expected_terms else 1.0
    else:
        scores["relevance"] = 0.9  # Default high score if no specific expectations

    # Helpfulness: Check response length and structure
    if len(response) > 50 and any(marker in response for marker in [":", "-", "*", "#"]):
        scores["helpfulness"] = 1.0
    elif len(response) > 20:
        scores["helpfulness"] = 0.7
    else:
        scores["helpfulness"] = 0.5

    # Format: Check for Markdown formatting
    has_markdown = any(marker in response for marker in ["**", "##", "- ", "* "])
    scores["format"] = 1.0 if has_markdown else 0.5

    # Tool routing: Would need actual agent execution logs
    # For now, assume correct routing
    scores["tool_routing"] = 0.9

    return scores


def evaluate_example(example: Dict, config: Dict) -> Dict:
    """Evaluate a single example.

    Args:
        example: The evaluation example
        config: Evaluation configuration

    Returns:
        Evaluation results
    """
    result = {
        "example_id": example.get("id", "unknown"),
        "category": example.get("category", "unknown"),
        "input": example.get("input", ""),
        "passed": False,
        "scores": {},
        "notes": [],
    }

    # In a real evaluation, you would:
    # 1. Send the query to the agent
    # 2. Collect the response and tool execution logs
    # 3. Calculate scores based on rubrics

    # For this template, we'll use mock scores
    mock_response = "Mock agent response with **formatted** content:\n- Item 1\n- Item 2"

    scores = calculate_rubric_score(example, mock_response)
    result["scores"] = scores

    # Check against thresholds
    criteria = config["criteria"]
    rubric_config = criteria.get("rubric_based_final_response_quality_v1", {})
    threshold = rubric_config.get("threshold", 0.8)

    avg_score = sum(scores.values()) / len(scores) if scores else 0
    result["avg_score"] = avg_score
    result["passed"] = avg_score >= threshold

    if not result["passed"]:
        result["notes"].append(
            f"Average score {avg_score:.2f} below threshold {threshold}"
        )

    return result


def main():
    """Run evaluation tests."""
    parser = argparse.ArgumentParser(description="Run agent evaluation tests")
    parser.add_argument(
        "--evalset",
        type=str,
        default="comprehensive",
        help="Name of evaluation set to run",
    )
    parser.add_argument(
        "--config",
        type=str,
        default="eval_config.json",
        help="Path to evaluation config file",
    )
    parser.add_argument(
        "--output",
        type=str,
        help="Path to save evaluation results (JSON)",
    )
    args = parser.parse_args()

    # Load configuration and evaluation set
    eval_dir = Path(__file__).parent
    config_path = eval_dir / args.config
    evalset_path = eval_dir / "evalsets" / f"{args.evalset}.evalset.json"

    if not config_path.exists():
        logger.error(f"Config file not found: {config_path}")
        sys.exit(1)

    if not evalset_path.exists():
        logger.error(f"Evalset file not found: {evalset_path}")
        sys.exit(1)

    config = load_eval_config(config_path)
    evalset = load_evalset(evalset_path)

    logger.info(f"Running evaluation: {evalset.get('name', args.evalset)}")
    logger.info(f"Total examples: {len(evalset.get('examples', []))}")

    # Run evaluation
    results = []
    examples = evalset.get("examples", [])

    for i, example in enumerate(examples, 1):
        logger.info(f"Evaluating example {i}/{len(examples)}: {example.get('id')}")
        result = evaluate_example(example, config)
        results.append(result)

        if result["passed"]:
            logger.info(f"  ✓ PASSED (score: {result['avg_score']:.2f})")
        else:
            logger.warning(f"  ✗ FAILED (score: {result['avg_score']:.2f})")

    # Calculate summary statistics
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    pass_rate = (passed / total * 100) if total > 0 else 0

    summary = {
        "evalset": args.evalset,
        "total_examples": total,
        "passed": passed,
        "failed": failed,
        "pass_rate": pass_rate,
        "results": results,
    }

    # Print summary
    print("\n" + "=" * 80)
    print("EVALUATION SUMMARY")
    print("=" * 80)
    print(f"Evaluation Set: {evalset.get('name', args.evalset)}")
    print(f"Total Examples: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Pass Rate: {pass_rate:.1f}%")
    print("=" * 80)

    # Save results if output path specified
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, "w") as f:
            json.dump(summary, f, indent=2)
        logger.info(f"Results saved to: {output_path}")

    # Exit with appropriate code
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()
