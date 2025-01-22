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
