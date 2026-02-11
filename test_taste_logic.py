from app.reco import estimate_taste_vector

test_cases = [
    "甘口でフルーティなモダンな酒",
    "辛口ですっきり淡麗",
    "濃厚で芳醇なクラシックタイプ",
    "メロンのような華やかな吟醸香",
    "ワインのような酸味とキレ",
]

for text in test_cases:
    vector, scores = estimate_taste_vector(text)
    print(f"Text: {text}")
    print(f"Vector: {vector}")
    print(f"Scores: {scores}")
    print("-" * 20)
