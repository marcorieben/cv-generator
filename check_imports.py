try:
    import streamlit
    print("streamlit: OK")
except ImportError as e:
    print(f"streamlit: FAIL {e}")

try:
    import streamlit_authenticator
    print("streamlit_authenticator: OK")
except ImportError as e:
    print(f"streamlit_authenticator: FAIL {e}")

try:
    import yaml
    print("yaml: OK")
except ImportError as e:
    print(f"yaml: FAIL {e}")
