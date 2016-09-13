import json

import requests


class RobotsTXTParser:
    def __init__(self, domain, user_agent):
        URL = "{}/robots.txt".format(domain)

        headers = {
            "User-Agent": user_agent
        }

        robot_data = requests.get(
            url=URL,
            headers=headers
        )

        if robot_data.status_code is not 200:
            print(robot_data.status_code)
            return

        robot_data.encoding = "utf-8-sig"

        current_agent_rules = "*"

        agent_mapping = {
            u'*': "Any"
        }

        rules = {}

        try:
            for line in robot_data.text.split("\n"):
                line = line.strip()

                if len(line) < 2:
                    current_agent_rules = agent_mapping["*"]
                    continue

                if line[0] == "#":
                    # ignore dis shit, dis is comment
                    continue

                if "#" in line:
                    # ignore after dis mark cuz dis shit is comments
                    before_comment = line.split("#")
                    line = before_comment[0].strip()

                command_splitter = line.split(":", 1)

                if command_splitter[0].lower() == "user-agent":
                    intermediate_agent = command_splitter[1].strip()
                    current_agent_rules = agent_mapping[intermediate_agent] if intermediate_agent in agent_mapping else intermediate_agent

                    if current_agent_rules not in rules:
                        rules[current_agent_rules] = {"allow": [], "disallow": [], "crawl-delay": 0, "user-agent": current_agent_rules, "sitemap": []}

                    continue

                if type(rules[current_agent_rules][command_splitter[0].lower()]) is not type([]):
                    rules[current_agent_rules][command_splitter[0].lower()] = command_splitter[1].strip()
                else:
                    rules[current_agent_rules][command_splitter[0].lower()].append(command_splitter[1].strip())

                print(json.dumps(rules))
        except Exception as e:
            print(str(e))
