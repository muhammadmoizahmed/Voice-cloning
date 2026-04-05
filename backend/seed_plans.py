"""
Manual script to seed default plans into database
Run: python seed_plans.py
"""
import sys
sys.path.insert(0, 'd:/cloning/voiceforge-ai/backend')

from sqlalchemy.orm import Session
from app.database import SessionLocal, Plan

def seed_plans_force():
    db = SessionLocal()
    try:
        # Check existing plans
        existing = db.query(Plan).all()
        print(f"Found {len(existing)} existing plans")
        for p in existing:
            print(f"  - {p.name}: {p.display_name}")
        
        # Delete all existing plans and re-seed
        if existing:
            print("\nDeleting existing plans...")
            for p in existing:
                db.delete(p)
            db.commit()
            print("Deleted existing plans")
        
        # Create all plans
        default_plans = [
            Plan(
                name="FREE",
                display_name="Free",
                description="Try it out",
                price_monthly=0,
                price_yearly=None,
                audio_limit=3,
                video_limit=0,
                voice_clone_limit=1,
                features='["3 audio generations", "Basic quality", "Watermark", "Email support"]',
                is_active=True,
                is_popular=False,
                sort_order=1
            ),
            Plan(
                name="STARTER",
                display_name="Starter",
                description="Perfect start",
                price_monthly=5,
                price_yearly=50,
                audio_limit=50,
                video_limit=10,
                voice_clone_limit=3,
                features='["50 audio/month", "High quality", "No watermark", "Priority support"]',
                is_active=True,
                is_popular=False,
                sort_order=2
            ),
            Plan(
                name="PRO",
                display_name="Pro",
                description="For creators",
                price_monthly=15,
                price_yearly=150,
                audio_limit=200,
                video_limit=50,
                voice_clone_limit=10,
                features='["200 audio/month", "Ultra quality", "API access", "24/7 support"]',
                is_active=True,
                is_popular=True,
                sort_order=3
            ),
            Plan(
                name="BUSINESS",
                display_name="Business",
                description="For teams",
                price_monthly=30,
                price_yearly=300,
                audio_limit=500,
                video_limit=100,
                voice_clone_limit=25,
                features='["500 audio/month", "Ultra quality", "Full API", "Team collaboration"]',
                is_active=True,
                is_popular=False,
                sort_order=4
            ),
            # Bulk Credit Packages
            Plan(
                name="CREDIT_50",
                display_name="50 Credits",
                description="Best for beginners",
                price_monthly=20,
                price_yearly=None,
                audio_limit=50,
                video_limit=0,
                voice_clone_limit=0,
                features='["50 audio credits", "Never expires", "No subscription needed", "Best for beginners"]',
                is_active=True,
                is_popular=False,
                sort_order=5
            ),
            Plan(
                name="CREDIT_100",
                display_name="100 Credits",
                description="Most popular",
                price_monthly=35,
                price_yearly=None,
                audio_limit=100,
                video_limit=0,
                voice_clone_limit=0,
                features='["100 audio credits", "Never expires", "No subscription needed", "Most popular", "Save $65"]',
                is_active=True,
                is_popular=True,
                sort_order=6
            ),
            Plan(
                name="CREDIT_200",
                display_name="200 Credits",
                description="Best value",
                price_monthly=60,
                price_yearly=None,
                audio_limit=200,
                video_limit=0,
                voice_clone_limit=0,
                features='["200 audio credits", "Never expires", "No subscription needed", "Best value", "Save $140"]',
                is_active=True,
                is_popular=False,
                sort_order=7
            )
        ]
        
        for plan in default_plans:
            db.add(plan)
        
        db.commit()
        print(f"\n✅ Successfully seeded {len(default_plans)} plans!")
        
        # Verify
        plans = db.query(Plan).all()
        print(f"\nTotal plans in database: {len(plans)}")
        for p in plans:
            print(f"  - {p.name}: {p.display_name} (${p.price_monthly})")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    seed_plans_force()
