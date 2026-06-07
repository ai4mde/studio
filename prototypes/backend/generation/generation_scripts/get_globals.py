import sys
from utils.loading_json_utils import get_apps, authentication_is_present

def main():
    if len(sys.argv) < 3:
        return
    
    command = sys.argv[1]
    metadata_path = sys.argv[2]

    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = f.read()

    if command == "get_apps":
        print(get_apps(metadata))

    if command == "get_auth":
        print(authentication_is_present(metadata))

if __name__ == "__main__":
    main()