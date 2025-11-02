import json

# Load saved file
with open('datasets/local_backup/code_generation/black_20251102_143642_51.json') as f:
    data = json.load(f)

print(f"Total functions: {len(data)}")
print(f"\nSample function:")
print(f"  Name: {data[0]['func_name']}")
print(f"  Language: {data[0]['language']}")
print(f"  Output preview:")
print(data[0]['output'][:300])
