"""Upload dashboard files to HuggingFace Space."""
import os
from huggingface_hub import HfApi

api = HfApi(token=os.environ["HF_TOKEN"])

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
