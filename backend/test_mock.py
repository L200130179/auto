from video_processor import format_srt_time

transcript_data = [
    {'text': 'hello', 'start': 29.0, 'duration': 2.0},
    {'text': 'world', 'start': 31.0, 'duration': 3.0},
    {'text': 'overlap', 'start': 32.0, 'duration': 4.0}
]

start_time = 30
end_time = 60

idx = 1
with open('test.srt', 'w', encoding='utf-8') as sf:
    for i in range(len(transcript_data)):
        item = transcript_data[i]
        try:
            s = item['start']
            d = item['duration']
            text = item['text']
        except (KeyError, TypeError):
            s = getattr(item, 'start', 0)
            d = getattr(item, 'duration', 0)
            text = getattr(item, 'text', '')
            
        e = s + d
        
        # Hindari duplikasi tumpuk (stacking) dengan memotong durasi jika overlap kalimat berikutnya
        if i + 1 < len(transcript_data):
            next_item = transcript_data[i+1]
            try:
                next_s = next_item['start']
            except (KeyError, TypeError):
                next_s = getattr(next_item, 'start', e)
                
            if e > next_s:
                e = next_s
                
        # Memastikan dialog berada di dalam rentang klip
        if e >= start_time and s <= end_time:
            rel_s = max(0, s - start_time)
            rel_e = min(end_time - start_time, e - start_time)
            if rel_s >= rel_e:
                continue
                
            s_str = format_srt_time(rel_s)
            e_str = format_srt_time(rel_e)
            text = text.replace('\n', ' ')
            sf.write(f"{idx}\n{s_str} --> {e_str}\n{text}\n\n")
            idx += 1
            print(f"[{s_str} --> {e_str}] {text}")

print("Total lines:", idx - 1)
