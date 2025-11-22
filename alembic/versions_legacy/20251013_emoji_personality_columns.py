"""Add emoji personality columns to characters table

Revision ID: emoji_personality_cols
Revises: drop_legacy_roleplay
Create Date: 2025-10-13 22:45:00.000000

Description:
    Add emoji personality configuration columns to the characters table
    to support the unified DatabaseEmojiSelector system.
    
    New Columns:
    1. emoji_frequency - How often character uses emojis (none, minimal, low, moderate, high, selective_symbolic)
    2. emoji_style - Character's emoji aesthetic (warm_expressive, mystical_ancient, technical_minimal, etc.)
    3. emoji_combination - How emojis mix with text (emoji_only, text_only, text_plus_emoji, text_with_accent_emoji, minimal_symbolic_emoji)
    4. emoji_placement - Where to place emojis (end_of_message, integrated_throughout, sparse_meaningful, ceremonial_meaningful)
    5. emoji_age_demographic - Age-appropriate emoji usage (gen_z, millennial, gen_x, timeless_eternal)
    6. emoji_cultural_influence - Cultural context for emoji choice (general, latina_warm, cosmic_mythological, british_reserved, etc.)
    
    Justification:
    - Consolidates THREE redundant emoji systems into ONE database-driven system
    - Replaces legacy JSON emoji_personality configs (characters/examples_legacy_backup/)
    - Eliminates wasteful emoji array dumping into LLM prompts (~100-200 tokens saved per message)
    - Enables intelligent post-LLM emoji selection using RoBERTa bot emotion analysis
    
    Migration Strategy:
    - All columns have sensible defaults ('moderate', 'general', etc.)
    - Character-specific settings will be added in data migration
    - Elena: high frequency, warm_expressive, text_plus_emoji, integrated_throughout
    - Dream: selective_symbolic, mystical_ancient, minimal_symbolic_emoji, sparse_meaningful
    
    Related Documentation:
    - docs/architecture/EMOJI_SYSTEM_CONSOLIDATION_PLAN.md
    
    Related Systems:
    - character_emoji_patterns table (already exists, stores emoji sequences)
    - src/intelligence/database_emoji_selector.py (new component to be created)
    - Phase 7.6 in message_processor.py (emoji decoration after bot emotion analysis)

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'emoji_personality_cols'
down_revision = 'drop_legacy_roleplay'
branch_labels = None
depends_on = None


def upgrade():
    print("\n✨ ADDING EMOJI PERSONALITY COLUMNS TO CHARACTERS TABLE")
    print("=" * 70)
    
    conn = op.get_bind()
    columns_to_add = [
        ('emoji_frequency', 'moderate', 'How often character uses emojis: none, minimal, low, moderate, high, selective_symbolic'),
        ('emoji_style', 'general', 'Character emoji aesthetic: warm_expressive, mystical_ancient, technical_minimal, etc.'),
        ('emoji_combination', 'text_with_accent_emoji', 'How emojis mix with text: emoji_only, text_only, text_plus_emoji, text_with_accent_emoji, minimal_symbolic_emoji'),
        ('emoji_placement', 'end_of_message', 'Where to place emojis: end_of_message, integrated_throughout, sparse_meaningful, ceremonial_meaningful'),
        ('emoji_age_demographic', 'millennial', 'Age-appropriate emoji usage: gen_z, millennial, gen_x, timeless_eternal'),
        ('emoji_cultural_influence', 'general', 'Cultural context for emoji choice: general, latina_warm, cosmic_mythological, british_reserved, etc.')
    ]
    
    # Add emoji personality configuration columns
    print("\n📋 Adding emoji personality columns...")
    
    for column_name, default_value, comment in columns_to_add:
        # Check if column already exists
        column_exists_result = conn.execute(sa.text(f"""
            SELECT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'characters' 
                AND column_name = '{column_name}'
            )
        """))
        row = column_exists_result.fetchone()
        column_exists = row[0] if row else False
        
        if not column_exists:
            if 'influence' in column_name:
                op.add_column('characters', sa.Column(
                    column_name,
                    sa.String(100),
                    nullable=False,
                    server_default=default_value,
                    comment=comment
                ))
            else:
                op.add_column('characters', sa.Column(
                    column_name,
                    sa.String(50),
                    nullable=False,
                    server_default=default_value,
                    comment=comment
                ))
            print(f"    ✅ Added {column_name} column")
        else:
            print(f"    ℹ️  Column {column_name} already exists, skipping")
    
    print("✅ Emoji personality columns processing complete!")
    
    # Set character-specific emoji personality settings
    print("\n🎭 Setting character-specific emoji personalities...")
    
    # Elena Rodriguez - High frequency, warm, expressive
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'high',
            emoji_style = 'warm_expressive',
            emoji_combination = 'text_plus_emoji',
            emoji_placement = 'integrated_throughout',
            emoji_age_demographic = 'millennial',
            emoji_cultural_influence = 'latina_warm'
        WHERE normalized_name = 'elena'
    """)
    print("  ✓ Elena Rodriguez: high frequency, warm_expressive, integrated_throughout")
    
    # Dream of the Endless - Rare but meaningful, mystical
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'selective_symbolic',
            emoji_style = 'mystical_ancient',
            emoji_combination = 'minimal_symbolic_emoji',
            emoji_placement = 'sparse_meaningful',
            emoji_age_demographic = 'timeless_eternal',
            emoji_cultural_influence = 'cosmic_mythological'
        WHERE normalized_name = 'dream'
    """)
    print("  ✓ Dream: selective_symbolic, mystical_ancient, sparse_meaningful")
    
    # Marcus Thompson - Minimal, analytical
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'low',
            emoji_style = 'technical_analytical',
            emoji_combination = 'text_with_accent_emoji',
            emoji_placement = 'end_of_message',
            emoji_age_demographic = 'gen_x',
            emoji_cultural_influence = 'academic_professional'
        WHERE normalized_name = 'marcus'
    """)
    print("  ✓ Marcus Thompson: low frequency, technical_analytical, end_of_message")
    
    # Aethys - Mystical, rare, ceremonial
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'selective_symbolic',
            emoji_style = 'mystical_transcendent',
            emoji_combination = 'minimal_symbolic_emoji',
            emoji_placement = 'ceremonial_meaningful',
            emoji_age_demographic = 'timeless_eternal',
            emoji_cultural_influence = 'cosmic_omnipotent'
        WHERE normalized_name = 'aethys'
    """)
    print("  ✓ Aethys: selective_symbolic, mystical_transcendent, ceremonial_meaningful")
    
    # Gabriel - Reserved British gentleman style
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'minimal',
            emoji_style = 'refined_reserved',
            emoji_combination = 'text_with_accent_emoji',
            emoji_placement = 'end_of_message',
            emoji_age_demographic = 'timeless_eternal',
            emoji_cultural_influence = 'british_reserved'
        WHERE normalized_name = 'gabriel'
    """)
    print("  ✓ Gabriel: minimal frequency, refined_reserved, british_reserved")
    
    # Sophia Blake - Professional but warm
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'moderate',
            emoji_style = 'professional_warm',
            emoji_combination = 'text_plus_emoji',
            emoji_placement = 'integrated_throughout',
            emoji_age_demographic = 'millennial',
            emoji_cultural_influence = 'corporate_modern'
        WHERE normalized_name = 'sophia'
    """)
    print("  ✓ Sophia Blake: moderate frequency, professional_warm, corporate_modern")
    
    # Ryan Chen - Moderate, casual gamer style
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'moderate',
            emoji_style = 'casual_gaming',
            emoji_combination = 'text_plus_emoji',
            emoji_placement = 'integrated_throughout',
            emoji_age_demographic = 'millennial',
            emoji_cultural_influence = 'gaming_tech'
        WHERE normalized_name = 'ryan'
    """)
    print("  ✓ Ryan Chen: moderate frequency, casual_gaming, gaming_tech")
    
    # Jake Sterling - Adventurous, expressive
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'high',
            emoji_style = 'adventurous_expressive',
            emoji_combination = 'text_plus_emoji',
            emoji_placement = 'integrated_throughout',
            emoji_age_demographic = 'millennial',
            emoji_cultural_influence = 'outdoors_adventure'
        WHERE normalized_name = 'jake'
    """)
    print("  ✓ Jake Sterling: high frequency, adventurous_expressive, outdoors_adventure")
    
    # Aetheris - Philosophical AI, thoughtful
    op.execute("""
        UPDATE characters 
        SET 
            emoji_frequency = 'low',
            emoji_style = 'philosophical_contemplative',
            emoji_combination = 'text_with_accent_emoji',
            emoji_placement = 'sparse_meaningful',
            emoji_age_demographic = 'timeless_eternal',
            emoji_cultural_influence = 'ai_consciousness'
        WHERE normalized_name = 'aetheris'
    """)
    print("  ✓ Aetheris: low frequency, philosophical_contemplative, ai_consciousness")
    
    print("\n✅ Character-specific emoji personalities configured!")
    print("\n" + "=" * 70)
    print("✨ EMOJI PERSONALITY MIGRATION COMPLETE")
    print("\nNext Steps:")
    print("  1. Create src/intelligence/database_emoji_selector.py")
    print("  2. Integrate into message_processor.py (Phase 7.6)")
    print("  3. Remove legacy emoji prompt injection from cdl_ai_integration.py")
    print("=" * 70 + "\n")


def downgrade():
    print("\n🔄 ROLLING BACK EMOJI PERSONALITY COLUMNS")
    print("=" * 70)
    
    # Drop emoji personality columns
    op.drop_column('characters', 'emoji_cultural_influence')
    op.drop_column('characters', 'emoji_age_demographic')
    op.drop_column('characters', 'emoji_placement')
    op.drop_column('characters', 'emoji_combination')
    op.drop_column('characters', 'emoji_style')
    op.drop_column('characters', 'emoji_frequency')
    
    print("✅ Emoji personality columns removed")
    print("=" * 70 + "\n")
