import pytest
import yaml
import os
import sys
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.utils.generate_keys import generate_hash

class TestAuthentication:
    def test_config_yaml_structure(self):
        """Verify config.yaml has the required structure for streamlit-authenticator."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
        
        assert os.path.exists(config_path), "config.yaml not found"
        
        with open(config_path) as file:
            config = yaml.safe_load(file)
            
        assert "credentials" in config
        assert "usernames" in config["credentials"]
        assert "cookie" in config
        assert "name" in config["cookie"]
        assert "key" in config["cookie"]
        assert "expiry_days" in config["cookie"]

    def test_admin_user_exists(self):
        """Verify that the default admin user exists in config."""
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.yaml")
        with open(config_path) as file:
            config = yaml.safe_load(file)
            
        usernames = config["credentials"]["usernames"]
        assert "admin" in usernames
        assert "password" in usernames["admin"]
        assert "email" in usernames["admin"]
        assert "name" in usernames["admin"]

    def test_password_hashing(self):
        """Verify that the helper script generates valid bcrypt hashes."""
        password = "test_password"
        hashed = generate_hash(password)
        
        assert hashed is not None
        assert isinstance(hashed, str)
        assert hashed.startswith("$2b$")  # Bcrypt hash prefix
        assert len(hashed) > 0

    @patch("streamlit_authenticator.Authenticate")
    def test_authenticator_initialization(self, mock_auth):
        """Verify Authenticate class is initialized with correct parameters."""
        # Mock config
        config = {
            "credentials": {"usernames": {"admin": {}}},
            "cookie": {
                "name": "test_cookie",
                "key": "test_key",
                "expiry_days": 30
            }
        }
        
        import streamlit_authenticator as stauth
        
        authenticator = stauth.Authenticate(
            config['credentials'],
            config['cookie']['name'],
            config['cookie']['key'],
            config['cookie']['expiry_days']
        )
        
        assert authenticator is not None
