import sys
from utils.loading_json_utils import get_apps, authentication_is_present
from utils.metadata_input import resolve_metadata_arg

def main():
    if (len(sys.argv) >= 3 and str(sys.argv[1]) == "get_apps"):
        print(get_apps(resolve_metadata_arg(sys.argv[2])))

    if (len(sys.argv) >= 3 and str(sys.argv[1]) == "get_auth"):
        print(authentication_is_present(resolve_metadata_arg(sys.argv[2])))

if __name__ == "__main__":
    main()