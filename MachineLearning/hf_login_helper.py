"""
HuggingFace Login Helper
========================

Simple script to authenticate with HuggingFace Hub in the virtual environment.
"""

import sys
from huggingface_hub import login, whoami

def main():
    print("=" * 60)
    print("HUGGINGFACE LOGIN HELPER")
    print("=" * 60)
    print()
    print("To get your token:")
    print("1. Go to: https://huggingface.co/settings/tokens")
    print("2. Create a new token (type: Read)")
    print("3. Copy the token (starts with 'hf_')")
    print()

    # Check if already logged in
    try:
        user_info = whoami()
        print(f"[OK] Already logged in as: {user_info['name']}")
        print(f"Token type: {user_info.get('auth', {}).get('type', 'unknown')}")
        print()

        response = input("Do you want to login with a different token? (y/N): ").strip().lower()
        if response != 'y':
            print("\n[INFO] Keeping existing login")
            return
        print()
    except Exception:
        print("[INFO] Not logged in yet")
        print()

    # Get token from user
    print("Enter your HuggingFace token:")
    print("(Paste with Ctrl+V and press Enter)")
    token = input().strip()

    if not token:
        print("\n[FAIL] No token provided")
        sys.exit(1)

    if not token.startswith('hf_'):
        print("\n[WARN] Token should start with 'hf_'")
        response = input("Continue anyway? (y/N): ").strip().lower()
        if response != 'y':
            print("[INFO] Login cancelled")
            sys.exit(0)

    # Attempt login
    print("\n[INFO] Logging in...")
    try:
        login(token=token, add_to_git_credential=True)
        print("[OK] Login successful!")

        # Verify
        user_info = whoami()
        print(f"[OK] Logged in as: {user_info['name']}")
        print(f"[OK] Token saved to: ~/.cache/huggingface/token")
        print()
        print("=" * 60)
        print("You can now use The Stack dataset:")
        print("  python main.py --download-stack --stack-languages python --stack-count 500")
        print("=" * 60)

    except Exception as e:
        print(f"\n[FAIL] Login failed: {e}")
        print()
        print("Common issues:")
        print("- Token is invalid or expired")
        print("- Token doesn't have correct permissions")
        print("- Network connectivity issues")
        print()
        print("Try creating a new token at:")
        print("  https://huggingface.co/settings/tokens")
        sys.exit(1)


if __name__ == '__main__':
    main()
