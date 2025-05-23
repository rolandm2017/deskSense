import platform


class OperatingSystemInfo:
    def __init__(self):
        self.is_windows = None
        self.is_ubuntu = None
        self.current_os = self.get_os_info()
        if self.current_os.startswith("Windows"):
            self.is_windows = True
            self.is_ubuntu = False
        else:
            self.is_windows = False
            self.is_ubuntu = True

    def get_os_info(self):
        system = platform.system()
        if system == "Windows":
            # For Windows, we can get the specific version
            version = platform.win32_ver()[0]
            if version == "11":
                return "Windows 11"
            else:
                return f"Windows {version}"
        elif system == "Linux":
            # Cannot import Distro on Windows machines so must import it here
            import distro

            # For Linux, we can get the distribution details
            try:
                # This works for most Linux distributions
                distro_name = distro.id().lower()
                if "ubuntu" in distro_name:
                    return f"Ubuntu {distro.version()}"
                return f"Linux ({distro.name()} {distro.version()})"

            except:
                # Fallback for newer Python versions where linux_distribution() is removed
                try:
                    return f"Linux ({distro.name()} {distro.version()})"
                except ImportError:
                    return "Linux (distribution unknown)"
        return system


# Usage
sys_info = OperatingSystemInfo()
print(f"Current operating system: {sys_info.current_os}")

# # You can also do specific checks
# if platform.system() == "Windows" and platform.win32_ver()[0] == "11":
#     print("This is Windows 11")
# elif platform.system() == "Linux":
#     print("This is Linux")
