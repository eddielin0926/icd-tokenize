"""
This script is used to analyze the dataset. Output the most frequent 50 labels.
"""
import ast
import os
import time

import pandas as pd
from rich.console import Console

# Create rich console
console = Console()

# Start process timing
start_time = time.time()
console.print(":rocket: start processing")

data_dir = "tmp"
data_dir = os.path.join(data_dir, os.listdir(data_dir)[-1])
data_dir = [os.path.join(data_dir, f) for f in os.listdir(data_dir)]
data_dir = list(filter(os.path.isdir, data_dir))
files = []
for d in data_dir:
    for f in os.listdir(d):
        files.append(os.path.join(d, f))

targets_list = []
for file in files:
    # Load Dataset
    df = pd.read_csv(file)
    for _, row in df.iterrows():
        inputs = ast.literal_eval(row["inputs"])
        targets = ast.literal_eval(row["targets"])
        for target in targets:
            if targets not in inputs:
                targets_list.append(target)

labels_count = pd.Series(targets_list).value_counts()
labels_count = labels_count.sort_values(ascending=False)
most_labels = labels_count.head(50)
print(most_labels)

# Finish process timing
end_time = time.time()
elapsed_time = end_time - start_time

# Print final result
console.print(f":hourglass: elapsed time:\t[green bold]{round(elapsed_time, 3)}s[/]")
