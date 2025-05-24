import requests
from requests.auth import HTTPBasicAuth


def test_vlc_connection():
    """
    Simple test to see if VLC HTTP interface is responding
    """
    url = "http://localhost:8080/requests/status.json"

    # Test without auth first
    print("Testing without authentication...")
    try:
        response = requests.get(url, timeout=5)
        print(f"Status code: {response.status_code}")
        if response.status_code == 401:
            print("✓ VLC is running but requires authentication")
        elif response.status_code == 200:
            print("✓ VLC is running and no auth required")
        else:
            print(f"Unexpected status code: {response.status_code}")
    except requests.exceptions.ConnectionError:
        print("✗ Cannot connect to VLC - HTTP interface not running")
        return False
    except requests.exceptions.Timeout:
        print("✗ Connection timeout")
        return False

    # Test with auth
    print("\nTesting with authentication...")
    auth = HTTPBasicAuth("", "vlcpass")  # Replace with your actual password
    try:
        response = requests.get(url, auth=auth, timeout=5)
        print(f"Status code: {response.status_code}")
        if response.status_code == 200:
            print("✓ Authentication successful!")
            data = response.json()
            print(f"VLC State: {data.get('state', 'unknown')}")
            return True
        elif response.status_code == 401:
            print("✗ Authentication failed - check your password")
        else:
            print(f"Unexpected status code: {response.status_code}")
    except Exception as e:
        print(f"Error: {e}")

    return False


if __name__ == "__main__":
    test_vlc_connection()
