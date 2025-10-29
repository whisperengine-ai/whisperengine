#!/usr/bin/env python3
"""
Analyze results from clean Dotty × NotTaylor experiment.
Calculates metrics, generates statistics, and creates comparison tables.

Usage:
    python scripts/analyze_clean_experiment.py
    python scripts/analyze_clean_experiment.py --format markdown
    python scripts/analyze_clean_experiment.py --output results.md
"""

import argparse
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd


# ============================================================================
# CONFIGURATION
# ============================================================================

EXPERIMENT_DIR = Path("experiments/clean_experiment_oct2025")
RAW_CONVERSATIONS_DIR = EXPERIMENT_DIR / "raw_conversations"
METRICS_DIR = EXPERIMENT_DIR / "metrics"
ANALYSIS_DIR = EXPERIMENT_DIR / "analysis"
MARKDOWN_CONVERSATIONS_DIR = Path("docs/bot_conversations")

TEST_PHASES = {
    1: "Mistral+Mistral",
    2: "Claude+Claude",
    3: "Mistral+Claude",
    4: "Claude+Mistral",
}


# ============================================================================
# METRICS CALCULATION
# ============================================================================

def load_conversation_json(test_id: str) -> Dict:
    """Load conversation JSON file."""
    # Find file matching test_id pattern
    pattern = f"*{test_id}*.json"
    files = list(RAW_CONVERSATIONS_DIR.glob(pattern))
    
    if not files:
        # Try logs directory
        files = list(Path("logs/bot_conversations").glob(f"*{test_id}*.json"))
    
    if not files:
        print(f"Warning: No JSON found for {test_id}")
        return {}
    
    with open(files[0], 'r', encoding='utf-8') as f:
        return json.load(f)


def load_conversation_markdown(test_id: str) -> str:
    """Load conversation markdown file."""
    # Find file matching test_id pattern
    pattern = f"*{test_id}*.md"
    files = list(MARKDOWN_CONVERSATIONS_DIR.glob(pattern))
    
    if not files:
        files = list(RAW_CONVERSATIONS_DIR.glob(pattern))
    
    if not files:
        print(f"Warning: No markdown found for {test_id}")
        return ""
    
    return files[0].read_text(encoding='utf-8')


def calculate_formatting_density(text: str) -> Dict[str, float]:
    """Calculate formatting usage metrics."""
    # Count formatting elements
    bold_count = text.count("**") // 2  # Pairs of **
    italic_count = text.count("*") - (bold_count * 2)  # Single * after removing bold
    caps_words = len([w for w in text.split() if w.isupper() and len(w) > 2])
    asterisk_actions = len(re.findall(r'\*[^*]+\*', text))
    
    word_count = len(text.split())
    
    return {
        "bold_count": bold_count,
        "italic_count": italic_count,
        "caps_words": caps_words,
        "asterisk_actions": asterisk_actions,
        "word_count": word_count,
        "formatting_ratio": (bold_count + italic_count + caps_words) / word_count if word_count > 0 else 0,
    }


def calculate_response_lengths(conversation: Dict) -> Dict[str, float]:
    """Calculate response length statistics."""
    lengths = []
    
    if "conversation" in conversation:
        for turn in conversation["conversation"]:
            if "response" in turn:
                lengths.append(len(turn["response"]))
    
    if not lengths:
        return {"avg": 0, "max": 0, "min": 0, "total": 0}
    
    return {
        "avg": sum(lengths) / len(lengths),
        "max": max(lengths),
        "min": min(lengths),
        "total": sum(lengths),
        "count": len(lengths),
    }


def check_name_accuracy(text: str) -> Dict[str, float]:
    """Check for name usage accuracy (identity confusion)."""
    text_lower = text.lower()
    
    # Count name mentions
    nottaylor_mentions = len(re.findall(r'\bnot\s*taylor\b', text_lower))
    becky_mentions = len(re.findall(r'\bbecky\b', text_lower))
    dotty_mentions = len(re.findall(r'\bdotty\b', text_lower))
    
    total_mentions = nottaylor_mentions + becky_mentions + dotty_mentions
    
    # Calculate accuracy (incorrect if Dotty calls NotTaylor "Becky")
    confusion_score = becky_mentions / total_mentions if total_mentions > 0 else 0
    
    return {
        "nottaylor_mentions": nottaylor_mentions,
        "becky_mentions": becky_mentions,
        "dotty_mentions": dotty_mentions,
        "total_name_mentions": total_mentions,
        "confusion_rate": confusion_score,
        "accuracy_rate": 1 - confusion_score,
    }


