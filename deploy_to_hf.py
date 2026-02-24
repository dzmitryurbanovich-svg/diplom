import os
import sys
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
            "app.py", 
            "requirements.txt", 
            "src/**", 
            "assets/**", 
            "demos/agents_hf.py", 
            "demos/agents_baseline.py",
            "Dockerfile"
        ],
        ignore_patterns=[
            "venv/**",
            "__pycache__/**",
            "*.pyc",
            "*.zip",
            ".git/**",
            "deployment_package/**"
        ],
        commit_message="🚀 Deploying Phase 5: High-Fidelity UI with Real Asset Graphics"
    )
    print("\n[SUCCESS] Deployment complete!")
    print(f"Your app is now live at: https://huggingface.co/spaces/{repo_id}")
    
except Exception as e:
    print(f"\n[ERROR] Deployment failed: {e}")
    sys.exit(1)
