import requests

url = "https://githubactionschatbot.onrender.com/analyze"
data = {
    "api_key": "your_api_key_here",
    "logs": 'Traceback (most recent call last):\n  File "main.py", line 10, in <module>\n    x = 1 / 0\nZeroDivisionError: division by zero'
}

response = requests.post(url, json=data)
print(response.json())