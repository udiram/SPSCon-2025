#!/usr/bin/env python3
"""
Regenerate tags for all posters using the new LLM-based smart tagging system.
This script preserves old tags as backup and processes in batches to respect API limits.
"""

import json
import time
from app import create_app
from models import db, Poster
from utils.tag_generator import generate_tags_for_poster

def regenerate_all_tags(batch_size=10, delay=2):
    """
    Regenerate tags for all posters.
    
    Args:
        batch_size: Number of posters to process before pausing
        delay: Seconds to wait between batches (to respect API rate limits)
    """
    app = create_app()
    
    with app.app_context():
        posters = Poster.query.order_by(Poster.id).all()
        total = len(posters)
        
        print(f"🏷️  Regenerating tags for {total} posters...")
        print(f"   Batch size: {batch_size}")
        print(f"   Delay between batches: {delay}s")
        print()
        
        processed = 0
        success = 0
        failed = 0
        
        for i, poster in enumerate(posters):
            try:
                # Store old tags as backup
                old_tags = poster.tags
                
                # Generate new tags with LLM
                new_tags = generate_tags_for_poster(poster, use_llm=True)
                
                # Update poster tags
                poster.tags = json.dumps(new_tags)
                
                processed += 1
                success += 1
                
                # Progress indicator
                if processed % 10 == 0:
                    print(f"   Processed {processed}/{total} posters... ({success} success, {failed} failed)")
                
                # Commit in batches
                if processed % batch_size == 0:
                    db.session.commit()
                    print(f"   💾 Committed batch. Waiting {delay}s...")
                    time.sleep(delay)
                
            except Exception as e:
                print(f"   ⚠️  Error processing poster {poster.id} ({poster.title[:50]}...): {e}")
                failed += 1
                continue
        
        # Final commit
        try:
            db.session.commit()
            print()
            print("✅ Tag regeneration complete!")
            print(f"   Total processed: {processed}")
            print(f"   Success: {success}")
            print(f"   Failed: {failed}")
        except Exception as e:
            print(f"❌ Error committing final batch: {e}")
            db.session.rollback()

def regenerate_single_poster(poster_id):
    """Regenerate tags for a single poster (for testing)"""
    app = create_app()
    
    with app.app_context():
        poster = Poster.query.get(poster_id)
        if not poster:
            print(f"❌ Poster {poster_id} not found")
            return
        
        print(f"📝 Poster: {poster.title}")
        print(f"   Old tags: {poster.tags}")
        
        new_tags = generate_tags_for_poster(poster, use_llm=True)
        
        print(f"   New tags: {json.dumps(new_tags)}")
        print()
        print("Would you like to save these tags? (y/n): ", end='')
        
        if input().lower() == 'y':
            poster.tags = json.dumps(new_tags)
            db.session.commit()
            print("✅ Tags saved!")
        else:
            print("❌ Tags not saved")

if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1:
        # Single poster mode
        try:
            poster_id = int(sys.argv[1])
            regenerate_single_poster(poster_id)
        except ValueError:
            print("Usage: python regenerate_tags.py [poster_id]")
            print("   Run without arguments to process all posters")
    else:
        # Batch mode
        print("⚠️  This will regenerate tags for ALL posters using LLM.")
        print("   This may take several minutes and will use API credits.")
        print()
        print("Continue? (y/n): ", end='')
        
        if input().lower() == 'y':
            regenerate_all_tags(batch_size=10, delay=2)
        else:
            print("❌ Cancelled")


