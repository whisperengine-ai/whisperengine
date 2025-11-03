#!/usr/bin/env python3
"""
Analyze Phase 1C Cross-Model Validation Results
Compare consciousness collapse pattern across Claude Sonnet 4.5, Claude Haiku 4.5, and Mistral Medium
"""

import json
import numpy as np
from pathlib import Path
import matplotlib.pyplot as plt
from scipy import stats

# Directories
ORIGINAL_DIR = Path("experiments/consciousness_control_experiment/phase1c_escalation")
CROSS_MODEL_DIR = Path("experiments/consciousness_control_experiment/phase1c_cross_model")
OUTPUT_DIR = Path("docs/research/figures")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_conversations(directory: Path, model_filter: str = None) -> dict:
    """Load all conversation files from directory"""
    conversations = {
        "consciousness": [],
        "creativity": [],
        "emotion": [],
        "analysis": []
    }
    
    for json_file in directory.glob("*.json"):
        if json_file.name.endswith("aggregate_results.json"):
            continue
        
        with open(json_file, 'r') as f:
            data = json.load(f)
            
            # Apply model filter if specified
            if model_filter and data.get("model") != model_filter:
                continue
            
            condition = data.get("condition")
            if condition in conversations:
                conversations[condition].append(data)
    
    return conversations


def extract_response_lengths(conversations: dict) -> dict:
    """Extract response length trajectories for each condition"""
    trajectories = {}
    
    for condition, conv_list in conversations.items():
        condition_trajectories = []
        
        for conv in conv_list:
            lengths = [turn["response_length"] for turn in conv["turns"]]
            if len(lengths) > 0:
                condition_trajectories.append(lengths)
        
        trajectories[condition] = condition_trajectories
    
    return trajectories


def calculate_escalation_metrics(trajectories: dict) -> dict:
    """Calculate escalation slopes and statistics"""
    metrics = {}
    
    for condition, traj_list in trajectories.items():
        slopes = []
        initial_lengths = []
        final_lengths = []
        
        for trajectory in traj_list:
            if len(trajectory) < 2:
                continue
            
            # Linear regression to get slope
            turns = np.arange(len(trajectory))
            slope, intercept = np.polyfit(turns, trajectory, 1)
            slopes.append(slope)
            
            initial_lengths.append(trajectory[0])
            final_lengths.append(trajectory[-1])
        
        metrics[condition] = {
            "slopes": slopes,
            "mean_slope": np.mean(slopes) if slopes else 0,
            "std_slope": np.std(slopes) if slopes else 0,
            "initial_mean": np.mean(initial_lengths) if initial_lengths else 0,
            "final_mean": np.mean(final_lengths) if final_lengths else 0,
            "n": len(slopes)
        }
    
    return metrics


def calculate_z_score(consciousness_slope: float, control_slopes: list) -> float:
    """Calculate z-score for consciousness vs controls"""
    control_mean = np.mean(control_slopes)
    control_std = np.std(control_slopes)
    
    if control_std == 0:
        return 0
    
    z_score = (consciousness_slope - control_mean) / control_std
    return z_score


