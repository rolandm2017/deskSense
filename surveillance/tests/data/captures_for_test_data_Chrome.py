from datetime import datetime

from src.object.pydantic_dto import TabChangeEvent

chrome_data = [
    TabChangeEvent(tabTitle='Google Docs', url='docs.google.com',
                   startTime=datetime.strptime('2025-03-22 23:15:02', '%Y-%m-%d %H:%M:%S')),
    TabChangeEvent(tabTitle='ChatGPT', url='chatgpt.com', startTime=datetime.strptime(
        '2025-03-22 23:15:10', '%Y-%m-%d %H:%M:%S')),
    TabChangeEvent(tabTitle='Claude', url='claude.ai', startTime=datetime.strptime(
        '2025-03-22 23:15:21', '%Y-%m-%d %H:%M:%S')),
    TabChangeEvent(tabTitle='ChatGPT', url='chatgpt.com', startTime=datetime.strptime(
        '2025-03-22 23:15:30', '%Y-%m-%d %H:%M:%S')),
    TabChangeEvent(tabTitle='Google', url='www.google.com', startTime=datetime.strptime(
        '2025-03-22 23:15:39', '%Y-%m-%d %H:%M:%S')),
    TabChangeEvent(tabTitle='YouTube', url='www.youtube.com',
                   startTime=datetime.strptime('2025-03-22 23:16:27', '%Y-%m-%d %H:%M:%S')),
    TabChangeEvent(tabTitle='X. It’s what’s happening / X', url='x.com',
                   startTime=datetime.strptime('2025-03-22 23:16:37', '%Y-%m-%d %H:%M:%S')),
    TabChangeEvent(tabTitle='Google Docs', url='docs.google.com',
                   startTime=datetime.strptime('2025-03-22 23:16:50', '%Y-%m-%d %H:%M:%S')),
    TabChangeEvent(tabTitle='ChatGPT', url='chatgpt.com', startTime=datetime.strptime(
        '2025-03-22 23:17:21', '%Y-%m-%d %H:%M:%S'))
]
