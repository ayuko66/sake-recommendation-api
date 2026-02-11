import json
from app import database as db
from app.models import SakeListItem, SakeDetail

def test_db():
    print("Testing get_sakes...")
    sakes = db.get_sakes(page=1, limit=5)
    for s in sakes:
        print(f"  - {s.name} ({s.brewery})")
    
    if sakes:
        sake_id = sakes[0].sake_id
        print(f"\nTesting get_sake_by_id({sake_id})...")
        sake = db.get_sake_by_id(sake_id)
        if sake:
            print(f"  Name: {sake.name}")
            print(f"  Prefecture: {sake.prefecture}")
            if sake.taste_profile:
                print(f"  Taste: {sake.taste_profile}")
        else:
            print("  Not found")

    print("\nTesting search_sakes('獺祭')...")
    results = db.search_sakes("獺祭", limit=5)
    for r in results:
        print(f"  - {r.name}")

if __name__ == "__main__":
    test_db()
