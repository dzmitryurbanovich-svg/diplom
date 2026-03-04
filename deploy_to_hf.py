import os
import sys
import time
from huggingface_hub import HfApi

# Ensure the token is available
hf_token = os.environ.get("HF_TOKEN")
if not hf_token:
    print("[ERROR] HF_TOKEN is not set.")
    print("Please run: export HF_TOKEN='your_hf_token_here'")
    sys.exit(1)

api = HfApi(token=hf_token)

repo_id = "dzmitro/carcassonne-ai"

print(f"[*] Starting deployment to Hugging Face Space: {repo_id}")
print("[*] Uploading files... (this may take a minute for all the high-quality assets)")

try:
    api.upload_folder(
        folder_path=".",
        repo_id=repo_id,
        repo_type="space",
        allow_patterns=[
            "server.py", 
            "requirements.txt", 
            "src/**", 
            "assets/**", 
            "frontend/dist/**",
            "Dockerfile"
        ],
        ignore_patterns=[
            "venv/**",
            "frontend/src/**",
            "frontend/node_modules/**",
            "__pycache__/**",
            "*.pyc",
            ".git/**"
        ],
        delete_patterns=[
            "frontend/dist/assets/*"
        ],
        commit_message=f"🚀 Deploying React+FastAPI: Force Sync Assets {int(time.time())}"
    )
    print("\n[SUCCESS] Deployment complete!")
    print(f"Your app is now live at: https://huggingface.co/spaces/{repo_id}")
    
except Exception as e:
    print(f"\n[ERROR] Deployment failed: {e}")
    sys.exit(1)
