from pathlib import Path

dataset = Path("dataset") / "Garbage classification" / "Garbage classification"

for folder in sorted(dataset.iterdir()):
    if folder.is_dir():
        print(folder.name, len(list(folder.glob("*"))))