#!/usr/bin/env python3
"""
Convert bot-to-bot conversation JSON logs into human-readable markdown format.
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Dict, List
from collections import defaultdict


def format_timestamp(iso_timestamp: str) -> str:
    """Convert ISO timestamp to readable format."""
    try:
        dt = datetime.fromisoformat(iso_timestamp)
        return dt.strftime("%I:%M:%S %p")
    except:
        return iso_timestamp


def format_speaker_name(speaker: str, participants: Dict) -> str:
    """Get formatted speaker name."""
    if speaker == "system":
        return "**System**"
    
    # Map speaker to participant info
    for bot_key, info in participants.items():
        if info["name"] == speaker:
            return f"**{info['full_name']}**"
    
    return f"**{speaker.title()}**"


def format_dialogue_text(text: str) -> str:
    """Format dialogue text with stage directions in subdued style and dialogue in quotes."""
    import re
    
    # Split into lines to process each separately
    lines = text.split('\n')
    formatted_lines = []
    
    for line in lines:
        stripped = line.strip()
        # Check if the entire line (or most of it) is a stage direction
        # Stage directions are lines that start with * and end with *
        if stripped.startswith('*') and stripped.endswith('*') and len(stripped) > 2:
            # This is a stage direction line - make it smaller and subdued
            formatted_lines.append(f'<sub>{line}</sub>')
        elif stripped and not stripped.startswith('*'):
            # This is dialogue - wrap in quotes
            # But preserve any emphasis markers within
            formatted_lines.append(f'"{line}"')
        else:
            # Empty line or other - keep as is
            formatted_lines.append(line)
    
    return '\n'.join(formatted_lines)


def create_markdown_conversation(json_file: Path, output_dir: Path) -> str:
    """Convert a single JSON conversation to markdown format."""
    
    with open(json_file, 'r') as f:
        data = json.load(f)
    
    # Extract metadata
    conv_id = data['conversation_id']
    participants = data['participants']
    metadata = data['metadata']
    conversation = data['conversation']
    
    # Create readable filename
    bot1_name = participants['bot1']['full_name']
    bot2_name = participants['bot2']['full_name']
    date = metadata['started_at'][:10]
    time = metadata['started_at'][11:19].replace(':', '')
    
    # Build markdown content
    md_lines = []
    md_lines.append(f"# Conversation: {bot1_name} & {bot2_name}")
    md_lines.append("")
    md_lines.append(f"**Date:** {date}")
    md_lines.append(f"**Time:** {metadata['started_at'][11:19]}")
    md_lines.append(f"**Total Exchanges:** {metadata['total_exchanges']}")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    
    # Add participant info
    md_lines.append("## Participants")
    md_lines.append("")
    md_lines.append(f"- **{bot1_name}** (Port {participants['bot1']['port']})")
    md_lines.append(f"- **{bot2_name}** (Port {participants['bot2']['port']})")
    md_lines.append("")
    md_lines.append("---")
    md_lines.append("")
    md_lines.append("## Conversation")
    md_lines.append("")
    
    # Process conversation exchanges
    for i, exchange in enumerate(conversation, 1):
        timestamp = format_timestamp(exchange['timestamp'])
        
        # Determine who is speaking in this exchange's response
        speaker_name = exchange['speaker']
        
        # Add exchange header
        md_lines.append(f"### Exchange {i}")
        md_lines.append(f"*{timestamp}*")
        md_lines.append("")
        md_lines.append("---")
        md_lines.append("")
        
        # For the FIRST exchange only, show the initial message (prompt)
        if i == 1:
            md_lines.append("## 💬 **System Prompt**")
            md_lines.append("")
            formatted_message = format_dialogue_text(exchange['message'])
            indented_message = '\n'.join('> ' + line if line.strip() else '>' 
                                         for line in formatted_message.split('\n'))
            md_lines.append(indented_message)
            md_lines.append("")
            
            # Determine who responded to the system prompt
            if speaker_name == 'system':
                # Shouldn't happen, but handle it
                current_speaker = participants['bot2']['full_name']
            elif speaker_name == participants['bot1']['name']:
                current_speaker = participants['bot1']['full_name']
            else:
                current_speaker = participants['bot2']['full_name']
        else:
            # For subsequent exchanges, determine speaker from the response
            if speaker_name == participants['bot1']['name']:
                current_speaker = participants['bot1']['full_name']
            else:
                current_speaker = participants['bot2']['full_name']
        
        # Always show the response (this is the actual new content)
        md_lines.append(f"## 💬 **{current_speaker}**")
        md_lines.append("")
        formatted_response = format_dialogue_text(exchange['response'])
        indented_response = '\n'.join('> ' + line if line.strip() else '>' 
                                      for line in formatted_response.split('\n'))
        md_lines.append(indented_response)
        md_lines.append("")
    
    # Create output filename
    output_filename = f"{bot1_name.replace(' ', '_')}_{bot2_name.replace(' ', '_')}_{date}_{time}.md"
    output_path = output_dir / output_filename
    
    # Write markdown file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    
    return output_filename


def group_conversations_by_participants(json_files: List[Path]) -> Dict[str, List[Path]]:
    """Group conversation files by participant pairs."""
    grouped = defaultdict(list)
    
    for json_file in json_files:
        with open(json_file, 'r') as f:
            data = json.load(f)
        
        bot1 = data['participants']['bot1']['name']
        bot2 = data['participants']['bot2']['name']
        
        # Create consistent key (alphabetically sorted)
        key = '_'.join(sorted([bot1, bot2]))
        grouped[key].append(json_file)
    
    return grouped


def main():
    """Main conversion function."""
    # Setup paths
    project_root = Path(__file__).parent.parent
    input_dir = project_root / "logs" / "bot_conversations"
    output_dir = project_root / "docs" / "bot_conversations"
    
    # Create output directory
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Find all JSON conversation files
    json_files = sorted(input_dir.glob("*.json"))
    
    if not json_files:
        print(f"No JSON files found in {input_dir}")
        return
    
    print(f"Found {len(json_files)} conversation files")
    print(f"Converting to markdown in {output_dir}")
    print()
    
    # Group conversations
    grouped = group_conversations_by_participants(json_files)
    
    print(f"Found {len(grouped)} unique conversation pairs:")
    for pair, files in grouped.items():
        print(f"  - {pair}: {len(files)} conversations")
    print()
    
    # Convert each file
    converted_files = []
    for json_file in json_files:
        try:
            output_file = create_markdown_conversation(json_file, output_dir)
            converted_files.append(output_file)
            print(f"✓ Converted: {json_file.name} -> {output_file}")
        except Exception as e:
            print(f"✗ Error converting {json_file.name}: {e}")
    
    print()
    print(f"Successfully converted {len(converted_files)} conversations!")
    print(f"Output directory: {output_dir}")
    
    # Create index file
    create_index_file(output_dir, grouped, converted_files)


def create_index_file(output_dir: Path, grouped: Dict, converted_files: List[str]):
    """Create an index markdown file listing all conversations."""
    
    index_lines = []
    index_lines.append("# Bot-to-Bot Conversations")
    index_lines.append("")
    index_lines.append("This directory contains transcripts of conversations between WhisperEngine AI characters.")
    index_lines.append("")
    index_lines.append("## Overview")
    index_lines.append("")
    index_lines.append(f"- **Total Conversations:** {len(converted_files)}")
    index_lines.append(f"- **Unique Character Pairs:** {len(grouped)}")
    index_lines.append("")
    index_lines.append("## Conversations by Character Pair")
    index_lines.append("")
    
    # Group by character pairs
    for pair_key in sorted(grouped.keys()):
        files = grouped[pair_key]
        pair_name = pair_key.replace('_', ' & ').title()
        
        index_lines.append(f"### {pair_name}")
        index_lines.append("")
        
        # List conversations for this pair
        for json_file in sorted(files):
            with open(json_file, 'r') as f:
                data = json.load(f)
            
            bot1_name = data['participants']['bot1']['full_name']
            bot2_name = data['participants']['bot2']['full_name']
            date = data['metadata']['started_at'][:10]
            time = data['metadata']['started_at'][11:19].replace(':', '')
            exchanges = data['metadata']['total_exchanges']
            
            md_filename = f"{bot1_name.replace(' ', '_')}_{bot2_name.replace(' ', '_')}_{date}_{time}.md"
            
            index_lines.append(f"- [{bot1_name} & {bot2_name} - {date}](./{md_filename}) ({exchanges} exchanges)")
        
        index_lines.append("")
    
    index_lines.append("---")
    index_lines.append("")
    index_lines.append("## About WhisperEngine")
    index_lines.append("")
    index_lines.append("WhisperEngine is a multi-character Discord AI roleplay platform featuring:")
    index_lines.append("")
    index_lines.append("- **Vector-Native Memory**: Qdrant + FastEmbed for semantic conversation storage")
    index_lines.append("- **Database-Driven Characters**: PostgreSQL-based CDL (Character Definition Language)")
    index_lines.append("- **Multi-Bot Platform**: 10+ independent AI characters with unique personalities")
    index_lines.append("- **Character Archetypes**: Real-world, fantasy, and narrative AI personalities")
    index_lines.append("")
    index_lines.append("These conversations showcase the depth and authenticity of character interactions in the WhisperEngine platform.")
    index_lines.append("")
    
    # Write index file
    index_path = output_dir / "README.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(index_lines))
    
    print(f"✓ Created index file: README.md")


if __name__ == "__main__":
    main()
