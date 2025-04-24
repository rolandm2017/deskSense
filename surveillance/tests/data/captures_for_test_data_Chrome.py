from datetime import datetime

from surveillance.src.object.pydantic_dto import UtcDtTabChange

# NOTE: Originally, the TabChangeEvents were recorded *without* a timestamp.
# NOTE: BUT, they SHOULD have a timestamp!
# NOTE: So, I added one by hand.
# If this proves a problem, better data can be recorded.

# NOTE #2: i changed .strptime into .fromisoformat because it looks like it works better

chrome_data = [
    UtcDtTabChange(tabTitle='Google Docs', url='docs.google.com',
                            startTime=datetime.fromisoformat('2025-03-22 16:15:02-07:00')),
    UtcDtTabChange(tabTitle='ChatGPT', url='chatgpt.com',
                            startTime=datetime.fromisoformat('2025-03-22 16:15:10-07:00')),
    UtcDtTabChange(tabTitle='Claude', url='claude.ai',
                            startTime=datetime.fromisoformat('2025-03-22 16:15:21-07:00')),
    UtcDtTabChange(tabTitle='ChatGPT', url='chatgpt.com',
                            startTime=datetime.fromisoformat('2025-03-22 16:15:30-07:00'))
    # Commented out below entries because, because the tests were too long
    # TabChangeEvent(tabTitle='Google', url='www.google.com',
    #                startTime=datetime.strptime('2025-03-22 23:15:39', '%Y-%m-%d %H:%M:%S')),
    # TabChangeEvent(tabTitle='YouTube', url='www.youtube.com',
    #                startTime=datetime.strptime('2025-03-22 23:16:27', '%Y-%m-%d %H:%M:%S')),
    # TabChangeEvent(tabTitle='X. It’s what’s happening / X', url='x.com',
    #                startTime=datetime.strptime('2025-03-22 23:16:37', '%Y-%m-%d %H:%M:%S')),
    # TabChangeEvent(tabTitle='Google Docs', url='docs.google.com',
    #                startTime=datetime.strptime('2025-03-22 23:16:50', '%Y-%m-%d %H:%M:%S')),
    # TabChangeEvent(tabTitle='ChatGPT', url='chatgpt.com',
    #                startTime=datetime.strptime(
    #     '2025-03-22 23:17:21', '%Y-%m-%d %H:%M:%S'))
]
