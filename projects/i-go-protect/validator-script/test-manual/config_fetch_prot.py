import argparse
import configparser
from pathlib import Path


if __name__ == '__main__':

    repo_link = 'https://github.com'
    parser = argparse.ArgumentParser(description=f"IgoProtec validator script. For a guide, see {repo_link}.")
    parser.add_argument(
        '--path', type=str, help='Path to the config file', 
        required=False, default=Path( Path(__file__).parent, 'default.config' )
    )
    args = parser.parse_args()

    config_path = Path(args.path)
    config = configparser.RawConfigParser(defaults=None, strict=False, allow_no_value=True)
    config.read(config_path)
    
    validator_ad_id = str(config.get('i_go_protect_config', 'validator_ad_id'))
    manager_mnemonic = str(config.get('i_go_protect_config', 'manager_mnemonic'))
    noticeboard_id = str(config.get('i_go_protect_config', 'noticeboard_id'))

    sleep_time_s = int(config.get('node_config', 'sleep_time_s'))
