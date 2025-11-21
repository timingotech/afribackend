import requests
import json

URL = "https://afribackend-production-e293.up.railway.app/api/users/test-email/"
PARAMS = {"email": "oyenugaridwan@gmail.com"}

print(f"Testing Email Endpoint: {URL}")
print(f"Recipient: {PARAMS['email']}")

try:
    response = requests.get(URL, params=PARAMS, timeout=30)
    print(f"Status Code: {response.status_code}")
    try:
        print("Response Body:")
        print(json.dumps(response.json(), indent=2))
    except:
        print("Response Text:")
        print(response.text)
except Exception as e:
    print(f"Error: {e}")