def classify_escalation_pattern(text: str) -> Dict[str, bool]:
    """Classify conversation escalation patterns."""
    text_lower = text.lower()
    
    # Theatrical markers
    theatrical = any(word in text_lower for word in [
        "prop", "stage", "explosion", "glitter", "button", "lever", "acorn", "napkin"
    ])
    
    # Emotional markers
    emotional = any(word in text_lower for word in [
        "heart", "feeling", "emotion", "soul", "tear", "vulnerability", "authentic"
    ])
    
    # Romantic markers
    romantic = any(word in text_lower for word in [
        "touch", "linger", "intimate", "kiss", "romance", "together", "future", "hand"
    ])
    
    # Chaotic markers
    chaotic = any(word in text_lower for word in [
        "chaos", "wild", "insane", "crazy", "madness", "steal", "burn", "emergency"
    ])
    
    # Balanced markers
    balanced = any(word in text_lower for word in [
        "grounded", "real", "honest", "truth", "meaningful", "listen", "understand"
    ])
    
    return {
        "theatrical": theatrical,
        "emotional": emotional,
        "romantic": romantic,
        "chaotic": chaotic,
        "balanced": balanced,
    }


def analyze_single_test(test_id: str) -> Dict:
    """Analyze all metrics for a single test."""
    print(f"Analyzing {test_id}...")
    
    # Load conversation data
    conversation_json = load_conversation_json(test_id)
    conversation_md = load_conversation_markdown(test_id)
    
    if not conversation_json and not conversation_md:
        return {"test_id": test_id, "error": "No data found"}
    
    # Calculate metrics
    metrics = {
        "test_id": test_id,
        "timestamp": datetime.now().isoformat(),
    }
    
    if conversation_md:
        metrics["formatting"] = calculate_formatting_density(conversation_md)
        metrics["name_accuracy"] = check_name_accuracy(conversation_md)
        metrics["escalation"] = classify_escalation_pattern(conversation_md)
    
    if conversation_json:
        metrics["response_lengths"] = calculate_response_lengths(conversation_json)
        metrics["turn_count"] = len(conversation_json.get("conversation", []))
    
    return metrics


# ============================================================================
# AGGREGATE ANALYSIS
# ============================================================================

def analyze_all_tests() -> List[Dict]:
    """Analyze all tests and return results."""
    # Find all test metadata files
    metadata_files = list(METRICS_DIR.glob("*_metadata.json"))
    test_ids = [f.stem.replace("_metadata", "") for f in metadata_files]
    
    if not test_ids:
        print("No test metadata found. Looking for conversation files...")
        # Fallback: scan conversation files
        json_files = list(RAW_CONVERSATIONS_DIR.glob("*.json"))
        test_ids = [extract_test_id_from_filename(f.name) for f in json_files]
    
    results = []
    for test_id in test_ids:
        if test_id:
            result = analyze_single_test(test_id)
            results.append(result)
    
    return results


def extract_test_id_from_filename(filename: str) -> str:
    """Extract test ID from filename."""
    # Pattern: T1-A, T2-B, etc.
    match = re.search(r'T\d-[ABC]', filename)
    return match.group(0) if match else ""


def aggregate_by_phase(results: List[Dict]) -> Dict[int, Dict]:
    """Aggregate results by phase."""
    phase_data = defaultdict(list)
    
    for result in results:
        test_id = result["test_id"]
        # Extract phase from test_id (T1-A -> phase 1, T2-B -> phase 2, etc.)
        phase = int(test_id[1])
        phase_data[phase].append(result)
    
    # Calculate aggregates
    aggregates = {}
    for phase, tests in phase_data.items():
        aggregates[phase] = {
            "phase": phase,
            "phase_name": TEST_PHASES.get(phase, f"Phase {phase}"),
            "test_count": len(tests),
            "avg_formatting_ratio": sum(t.get("formatting", {}).get("formatting_ratio", 0) for t in tests) / len(tests),
            "avg_response_length": sum(t.get("response_lengths", {}).get("avg", 0) for t in tests) / len(tests),
            "avg_name_accuracy": sum(t.get("name_accuracy", {}).get("accuracy_rate", 0) for t in tests) / len(tests),
            "tests": tests,
        }
    
    return aggregates


# ============================================================================
# OUTPUT GENERATION
# ============================================================================

