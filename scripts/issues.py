import os, yaml, telegram, sys, asyncio


async def send_tg_message(text):
    tg_bot = telegram.Bot(os.getenv("TELEGRAM_TOKEN"))
    for chat_id in os.getenv("TELEGRAM_CHAT_ID").split(";"):
        await tg_bot.send_message(chat_id, text, "HTML")

def report_issue():
    # Format each service with its URL as a hyperlink
    services_list = []
    for issue in issues:
        if isinstance(issue, dict):
            # Format as HTML link for Telegram
            services_list.append('<a href="{}">{}</a>'.format(issue["url"], issue["name"]))
        else:
            # Fallback for old format (just name)
            services_list.append(issue)
    
    text = (
        "<b>Service outage detected!</b>\n\n"
        + "One or more below mentioned service(s) did not respond correctly to the CI ping:\n\n{}\n\n@iamimmanuelraj".format(
            "\n".join(services_list)
        )
    )
    print("Service outage detected: " + ", ".join([issue["name"] if isinstance(issue, dict) else issue for issue in issues]))
    asyncio.run(send_tg_message(text))


def report_restored():
    if len(restored_services) == 1:
        text = (
            "<b>Service restored!</b>\n\n"
            + "The following service is working normally: <b>{}</b>\n\n@iamimmanuelraj".format(
                ", ".join(restored_services)
            )
        )
        print("Service restored: " + ", ".join(restored_services))
    else:
        text = (
            "<b>Services restored!</b>\n\n"
            + "The following services are working normally: <b>{}</b>\n\n@iamimmanuelraj".format(
                ", ".join(restored_services)
            )
        )
        print("Services restored: " + ", ".join(restored_services))
    asyncio.run(send_tg_message(text))


with open("_data/issues.yml") as f:
    issues = yaml.load(f, Loader=yaml.FullLoader)
if len(issues) > 0:
    report_issue()


with open("_data/restored.yml") as f:
    restored_services = yaml.load(f, Loader=yaml.FullLoader)
if len(restored_services) > 0:
    report_restored()

os.remove("_data/issues.yml")
os.remove("_data/restored.yml")
sys.exit(0)
