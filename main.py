from dotenv import load_dotenv
from pprint import pprint
import json
import openai
import notion_client as nc
import string
import os

load_dotenv()

notion = nc.Client(auth=os.getenv("NOTION_TOKEN"))
openai.api_key = os.getenv("OPENAI_TOKEN")


def categorize_tasks(tasks, curr_state) -> str:
    with open("prompts/categorize_para.txt", "r") as text_prompt:
        prompt = string.Template(template=text_prompt.read())
        prompt = prompt.substitute(tasks=tasks, curr_state=curr_state)

        completion = openai.Completion.create(
            model="text-davinci-003",
            prompt=prompt,
            temperature=0.7,
            max_tokens=2048,
            top_p=1,
            frequency_penalty=0,
            presence_penalty=0,
        )

        # Remove leading text before json output
        message = completion.choices[0].text
        index = message.find("{")
        output = message[index:]

        return output


def get_current_state():
    parent_id = os.getenv("NOTION_PARENT_ID")
    pages = notion.blocks.children.list(parent_id)["results"]
    area_db_id = [
        db for db in pages
        if "child_database" in db and db["child_database"]["title"] == "Areas"
    ][0]["id"]
    areas = notion.databases.query(**{"database_id": area_db_id})["results"]

    curr_state = {}
    for area in areas:
        area_title = area["properties"]["Name"]["title"][0]["text"]["content"]
        curr_state[area_title] = {}
        project_ids = [
            project_id["id"] for project_id in area["properties"]["Projects"]["relation"]
        ]
        for project_id in project_ids:
            project = notion.pages.retrieve(page_id=project_id)
            project_title = project["properties"]["Name"]["title"][0]["text"]["content"]
            curr_state[area_title][project_title] = []

            task_ids = [task["id"] for task in project["properties"]["Tasks"]["relation"]]
            for task_id in task_ids:
                task = notion.pages.retrieve(page_id=task_id)
                try:
                    task_title = task["properties"]["Name"]["title"][0]["text"]["content"]
                    curr_state[area_title][project_title].append(task_title)
                except Exception:
                    continue

    return curr_state


if os.path.exists("./current_state.json"):
    with open("./current_state.json", "r") as cs_file:
        lines = cs_file.readlines()
        curr_state = json.loads(''.join(lines))
else:
    curr_state = get_current_state()

tasks = """* Plan out dinner tonight, use up the tomato sauce
* Research mechanic
* Schedule oil change
* Plan out meals for the week
* Look into macros for meal planning"""

pprint(categorize_tasks(tasks, curr_state))
