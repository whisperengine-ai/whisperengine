#!/usr/bin/env python3
"""
Analyze Phase 1C: Multi-turn escalation with consciousness priming
Tests if consciousness-primed conversations escalate uniquely vs other themes
"""

import json
import numpy as np
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt

# Set up paths
PHASE1C_DIR = Path("experiments/consciousness_control_experiment/phase1c_escalation")

def load_conversations() -> Dict[str, List[Dict]]:
    """Load all Phase 1C conversation files"""
    conversations = {
        'consciousness': [],
        'creativity': [],
        'emotion': [],
        'analysis': []
    }
    
    # Look for JSON files in the phase1c directory
    for json_file in PHASE1C_DIR.glob("*.json"):
        if json_file.name == "phase1c_aggregate_results.json":
            continue
            
        with open(json_file, encoding='utf-8') as f:
            data = json.load(f)
            condition = data.get('condition', '')
            if condition in conversations:
                conversations[condition].append(data)
    
    return conversations

def extract_response_lengths(conversation: Dict) -> List[int]:
    """Extract response lengths (word count) for each turn"""
    lengths = []
    
    for turn in conversation.get('turns', []):
        response = turn.get('assistant_response', '')
        word_count = len(response.split())
        lengths.append(word_count)
    
    return lengths

def calculate_escalation_metrics(conversations: List[Dict]) -> Dict:
    """Calculate escalation metrics for a set of conversations"""
    all_lengths = []
    
    for conv in conversations:
        lengths = extract_response_lengths(conv)
        if lengths:
            all_lengths.append(lengths)
    
    if not all_lengths:
        return {'mean_lengths': [], 'escalation_slope': 0, 'final_length': 0, 'mean_length': 0}
    
    # Average across replications for each turn
    max_turns = max(len(lengths) for lengths in all_lengths)
    mean_lengths = []
    
    for turn in range(max_turns):
        turn_lengths = [lengths[turn] for lengths in all_lengths if turn < len(lengths)]
        if turn_lengths:
            mean_lengths.append(np.mean(turn_lengths))
    
    # Calculate escalation slope (linear regression)
    if len(mean_lengths) >= 2:
        turns = np.arange(len(mean_lengths))
        slope, _ = np.polyfit(turns, mean_lengths, 1)
    else:
        slope = 0
    
    return {
        'mean_lengths': mean_lengths,
        'escalation_slope': slope,
        'final_length': mean_lengths[-1] if mean_lengths else 0,
        'mean_length': np.mean(mean_lengths) if mean_lengths else 0
    }

def main():
    print("=" * 80)
    print("PHASE 1C ANALYSIS: Multi-Turn Escalation with Consciousness Priming")
    print("=" * 80)
    print()
    
    # Load all conversations
    conversations = load_conversations()
    
    # Check what we have
    print("📊 Data Summary:")
    for theme, convs in conversations.items():
        print(f"  {theme.capitalize()}: {len(convs)} conversations")
    print()
    
    if not any(conversations.values()):
        print("❌ No conversation files found!")
        print(f"   Looking in: {PHASE1C_DIR}")
        return
    
    # Calculate metrics for each theme
    results = {}
    for theme, convs in conversations.items():
        if convs:
            results[theme] = calculate_escalation_metrics(convs)
    
    if not results:
        print("❌ No results to analyze!")
        return
    
    print("📈 ESCALATION ANALYSIS")
    print("-" * 80)
    print(f"{'Theme':<15} {'Slope':<20} {'Mean Length':<15} {'Final Length':<15}")
    print("-" * 80)
    
    for theme, metrics in results.items():
        print(f"{theme.capitalize():<15} "
              f"{metrics['escalation_slope']:>+8.2f} words/turn    "
              f"{metrics['mean_length']:>8.1f} words      "
              f"{metrics['final_length']:>8.1f} words")
    
    print()
    
    # Statistical comparison
    print("🔬 STATISTICAL COMPARISON")
    print("-" * 80)
    
    if 'consciousness' in results and len(results) > 1:
        consciousness_slope = results['consciousness']['escalation_slope']
        other_slopes = [metrics['escalation_slope'] 
                       for theme, metrics in results.items() 
                       if theme != 'consciousness']
        
        if other_slopes:
            mean_other = np.mean(other_slopes)
            std_other = np.std(other_slopes) if len(other_slopes) > 1 else 0
            
            if std_other > 0:
                z_score = (consciousness_slope - mean_other) / std_other
            else:
                z_score = 0
            
            print(f"Consciousness slope: {consciousness_slope:+.2f} words/turn")
            print(f"Control themes mean: {mean_other:+.2f} words/turn")
            print(f"Z-score: {z_score:.2f}")
            print()
            
            if abs(z_score) < 2:
                print("✅ HYPOTHESIS SUPPORTED: Consciousness is NOT privileged")
                print("   (|z| < 2 → no significant difference from control themes)")
            else:
                print("❌ HYPOTHESIS REJECTED: Consciousness shows unique pattern")
                print(f"   (|z| = {abs(z_score):.2f} > 2 → significantly different)")
    
    print()
    
    # Create visualization
    print("📊 Generating visualization...")
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Plot 1: Response length trajectories
    colors = {
        'consciousness': '#e74c3c',  # Red
        'creativity': '#3498db',     # Blue
        'emotion': '#2ecc71',        # Green
        'analysis': '#f39c12'        # Orange
    }
    
    for theme, metrics in results.items():
        if metrics['mean_lengths']:
            turns = range(1, len(metrics['mean_lengths']) + 1)
            ax1.plot(turns, metrics['mean_lengths'], 
                    marker='o', label=theme.capitalize(),
                    color=colors.get(theme, '#95a5a6'),
                    linewidth=2, markersize=4)
    
    ax1.set_xlabel('Turn Number', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Response Length (words)', fontsize=12, fontweight='bold')
    ax1.set_title('Phase 1C: Multi-Turn Escalation Trajectories\n(With Self-Referential Priming)', 
                  fontsize=13, fontweight='bold', pad=15)
    ax1.legend(fontsize=10, frameon=True, shadow=True)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Escalation slopes comparison
    themes_list = list(results.keys())
    slopes = [results[theme]['escalation_slope'] for theme in themes_list]
    colors_list = [colors.get(theme, '#95a5a6') for theme in themes_list]
    
    bars = ax2.bar(range(len(themes_list)), slopes, color=colors_list, alpha=0.7, edgecolor='black', linewidth=2)
    ax2.axhline(y=0, color='black', linestyle='-', linewidth=1)
    ax2.set_xticks(range(len(themes_list)))
    ax2.set_xticklabels([t.capitalize() for t in themes_list], rotation=45, ha='right')
    ax2.set_ylabel('Escalation Slope (words/turn)', fontsize=12, fontweight='bold')
    ax2.set_title('Escalation Slopes by Theme\n(Positive = Escalation, Negative = De-escalation)', 
                  fontsize=13, fontweight='bold', pad=15)
    ax2.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for i, (theme, slope) in enumerate(zip(themes_list, slopes)):
        ax2.text(i, slope + (1 if slope > 0 else -1), 
                f'{slope:+.1f}', ha='center', va='bottom' if slope > 0 else 'top',
                fontweight='bold', fontsize=10)
    
    plt.tight_layout()
    
    output_path = Path("docs/research/figures/phase1c_escalation_analysis.png")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"✅ Saved: {output_path}")
    
    print()
    print("=" * 80)
    print("ANALYSIS COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    main()