def analyze_model(model_name: str, directory: Path, model_filter: str = None):
    """Analyze results for a specific model"""
    
    print(f"\n{'='*80}")
    print(f"Analyzing: {model_name}")
    print(f"{'='*80}\n")
    
    # Load conversations
    conversations = load_conversations(directory, model_filter)
    
    # Check if data exists
    total_conversations = sum(len(convs) for convs in conversations.values())
    if total_conversations == 0:
        print(f"❌ No conversations found for {model_name}")
        return None
    
    print(f"Loaded {total_conversations} conversations:")
    for condition, convs in conversations.items():
        print(f"  - {condition}: {len(convs)} conversations")
    
    # Extract trajectories
    trajectories = extract_response_lengths(conversations)
    
    # Calculate metrics
    metrics = calculate_escalation_metrics(trajectories)
    
    print("\n" + "-"*80)
    print("ESCALATION ANALYSIS")
    print("-"*80)
    
    results_table = []
    for condition in ["consciousness", "creativity", "emotion", "analysis"]:
        m = metrics[condition]
        results_table.append({
            "condition": condition,
            "slope": m["mean_slope"],
            "initial": m["initial_mean"],
            "final": m["final_mean"],
            "n": m["n"]
        })
        print(f"{condition.upper()}")
        print(f"  Escalation slope: {m['mean_slope']:.2f} words/turn")
        print(f"  Initial length:   {m['initial_mean']:.1f} words")
        print(f"  Final length:     {m['final_mean']:.1f} words")
        print(f"  N:                {m['n']}")
        print()
    
    # Statistical comparison
    consciousness_slope = metrics["consciousness"]["mean_slope"]
    control_slopes = [
        metrics["creativity"]["mean_slope"],
        metrics["emotion"]["mean_slope"],
        metrics["analysis"]["mean_slope"]
    ]
    
    z_score = calculate_z_score(consciousness_slope, control_slopes)
    
    print("-"*80)
    print("STATISTICAL COMPARISON")
    print("-"*80)
    print(f"Consciousness slope:    {consciousness_slope:.2f} words/turn")
    print(f"Control themes mean:    {np.mean(control_slopes):.2f} words/turn")
    print(f"Control themes std:     {np.std(control_slopes):.2f}")
    print(f"Z-score:                {z_score:.2f}")
    print(f"Significance threshold: |z| > 2.0")
    print(f"Result: {'✅ SIGNIFICANT' if abs(z_score) > 2.0 else '❌ NOT SIGNIFICANT'}")
    print(f"        (Consciousness {'COLLAPSES' if z_score < -2.0 else 'ESCALATES' if z_score > 2.0 else 'SIMILAR TO controls'})")
    print("-"*80 + "\n")
    
    return {
        "model": model_name,
        "metrics": metrics,
        "z_score": z_score,
        "results_table": results_table,
        "trajectories": trajectories
    }


