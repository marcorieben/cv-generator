import streamlit_authenticator as stauth
import sys

def generate_hash(password):
    return stauth.Hasher().hash(password)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        password = sys.argv[1]
        print(f"Password: {password}")
        print(f"Hash: {generate_hash(password)}")
    else:
        print("Usage: python generate_keys.py <password>")
        print("Or enter password below:")
        password = input("Password: ")
        print(f"Hash: {generate_hash(password)}")
