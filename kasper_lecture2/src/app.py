import requests

URL = "https://en.wikipedia.org/robots.txt"
USER_AGENT = "iIzHax0r"

headers = {
    "User-Agent": USER_AGENT
}

robot_data = requests.get(
    url=URL,
    headers=headers
)

for line in robot_data.content.decode(robot_data.encoding).split("\n"):
    print(line)
