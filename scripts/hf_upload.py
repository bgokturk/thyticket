"""Upload dashboard files to HuggingFace Space."""
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])

README = """\
---
title: TK Fare Tracker
emoji: ✈️
colorFrom: red
colorTo: gray
sdk: streamlit
sdk_version: 1.41.1
app_file: app.py
pinned: false
---
"""

# Upload README.md with correct app_file setting
api.upload_file(
    path_or_fileobj=README.encode(),
    path_in_repo="README.md",
    repo_id="bgokturk/thyticket",
    repo_type="space",
)
print("✓ README.md uploaded")

FILES = ["app.py", "config.py", "requirements.txt", "fares.db"]

for filename in FILES:
    api.upload_file(
        path_or_fileobj=filename,
        path_in_repo=filename,
        repo_id="bgokturk/thyticket",
        repo_type="space",
    )
    print(f"✓ {filename} uploaded")

print("Done.")