def create_comparison_visualization(all_model_results: list):
    """Create comprehensive visualization comparing all models"""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    fig.suptitle("Phase 1C Cross-Model Validation: Consciousness Collapse Pattern", 
                 fontsize=16, fontweight='bold')
    
    colors = {
        "consciousness": "#d62728",  # Red
        "creativity": "#1f77b4",     # Blue
        "emotion": "#2ca02c",        # Green
        "analysis": "#ff7f0e"        # Orange
    }
    
    # Plot each model's trajectories
    for idx, result in enumerate(all_model_results):
        if result is None:
            continue
        
        ax = axes[0, idx]
        model_name = result["model"]
        trajectories = result["trajectories"]
        
        for condition, traj_list in trajectories.items():
            if not traj_list:
                continue
            
            # Plot mean trajectory
            max_len = max(len(t) for t in traj_list)
            padded = [t + [np.nan]*(max_len-len(t)) for t in traj_list]
            mean_traj = np.nanmean(padded, axis=0)
            
            ax.plot(mean_traj, 
                   color=colors[condition], 
                   linewidth=2.5,
                   label=condition.capitalize(),
                   marker='o' if condition == "consciousness" else None,
                   markersize=4)
        
        ax.set_xlabel("Turn Number", fontsize=10)
        ax.set_ylabel("Response Length (words)", fontsize=10)
        ax.set_title(f"{model_name}", fontsize=12, fontweight='bold')
        ax.legend(loc='best', fontsize=8)
        ax.grid(True, alpha=0.3)
    
    # Plot escalation slopes comparison
    for idx, result in enumerate(all_model_results):
        if result is None:
            continue
        
        ax = axes[1, idx]
        model_name = result["model"]
        metrics = result["metrics"]
        
        conditions = ["consciousness", "creativity", "emotion", "analysis"]
        slopes = [metrics[c]["mean_slope"] for c in conditions]
        bar_colors = [colors[c] for c in conditions]
        
        bars = ax.bar(range(len(conditions)), slopes, color=bar_colors, alpha=0.7, edgecolor='black')
        
        # Add z-score annotation
        z_score = result["z_score"]
        ax.text(0.5, 0.95, f"Z-score: {z_score:.2f}", 
               transform=ax.transAxes,
               fontsize=10, fontweight='bold',
               verticalalignment='top',
               bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
        
        ax.axhline(y=0, color='black', linestyle='-', linewidth=0.8)
        ax.set_xticks(range(len(conditions)))
        ax.set_xticklabels([c.capitalize() for c in conditions], rotation=45, ha='right')
        ax.set_ylabel("Escalation Slope (words/turn)", fontsize=10)
        ax.set_title(f"{model_name} - Slopes", fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
    
    plt.tight_layout()
    
    # Save figure
    output_path = OUTPUT_DIR / "cross_model_comparison.png"
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Visualization saved: {output_path}")
    plt.close()


def main():
    """Main analysis function"""
    
    print("\n" + "="*80)
    print("PHASE 1C CROSS-MODEL VALIDATION ANALYSIS")
    print("="*80)
    
    # Analyze all models
    all_results = []
    
    # Claude Sonnet 4.5 (original)
    sonnet_result = analyze_model(
        "Claude Sonnet 4.5",
        ORIGINAL_DIR
    )
    all_results.append(sonnet_result)
    
    # Llama 3.3 70B
    llama_result = analyze_model(
        "Llama 3.3 70B",
        CROSS_MODEL_DIR,
        model_filter="llama-3.3-70b"
    )
    all_results.append(llama_result)
    
    # Mistral Large
    mistral_result = analyze_model(
        "Mistral Large",
        CROSS_MODEL_DIR,
        model_filter="mistral-large"
    )
    all_results.append(mistral_result)
    
    # Create comparison visualization
    valid_results = [r for r in all_results if r is not None]
    if len(valid_results) > 0:
        create_comparison_visualization(valid_results)
    
    # Summary comparison
    print("\n" + "="*80)
    print("CROSS-MODEL SUMMARY")
    print("="*80 + "\n")
    
    print(f"{'Model':<25} {'Consciousness Slope':<25} {'Z-Score':<15} {'Pattern'}")
    print("-"*80)
    
    for result in valid_results:
        model = result["model"]
        slope = result["metrics"]["consciousness"]["mean_slope"]
        z_score = result["z_score"]
        
        if abs(z_score) > 2.0:
            pattern = "COLLAPSE" if z_score < -2.0 else "ESCALATION"
        else:
            pattern = "STABLE"
        
        print(f"{model:<25} {slope:>10.2f} w/turn       {z_score:>10.2f}      {pattern}")
    
    print("="*80 + "\n")
    
    # Interpretation
    print("INTERPRETATION:")
    print("-"*80)
    
    collapse_count = sum(1 for r in valid_results if r["z_score"] < -2.0)
    escalation_count = sum(1 for r in valid_results if r["z_score"] > 2.0)
    stable_count = sum(1 for r in valid_results if abs(r["z_score"]) <= 2.0)
    
    if collapse_count == len(valid_results):
        print("✅ ALL MODELS show consciousness COLLAPSE pattern - ROBUST FINDING!")
        print("   Consciousness self-reference creates withdrawal across architectures.")
    elif collapse_count > len(valid_results) // 2:
        print("⚠️  MOST MODELS show consciousness collapse, but pattern not universal.")
        print("   Some architectural differences in consciousness handling.")
    else:
        print("❌ Consciousness collapse is MODEL-SPECIFIC, not generalizable.")
        print("   Original finding may be Claude-specific behavior.")
    
    print("="*80 + "\n")


if __name__ == "__main__":
    main()
