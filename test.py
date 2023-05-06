import pandas as pd

l = [{
        "file": 'path',
        "correct": 1,
        "total": 100,
        "accuracy": 0.01
    }]

df = pd.DataFrame(l)
print(df.head())