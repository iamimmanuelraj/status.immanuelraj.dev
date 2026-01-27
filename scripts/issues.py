import os, yaml, telegram, sys, asyncio
from html import escape


async def send_tg_message(text):
    tg_bot = telegram.Bot(os.getenv("TELEGRAM_TOKEN"))
    for chat_id in os.getenv("TELEGRAM_CHAT_ID").split(";"):
        await tg_bot.send_message(chat_id, text, "HTML")

def get_issue_name(issue):
    """Extract the name from an issue (dict or string)."""
    return issue["name"] if isinstance(issue, dict) else issue


def report_issue():
    # Format each service with its URL as a hyperlink
    services_list = []
    for issue in issues:
        if isinstance(issue, dict):
            # Format as HTML link for Telegram (with HTML escaping for security)
            safe_url = escape(issue["url"])
            safe_name = escape(issue["name"])
            services_list.append('<a href="{}">{}</a>'.format(safe_url, safe_name))
        else:
            # Fallback for old format (just name)
            services_list.append(escape(issue))
    
    text = (
        "<b>Service outage detected!</b>\n\n"
        + "One or more below mentioned service(s) did not respond correctly to the CI ping:\n\n{}\n\n@iamimmanuelraj".format(
            "\n".join(services_list)
        )
    )
    print("Service outage detected: " + ", ".join([get_issue_name(issue) for issue in issues]))
    asyncio.run(send_tg_message(text))


def report_restored():
    # Format each service with its URL as a hyperlink
    services_list = []
    for service in restored_services:
        if isinstance(service, dict):
            # Format as HTML link for Telegram (with HTML escaping for security)
            safe_url = escape(service["url"])
            safe_name = escape(service["name"])
            services_list.append('<a href="{}">{}</a>'.format(safe_url, safe_name))
        else:
            # Fallback for old format (just name)
            services_list.append(escape(service))
    
    if len(restored_services) == 1:
        text = (
            "<b>Service restored!</b>\n\n"
            + "The following service is working normally:\n\n{}\n\n@iamimmanuelraj".format(
                "\n".join(services_list)
            )
        )
        print("Service restored: " + ", ".join([get_issue_name(service) for service in restored_services]))
    else:
        text = (
            "<b>Services restored!</b>\n\n"
            + "The following services are working normally:\n\n{}\n\n@iamimmanuelraj".format(
                "\n".join(services_list)
            )
        )
        print("Services restored: " + ", ".join([get_issue_name(service) for service in restored_services]))
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
