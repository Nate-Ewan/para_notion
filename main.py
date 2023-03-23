from dotenv import load_dotenv
from pprint import pprint
import notion_client as nc
import os

load_dotenv()

notion = nc.Client(auth=os.getenv("NOTION_TOKEN"))
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


def create_area_db(parent_id: str):
    properties = {
        "Name": {"title": {}},  # This is a required property
        "Description": {"rich_text": {}},
    }
    title = [{"type": "text", "text": {"content": "Areas"}}]
    parent = {"type": "page_id", "page_id": parent_id}

    return notion.databases.create(parent=parent, title=title, properties=properties)


def create_projects_db(area_db_id: str):
    pass
