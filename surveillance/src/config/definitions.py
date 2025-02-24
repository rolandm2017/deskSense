MAX_QUEUE_LENGTH = 40

# Define productive applications
productive_apps = ['Chrome', "Google Chrome", 'File Explorer',  # Chrome determined by window title
                   'Postman', 'Terminal', 'Visual Studio Code']

# TODO: allow user to mark certain servers "productive" i.e. Slack analogues
# mostly a temp holder for later exploration by channel
unproductive_apps = ["Discord"]

productive_categories = {
    'File Explorer': True,
    'Google Chrome': None,  # Will be determined by window title
    'Mozilla Firefox': None,  # Will be determined by window title
    'Alt-tab window': None,  # Determined by destination of the alt-tab.
    'Postman': True,
    'Terminal': True,
    'Visual Studio Code': True
}

# Productive website patterns (for Chrome)
productive_sites = [
    'github.com',
    'stackoverflow.com',
    'docs.',
    'jira.',
    'confluence.',
    'claude.ai',
    'chatgpt.com',
    'www.google.com',
    'localhost',
    'extensions'
]


social_media = ['www.facebook.com', 'www.tiktok.com', 'x.com', ]

misc_sites = ['newtab', 'chatgpt.com']
