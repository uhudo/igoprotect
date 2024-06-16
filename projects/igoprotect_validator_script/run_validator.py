from pathlib import Path
import argparse

from src.igoprotect_validator_script import run_validator


if __name__ == '__main__':

    repo_link = 'https://github.com'
    parser = argparse.ArgumentParser(description=f"IgoProtec validator script. For a guide, see {repo_link}.")
    parser.add_argument(
        '--config_path', type=str, help='Path to the config file',
        required=False, default=Path(Path(__file__).parent, 'default.config')
    )
    parser.add_argument(
        '--log_path', type=str, help='Path to the log file',
        required=False, default=Path(Path(__file__).parent, 'validator_script.log')
    )
    args = parser.parse_args()

    run_validator(args.config_path, args.log_path)