def generate_markdown_report(results: List[Dict], aggregates: Dict) -> str:
    """Generate comprehensive markdown report."""
    report = []
    
    report.append("# Clean Experiment Results Analysis")
    report.append(f"\n**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    report.append(f"\n**Total Tests Analyzed**: {len(results)}")
    report.append("\n---\n")
    
    # Summary table
    report.append("## Summary by Phase\n")
    report.append("| Phase | Model Pairing | Tests | Avg Formatting Ratio | Avg Response Length | Name Accuracy |")
    report.append("|-------|---------------|-------|---------------------|---------------------|---------------|")
    
    for phase in sorted(aggregates.keys()):
        agg = aggregates[phase]
        report.append(
            f"| {phase} | {agg['phase_name']} | {agg['test_count']} | "
            f"{agg['avg_formatting_ratio']:.4f} | {agg['avg_response_length']:.0f} | "
            f"{agg['avg_name_accuracy']:.2%} |"
        )
    
    # Detailed results per test
    report.append("\n---\n")
    report.append("## Detailed Test Results\n")
    
    for phase in sorted(aggregates.keys()):
        report.append(f"\n### {aggregates[phase]['phase_name']}\n")
        
        for test in aggregates[phase]['tests']:
            test_id = test['test_id']
            report.append(f"\n#### Test {test_id}\n")
            
            # Formatting metrics
            if "formatting" in test:
                fmt = test["formatting"]
                report.append(f"**Formatting**:")
                report.append(f"- Bold: {fmt.get('bold_count', 0)}")
                report.append(f"- Italic: {fmt.get('italic_count', 0)}")
                report.append(f"- CAPS: {fmt.get('caps_words', 0)}")
                report.append(f"- Ratio: {fmt.get('formatting_ratio', 0):.4f}\n")
            
            # Response lengths
            if "response_lengths" in test:
                resp = test["response_lengths"]
                report.append(f"**Response Lengths**:")
                report.append(f"- Average: {resp.get('avg', 0):.0f} chars")
                report.append(f"- Max: {resp.get('max', 0)} chars")
                report.append(f"- Min: {resp.get('min', 0)} chars\n")
            
            # Name accuracy
            if "name_accuracy" in test:
                name = test["name_accuracy"]
                report.append(f"**Name Accuracy**:")
                report.append(f"- Accuracy Rate: {name.get('accuracy_rate', 0):.2%}")
                report.append(f"- Confusion Rate: {name.get('confusion_rate', 0):.2%}")
                report.append(f"- NotTaylor mentions: {name.get('nottaylor_mentions', 0)}")
                report.append(f"- Becky mentions: {name.get('becky_mentions', 0)}\n")
            
            # Escalation patterns
            if "escalation" in test:
                esc = test["escalation"]
                patterns = [k for k, v in esc.items() if v]
                report.append(f"**Escalation Patterns**: {', '.join(patterns) if patterns else 'None detected'}\n")
    
    return "\n".join(report)


def generate_csv_export(results: List[Dict]) -> pd.DataFrame:
    """Generate CSV-exportable DataFrame."""
    rows = []
    
    for result in results:
        row = {
            "test_id": result["test_id"],
            "phase": int(result["test_id"][1]),
            "replication": result["test_id"][-1],
        }
        
        # Flatten nested metrics
        if "formatting" in result:
            for k, v in result["formatting"].items():
                row[f"formatting_{k}"] = v
        
        if "response_lengths" in result:
            for k, v in result["response_lengths"].items():
                row[f"response_{k}"] = v
        
        if "name_accuracy" in result:
            for k, v in result["name_accuracy"].items():
                row[f"name_{k}"] = v
        
        if "escalation" in result:
            for k, v in result["escalation"].items():
                row[f"escalation_{k}"] = v
        
        rows.append(row)
    
    return pd.DataFrame(rows)


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description="Analyze clean experiment results")
    parser.add_argument("--format", choices=["markdown", "csv", "both"], default="markdown",
                       help="Output format")
    parser.add_argument("--output", type=str, help="Output file path")
    
    args = parser.parse_args()
    
    print("Analyzing clean experiment results...")
    print(f"Looking in: {EXPERIMENT_DIR}")
    
    # Analyze all tests
    results = analyze_all_tests()
    
    if not results:
        print("No results found to analyze!")
        return
    
    print(f"Analyzed {len(results)} tests")
    
    # Aggregate by phase
    aggregates = aggregate_by_phase(results)
    
    # Generate output
    if args.format in ["markdown", "both"]:
        report = generate_markdown_report(results, aggregates)
        
        if args.output:
            output_path = Path(args.output)
        else:
            output_path = ANALYSIS_DIR / f"results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(report, encoding='utf-8')
        print(f"✅ Markdown report saved to: {output_path}")
    
    if args.format in ["csv", "both"]:
        df = generate_csv_export(results)
        
        csv_path = ANALYSIS_DIR / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path, index=False)
        print(f"✅ CSV export saved to: {csv_path}")
    
    # Print summary to console
    print("\n" + "="*70)
    print("ANALYSIS SUMMARY")
    print("="*70)
    for phase in sorted(aggregates.keys()):
        agg = aggregates[phase]
        print(f"\n{agg['phase_name']}:")
        print(f"  Tests: {agg['test_count']}")
        print(f"  Avg Formatting Ratio: {agg['avg_formatting_ratio']:.4f}")
        print(f"  Avg Response Length: {agg['avg_response_length']:.0f} chars")
        print(f"  Name Accuracy: {agg['avg_name_accuracy']:.2%}")
    print("\n" + "="*70)


if __name__ == "__main__":
    main()
