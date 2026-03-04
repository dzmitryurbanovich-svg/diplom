import os
from huggingface_hub import HfApi
api = HfApi(token=os.environ.get("HF_TOKEN"))
repo_id = "dzmitro/carcassonne-ai"
files = api.list_repo_files(repo_id=repo_id, repo_type="space")
print("\n".join(files))
