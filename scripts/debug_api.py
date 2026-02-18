import requests

def check(url, name):
    print(f"\n--- Checking {name} ---")
    try:
        res = requests.get(url)
        data = res.json()
        print(f"Keys: {list(data.keys()) if isinstance(data, dict) else 'List'}")
        if isinstance(data, dict):
            for k in data.keys():
                if k == 'copyright': continue
                val = data[k]
                print(f"Key '{k}' is type {type(val)}")
                if isinstance(val, list) and len(val) > 0:
                    print(f"First item in '{k}': {val[0]}")
    except Exception as e:
        print(f"Error: {e}")

check("https://muro.sakenowa.com/sakenowa-data/api/brand-flavor-tags", "brand-flavor-tags")
check("https://muro.sakenowa.com/sakenowa-data/api/flavor-tags", "flavor-tags")
