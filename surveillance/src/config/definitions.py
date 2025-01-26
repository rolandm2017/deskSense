MAX_QUEUE_LENGTH = 40

# Define productive applications
productive_apps = ['Chrome', 'Discord', 'File Explorer', 'Google Chrome',
                   'Postman', 'Terminal', 'Visual Studio Code']

# TODO: allow user to mark certain servers "productive" i.e. Slack analogues
# mostly a temp holder for later exploration by channel
unproductive_apps = ["Discord"]

productive_categories = {
    'File Explorer': True,
    'Google Chrome': None,  # Will be determined by window title
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
    'chatgpt.com'
]

productive_sites_2 = ['claude.ai', 'extensions',
                      'stackoverflow.com', 'www.google.com', 'localhost']

social_media = ['www.facebook.com', 'www.tiktok.com', 'x.com', ]

misc_sites = ['newtab', 'chatgpt.com']
