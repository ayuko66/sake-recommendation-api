import requests
import json
import time
import sys

def test_recommend():
    url = "http://localhost:8000/recommend"
    
    # Wait for server
    for i in range(10):
        try:
            requests.get("http://localhost:8000/health")
            break
        except:
            print("Waiting for server...")
            time.sleep(1)
    else:
        print("Server not ready.")
        sys.exit(1)

    # 1. Basic Request
    print("\n=== Test 1: Basic Request (Fruity, Sweet) ===")
    payload = {
        "text": "フルーティで甘口な日本酒",
        "top_k": 3,
        "debug": True
    }
    
    try:
        res = requests.post(url, json=payload)
        res.raise_for_status()
        data = res.json()
        print("Response Keys:", data.keys())
        
        items = data.get("recommendations", [])
        if not items:
            print("WARNING: No recommendations returned.")
        else:
            print(f"Top 1: {items[0]['name']} (Score: {items[0]['score']:.4f})")
            print(f"Reason: {items[0]['reason']}")
            print(f"Distance: {items[0]['distance']:.4f}")
            print(f"Taste Vector: {items[0]['taste_vector']}")
            
        print(f"Query Vector: {data['query']['taste_vector']}")
            
    except Exception as e:
        print(f"Error: {e}")

    # 2. Filter Request
    print("\n=== Test 2: Filter Request (Niigata, Dry) ===")
    payload_filter = {
        "text": "キレのある辛口",
        "top_k": 3,
        "filters": {"prefecture": ["新潟県"]}, # DBのデータ形式に合わせる ("新潟" or "新潟県"?)
        "debug": True
    }
    
    try:
        res = requests.post(url, json=payload_filter)
        res.raise_for_status()
        data = res.json()
        
        items = data.get("recommendations", [])
        if not items:
             print("No recommendations found with filter.")

        for item in items:
            print(f"Name: {item['name']}, Pref: {item['prefecture']}, Score: {item['score']:.4f}")
            if "新潟" not in item["prefecture"]:
                print(f"ERROR: Filter failed. Got {item['prefecture']}")
            print(f"Reason: {item['reason']}")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_recommend()
