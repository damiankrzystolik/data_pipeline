import requests
import json

# url = 'https://api.nbp.pl/api/exchangerates/tables/a/today/'
# response = requests.get(url)

# debug <
# 1.
# print(f"Status: {response.status_code}")
# print(f"Response text: {response.text}")

# 2.
# Rozwiązania:
#   1. Sprawdź ostatnie dostępne dane — użyj /last/ zamiast /today/:
url = 'https://api.nbp.pl/api/exchangerates/tables/a/last/5/'
response = requests.get(url)
# 2. Dodaj obsługę błędów — sprawdź status przed parsowaniem JSON:
if response.status_code == 200:
  print(json.dumps(response.json(), indent=2))
else:
  print(f"Error {response.status_code}: {response.text}")

#  >>>
# print(json.dumps(response.json(), indent=2))
