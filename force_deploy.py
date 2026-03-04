import os
from huggingface_hub import HfApi
api = HfApi(token=os.environ.get("HF_TOKEN"))
repo_id = "dzmitro/carcassonne-ai"
print("[*] Deleting old frontend files...")
try:
    api.delete_folder(repo_id=repo_id, folder_path="frontend/dist", repo_type="space")
except Exception as e:
    print(f"Warning: {e}")
print("[*] Uploading everything fresh...")
api.upload_folder(
    folder_path=".",
    repo_id=repo_id,
    repo_type="space",
    allow_patterns=["server.py", "requirements.txt", "src/**", "assets/**", "frontend/dist/**", "Dockerfile"],
    commit_message="🚀 MEGA FORCE DEPLOY: Cleaned old dist"
)
print("[SUCCESS] Forced deployment complete!")
