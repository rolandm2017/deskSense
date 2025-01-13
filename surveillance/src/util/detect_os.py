import platform

def get_os_info():
    system = platform.system()
    if system == "Windows":
        # For Windows, we can get the specific version
        version = platform.win32_ver()[0]
        if version == "11":
            return "Windows 11"
        else:
            return f"Windows {version}"
    elif system == "Linux":
        # For Linux, we can get the distribution details
        try:
            # This works for most Linux distributions
            distro = platform.linux_distribution()[0].lower()
            if "ubuntu" in distro:
                return f"Ubuntu {platform.linux_distribution()[1]}"
            return f"Linux ({distro})"
        except:
            # Fallback for newer Python versions where linux_distribution() is removed
            try:
                import distro
                return f"Linux ({distro.name()} {distro.version()})"
            except ImportError:
                return "Linux (distribution unknown)"
    return system

# Usage
current_os = get_os_info()
print(f"Current operating system: {current_os}")

# You can also do specific checks
if platform.system() == "Windows" and platform.win32_ver()[0] == "11":
    print("This is Windows 11")
elif platform.system() == "Linux":
    print("This is Linux")