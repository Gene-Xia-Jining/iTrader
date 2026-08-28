"""Test script for client-side token functionality."""
import asyncio
from token_manager import TokenManager


async def test_token_flow():
    """Test the complete token flow."""
    server_url = "http://localhost:8000"
    
    # Create token manager
    token_manager = TokenManager(server_url)
    
    print("Testing token management...")
    print(f"Client ID: {token_manager.client_id}")
    
    # Check if we have a token
    if token_manager.have_token():
        print("✅ Found existing token")
        token = token_manager.load_token()
        print(f"Token: {token}")
        
        # Validate it
        valid = await token_manager.validate_token(token)
        if valid:
            print("✅ Token is valid")
        else:
            print("❌ Token is invalid, requesting new one...")
            token = await token_manager.request_new_token("Replacement token")
    else:
        print("❌ No token found, requesting new one...")
        token = await token_manager.request_new_token("Initial token")
    
    # Test authentication headers
    headers = token_manager.get_auth_headers()
    print(f"\nAuth headers: {headers}")
    
    # List tokens
    try:
        tokens = await token_manager.list_tokens()
        print(f"\nAvailable tokens: {len(tokens.get('tokens', []))}")
        for token_info in tokens.get('tokens', []):
            print(f"  - {token_info['description']} (uses: {token_info['use_count']})")
    except Exception as e:
        print(f"❌ Failed to list tokens: {e}")


async def main():
    """Run all tests."""
    print("Testing client token functionality...\n")
    await test_token_flow()


if __name__ == "__main__":
    asyncio.run(main())