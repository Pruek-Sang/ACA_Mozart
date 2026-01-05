
import json
import re

# Mock Logger
class Logger:
    def info(self, msg): print(f"[INFO] {msg}")
    def warning(self, msg): print(f"[WARN] {msg}")
    def error(self, msg): print(f"[ERROR] {msg}")

logger = Logger()

# Mock extracted data from LLM
extracted = {
    "floor_distances": {"1": 15, "2": 25},  # This should be used!
    "rooms": [{"name": "Living", "type": "living", "floor": 1}],
    "loads": [{"room_name": "Living", "device": "SOCKET", "quantity": 1}]
}

normalized_query = "Test Query with distances 15m and 25m"

def _extract_floor_distances(text):
    print("   -> Fallback Regex method called!")
    return {1: 99.0} # Fake regex result to distinguish

def reproduce_the_bug():
    print("="*60)
    print("🔬 SIMULATION: RUNNING THE BUGGY CODE PATH")
    print("="*60)
    print(f"Input extracted['floor_distances']: {extracted['floor_distances']}")

    try:
        # =========================================================
        # THE BUGGY CODE BLOCK (Reconstructed from memory/history)
        # =========================================================
        
        # 🆕 [RAG-FIX v2] Use floor_distances from LLM first, fallback to regex
        # Priority: LLM floor_distances > Regex extraction > Floor defaults
        
        print("\n[Code Execution] li_floor_distances = extracted.get(...)")
        li_floor_distances = extracted.get("floor_distances", {})  # ❌ Typo: li_ instead of llm_
        
        print("[Code Execution] if llm_floor_distances: ...")
        if llm_floor_distances:  # ❌ NameError here!
            # Convert string keys to int if needed
            floor_distances = {int(k): float(v) for k, v in llm_floor_distances.items() if v}
            logger.info(f"[TRACE-VD-1] LLM floor_distances raw: {llm_floor_distances}")
            logger.info(f"[TRACE-VD-2] Converted floor_distances: {floor_distances}")
        else:
            # Fallback to regex extraction
            floor_distances = _extract_floor_distances(normalized_query)
            logger.info(f"[TRACE-VD-1b] Regex extracted floor_distances: {floor_distances}")

        # Store floor_distances for downstream
        extracted["floor_distances"] = floor_distances
        
        print(f"\n✅ SUCCESS? floor_distances = {floor_distances}")
    
    except NameError as e:
        print(f"\n❌ CRASHED: NameError caught! -> {e}")
        print("   This confirms that 'llm_floor_distances' was undefined.")
    except Exception as e:
        print(f"\n❌ CRASHED: Other error -> {e}")

if __name__ == "__main__":
    reproduce_the_bug()
