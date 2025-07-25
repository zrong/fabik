#!/usr/bin/env python3

from pathlib import Path
from fabik.cmd import global_state
from fabik.deploy.gunicorn import GunicornDeploy

def test_server_connection():
    print("=== Testing Server Connection Setup ===")
    
    # Set up the global state like the CLI would
    global_state.env = 'local'
    global_state.cwd = Path('/Users/zrong/storage/zrong/fabik')
    global_state.conf_file = Path('/Users/zrong/storage/zrong/fabik/fabik.toml')
    
    print(f"env: {global_state.env}")
    print(f"cwd: {global_state.cwd}")
    print(f"conf_file: {global_state.conf_file}")
    
    # Test configuration loading
    print("\n=== Loading Configuration ===")
    try:
        conf_data = global_state.load_conf_data(check=True)
        print(f"Configuration loaded successfully")
        print(f"conf_data type: {type(conf_data)}")
        print(f"conf_data keys: {list(conf_data.keys()) if isinstance(conf_data, dict) else 'Not a dict'}")
        print(f"FABRIC in conf_data: {'FABRIC' in conf_data if isinstance(conf_data, dict) else 'Not a dict'}")
        
        if isinstance(conf_data, dict):
            print(f"FABRIC config: {conf_data.get('FABRIC')}")
    except Exception as e:
        print(f"Error loading configuration: {e}")
        return
    
    # Test build_deploy_conn
    print("\n=== Testing build_deploy_conn ===")
    try:
        deploy = global_state.build_deploy_conn(GunicornDeploy)
        print("build_deploy_conn succeeded")
        print(f"deploy type: {type(deploy)}")
    except Exception as e:
        print(f"Error in build_deploy_conn: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_server_connection()