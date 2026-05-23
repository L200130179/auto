import json

log_file = r"C:\Users\IT\.gemini\antigravity\brain\36e1100b-35f3-4749-b05a-85f84b36d299\.system_generated\logs\transcript.jsonl"

search_terms = ["video_processor.py", "task_worker.py"]
results = []

with open(log_file, "r", encoding="utf-8") as f:
    for line in f:
        try:
            data = json.loads(line)
            step_idx = data.get("step_index", 0)
            if step_idx >= 511:
                continue
            content = data.get("content", "")
            if not content:
                tool_calls = data.get("tool_calls", [])
                content = str(tool_calls)
            
            for term in search_terms:
                if term in content:
                    results.append((step_idx, data.get("type", ""), term, content[:200] + "..."))
                    break
        except Exception as e:
            pass

print(f"Found {len(results)} matching lines.")
for step, step_type, term, snippet in results[-40:]:
    print(f"Step {step} ({step_type}) [{term}]: {snippet}")
