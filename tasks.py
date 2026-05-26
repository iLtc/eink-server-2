import requests
import os
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
from datetime import datetime
from pytz import timezone

load_dotenv()

timezone_pacific = timezone("US/Pacific")


def get_tasks():
    headers = {
        "CF-Access-Client-Id": os.getenv("CF_ACCESS_CLIENT_ID"),
        "CF-Access-Client-Secret": os.getenv("CF_ACCESS_CLIENT_SECRET")
    }
    response = requests.get(os.getenv("TASK_SERVER_URL"), headers=headers).json()
    tasks = [task for task in response if not task["completed"] and task["taskStatus"] != "Dropped"]

    inbox_tasks = [task for task in tasks if task["inInbox"]]
    overdue_tasks = [task for task in tasks if task["taskStatus"] == "Overdue"]
    duesoon_tasks = [task for task in tasks if task["taskStatus"] == "DueSoon"]

    overdue_tasks.sort(key=lambda x: x["dueDate"])
    duesoon_tasks.sort(key=lambda x: x["dueDate"])

    return inbox_tasks, overdue_tasks, duesoon_tasks


def draw_task_card(task, description=None, due_date=None, color="black", dark_background=False, center_text=False):
    card_width, card_height = 600, 40
    card = Image.new("RGB", (card_width, card_height), "white" if not dark_background else "purple")

    draw = ImageDraw.Draw(card)

    if center_text:
        # draw centered text
        font = ImageFont.truetype("./fonts/NotoSansSC-Regular.ttf", 25)
        text_bbox = draw.textbbox((0, 0), task, font=font)
        text_height = text_bbox[3] - text_bbox[1]
        text_width = text_bbox[2] - text_bbox[0]
        draw.text(((card_width - text_width) / 2, (card_height - text_height) / 2 - text_bbox[1]), task, fill="white" if dark_background else "black", font=font)

        return card

    if description:
        # draw description text
        font = ImageFont.truetype("./fonts/NotoSansSC-Regular.ttf", 15)
        description_bbox = draw.textbbox((0, 0), description, font=font)
        description_width = description_bbox[2] - description_bbox[0]
        description_height = description_bbox[3] - description_bbox[1]

        if due_date:
            draw.text((card_width - description_width, (card_height // 4 - description_height // 2) - description_bbox[1] - 1), description, fill=color, font=font)
        else:
            draw.text((card_width - description_width, (card_height // 2 - description_height // 2) - description_bbox[1] - 1), description, fill=color, font=font)

    else:
        description_width = 0

    if due_date:
        # draw due date text
        font = ImageFont.truetype("./fonts/NotoSansSC-Regular.ttf", 15)
        due_date_bbox = draw.textbbox((0, 0), due_date, font=font)
        due_date_width = due_date_bbox[2] - due_date_bbox[0]
        due_date_height = due_date_bbox[3] - due_date_bbox[1]

        if description:
            draw.text((card_width - due_date_width, (card_height // 4 * 3 - due_date_height // 2) - due_date_bbox[1] - 1), due_date, fill=color, font=font)
        else:
            draw.text((card_width - due_date_width, (card_height // 2 - due_date_height // 2) - due_date_bbox[1] - 1), due_date, fill=color, font=font)

    else:
        due_date_width = 0

    right_text_width = max(description_width, due_date_width)

    # draw task text
    font = ImageFont.truetype("./fonts/NotoSansSC-Regular.ttf", 25)
    task_original = task
    task = task_original

    while True:
        task_bbox = draw.textbbox((0, 0), task, font=font)
        task_width = task_bbox[2] - task_bbox[0]

        if task_width < card_width - right_text_width - 10:
            break

        task_original = task_original[:-1]
        task = task_original + "..."

    task_bbox = draw.textbbox((0, 0), task, font=font)
    task_height = task_bbox[3] - task_bbox[1]

    draw.text((0, (card_height - task_height) // 2 - task_bbox[1] - 1), task, fill=color, font=font)

    # draw separator line
    draw.line((0, card_height - 2, card_width, card_height - 2), fill="black", width=2)

    return card


def draw_tasks():
    inbox, overdue, duesoon = get_tasks()
    image_width, image_height = 600, 1080
    image = Image.new("RGB", (image_width, image_height), "white")

    title_image = draw_task_card("TASKS", dark_background=True, center_text=True)
    image.paste(title_image, (0, 0))

    y = 45

    for task in inbox:
        due_date = datetime.fromisoformat(task["dueDate"]).astimezone(timezone_pacific).strftime("%Y-%m-%d") if task["dueDate"] else None
        color = "black"

        if task["taskStatus"] == "Overdue":
            color = "red"
        elif task["taskStatus"] == "DueSoon":
            color = "orangered"

        task_image = draw_task_card(task["name"], "Inbox", due_date, color=color)
        image.paste(task_image, (0, y))
        y += 45

    for task in overdue + duesoon:
        description = task['containingProjectName'] if task["containingProjectName"] else None
        due_date = datetime.fromisoformat(task["dueDate"]).astimezone(timezone_pacific).strftime("%Y-%m-%d") if task["dueDate"] else None
        color = "black"

        if task["taskStatus"] == "Overdue":
            color = "red"
        elif task["taskStatus"] == "DueSoon":
            color = "orangered"

        task_image = draw_task_card(task["name"], description, due_date, color=color)
        image.paste(task_image, (0, y))
        y += 45

    return image


if __name__ == "__main__":
    image = draw_tasks()
    image.show()
