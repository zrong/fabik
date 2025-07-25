#!/usr/bin/env python3

from pathlib import Path
from fabik.conf import ConfigReplacer
import tomllib

def test_config():
    print("=== Testing Configuration Loading ===")
    
    # Load the actual fabik.toml
    with open('fabik.toml', 'rb') as f:
        conf = tomllib.load(f)
    
    print("Configuration loaded:")
    print(f"- NAME: {conf.get('NAME')}")
    print(f"- ENV exists: {'ENV' in conf}")
    print(f"- ENV type: {type(conf.get('ENV'))}")
    print(f"- FABRIC exists: {'FABRIC' in conf}")
    print(f"- FABRIC: {conf.get('FABRIC')}")
    
    # Test without environment
    print("\n=== Testing without environment ===")
    try:
        replacer = ConfigReplacer(conf, Path('.'), env_name=None)
        fabric_conf = replacer.get_tpl_value('FABRIC', merge=False)
        print(f"FABRIC conf (no env): {fabric_conf}")
        print(f"Type: {type(fabric_conf)}")
    except Exception as e:
        print(f"Error (no env): {e}")
    
    # Test with local environment
    print("\n=== Testing with local environment ===")
    try:
        replacer = ConfigReplacer(conf, Path('.'), env_name='local')
        fabric_conf = replacer.get_tpl_value('FABRIC', merge=False)
        print(f"FABRIC conf (local): {fabric_conf}")
        print(f"Type: {type(fabric_conf)}")
    except Exception as e:
        print(f"Error (local): {e}")

if __name__ == "__main__":
    test_config()