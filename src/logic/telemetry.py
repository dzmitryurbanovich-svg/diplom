import json
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

class TelemetryManager:
    """
    Handles logging of game events, agent decisions, and outcomes 
    to create a dataset for future fine-tuning and learning.
    """
    def __init__(self, log_dir: str = None):
        if log_dir is None:
            # Check if we are on HF Spaces (usually /app)
            if os.path.exists("/app"):
                self.log_dir = "/app/logs/telemetry"
            else:
                base_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
                self.log_dir = os.path.join(base_path, "logs", "telemetry")
        else:
            self.log_dir = log_dir
            
        print(f"[TELEMETRY] Initializing in: {self.log_dir}", flush=True)
        try:
            os.makedirs(self.log_dir, exist_ok=True)
            # Test write access
            test_file = os.path.join(self.log_dir, ".write_test")
            with open(test_file, "w") as f:
                f.write("test")
            os.remove(test_file)
            print(f"[TELEMETRY] Write permissions verified in {self.log_dir}", flush=True)
        except Exception as e:
            print(f"[TELEMETRY ERROR] Could not initialize or write to {self.log_dir}: {e}", flush=True)

        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.game_log_path = os.path.join(self.log_dir, f"game_{self.session_id}.jsonl")
        self.current_game_history: List[Dict[str, Any]] = []

    def log_turn(self, turn_data: Dict[str, Any], session_id: Optional[str] = None):
        """Logs a single turn's state, action, and rationale."""
        turn_data["timestamp"] = datetime.now().isoformat()
        self.current_game_history.append(turn_data)
        
        # Determine log path
        if session_id:
            path = os.path.join(self.log_dir, f"session_{session_id}.jsonl")
        else:
            path = self.game_log_path

        # Append to log file
        print(f"[TELEMETRY] Logging turn to {path}", flush=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(turn_data, ensure_ascii=False) + "\n")
            f.flush()

    def finalize_game(self, final_scores: Dict[str, int], winner: str):
        """Saves the final result and summary of the game."""
        summary = {
            "session_id": self.session_id,
            "final_scores": final_scores,
            "winner": winner,
            "total_turns": len(self.current_game_history),
            "timestamp": datetime.now().isoformat()
        }
        
        summary_path = os.path.join(self.log_dir, "summary_stats.jsonl")
        print(f"[TELEMETRY] Finalizing game summary to {summary_path}", flush=True)
        print(f"[TELEMETRY] Summary data: {summary}", flush=True)
        try:
            with open(summary_path, "a", encoding="utf-8") as f:
                f.write(json.dumps(summary, ensure_ascii=False) + "\n")
                f.flush()
            print(f"[TELEMETRY] Successfully wrote summary to {summary_path}. Current size: {os.path.getsize(summary_path)} bytes", flush=True)
        except Exception as e:
            print(f"[TELEMETRY ERROR] Failed to write summary: {e}", flush=True)
            
    def list_logs(self) -> List[str]:
        """Returns a list of all telemetry log files."""
        files = []
        if os.path.exists(self.log_dir):
            for f in os.listdir(self.log_dir):
                if f.endswith(".jsonl"):
                    files.append(os.path.join(self.log_dir, f))
        return sorted(files, reverse=True)

    def get_past_lessons(self, agent_name: str, limit: int = 3) -> str:
        """Retrieves historical lessons learned from past wins."""
        summary_path = os.path.join(self.log_dir, "summary_stats.jsonl")
        if not os.path.exists(summary_path):
            return "Legacy Success: Initial cities provide strong foundation in early game."
            
        lessons = []
        try:
            with open(summary_path, "r", encoding="utf-8") as f:
                for line in f:
                    data = json.loads(line)
                    if data.get("winner") == agent_name:
                        lessons.append(f"Win on {data['timestamp'][:10]}: Score {data['final_scores'].get(agent_name)}")
            
            if lessons:
                return "Past Victories: " + " | ".join(lessons[-limit:])
        except Exception:
            pass
            
        return "Tactical Note: Controlling the center of the board increases connectivity options."

# Global instance for easy access
game_telemetry = TelemetryManager()
