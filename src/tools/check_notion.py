from dotenv import load_dotenv

load_dotenv()

import os

from notion_client import Client

notion = Client(auth=os.environ["NOTION_API_KEY"])

result = notion.search()

for item in result["results"]:
    # if item["object"] != "page":
    #    continue
    parent_type = item.get("parent", {}).get("type")
    title = "제목없음"
    for prop in item.get("properties", {}).values():
        if prop.get("type") == "title" and prop["title"]:
            title = prop["title"][0]["plain_text"]
            break
    print(f"{item['object']}    {item['id']}    [{parent_type}] {title}")
