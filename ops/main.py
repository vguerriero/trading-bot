from ops.secret_loader import load_secrets
load_secrets()          # pulls into environment before anything else

def main():
    print("Trading‑bot framework online!")

if __name__ == "__main__":
    main()