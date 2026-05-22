import requests

data = {
    "url": "https://www.youtube.com/watch?v=za8EqDmgeiM",
    "with_subtitle": False,
    "clip_duration": 15,
    "layout_mode": "gaussian_blur"
}
try:
    print("Testing API...")
    resp = requests.post("http://localhost:5000/api/process", json=data)
    print("Status:", resp.status_code)
    print("Response:", resp.text)
except Exception as e:
    print("Failed to request:", e)
