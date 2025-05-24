// In content script
export function runNeedToRefreshChecker() {
    setInterval(() => {
        chrome.runtime.sendMessage({ type: "heartbeat" }, (response) => {
            if (chrome.runtime.lastError) {
                // Extension context is dead - can't communicate anymore

                // Option 1: Ask user
                if (
                    confirm(
                        "Extension updated. Reload page to get latest version?"
                    )
                ) {
                    location.reload();
                }

                // Option 2: Just auto-reload (less intrusive for development)
                // location.reload();

                // Option 3: Show a banner instead of blocking popup
                // showReloadBanner();
            }
        });
    }, 5000);
}
