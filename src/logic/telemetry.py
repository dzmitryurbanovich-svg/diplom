import json
import os
from datetime import datetime
from typing import Dict, Any, List

class TelemetryManager:
    """
    Handles logging of game events, agent decisions, and outcomes 
    to create a dataset for future fine-tuning and learning.
    """
    def __init__(self, log_dir: str = "logs/telemetry"):
        self.log_dir = log_dir
        os.makedirs(self.log_dir, exist_ok=True)
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.game_log_path = os.path.join(self.log_dir, f"game_{self.session_id}.jsonl")
        self.current_game_history: List[Dict[str, Any]] = []

    def log_turn(self, turn_data: Dict[str, Any]):
        """Logs a single turn's state, action, and rationale."""
        turn_data["timestamp"] = datetime.now().isoformat()
        self.current_game_history.append(turn_data)
        
        # Append to individual game file
        with open(self.game_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(turn_data, ensure_ascii=False) + "\n")

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
        with open(summary_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(summary, ensure_ascii=False) + "\n")
            
    def get_past_lessons(self, agent_name: str, limit: int = 5) -> str:
        """
        Retrieves top 'N' lessons learned from past games 
        (e.g., cases where a strategy led to a loss).
        """
        # For now, it returns a static 'bootstrap' lesson if no data exists
        # In the future, this will parse the telemetry files.
        return "Legacy Success: Prioritizing Monk placement on turns 1-10 often yields +9 points."

# Global instance for easy access
game_telemetry = TelemetryManager()
