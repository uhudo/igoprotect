# Validator script

Validator script for monitoring subscribed delegators and generating/depositing keys, issuing breach warnings, and terminating contracts.

## Usage instructions

The validator script can be either used by cloning the full IgoProtect project or installed as a standalone package. Both approaches are described below together with the prerequisites.

### Prerequisites

The script requires a file with configuration instrucitons. During operation, the script will output runtime information to a log file.

#### Configuration input

Configuration instructions are provided to the script through a config file. An example of the config file is provided in [default.config](default.config). The config file needs to include:

- The ID of the validator advertisement.
- The manager's mnemonic.
- A flag indicating whether to use the `goal` command with `algokit` or standalone.
- The period at which the validator script is executed.

#### Log output

The script outputs information to a log file. Similar to the config file, the log file can be generated anywhere on the system. The log includes information such as:

- The number of delegators, associated with the validator and their state.
- Delegator contract state changes (e.g., participation keys generation).
- Miscellaneous validator script status information.

### Usage through the IgoProtect project

Validator script usage through the IgoProtect project entails using the project's existing virtual environment. That is, the environment used for generating and testing the smart contracts. The simplest setup, where the configuration and log files are placed in the project's `validator-script` directory, is described below.

#### Setup

- Annotate the file `<your-path>/validator-script/default.config` to match the configuration of your system.
- (optinoal) Clear any existing logs in `<your-path>/validator-script/validator_script.log`.

### Run

Activate the virtual environment and run the command `python validator-script/validator_script.py` (in the command line or an IDE, from the project's base direcory). This will automatically point the script to the aforementioned configuration and log files.

Alternativelly, one can point the validator script to a configuration and log file elsewhere on the system using the following arguments (appended to `python validator-script/validator_script.py `):

- `--config_path <some/path/to/config_file>`
- `--log_path <some/path/to/log_file>`

### Usage as an independent package

The validator script can be installed as a <a href="igoprotect_validator_script-0.0.1-py3-none-any.whl" download>standalone module</a> using the provided `.whl` file.

#### Setup

- (If working with a virtual environment) [Initialize and activate](https://docs.python.org/3/library/venv.html) the virtual environment.
- Install the <a href="igoprotect_validator_script-0.0.1-py3-none-any.whl" download>standalone module</a> using the provided wheel `python -m pip install <your-path>/validator-script/igoprotect_validator_script-0.0.1-py3-none-any.whl`

The above setup will automatically try to install the required dependencies.

#### Run

Using the same environment, run `python -c "from igoprotect_validator_script import run_validator; run_validator('<config_path>', '<log_path>')"`, where `<config_path>` points to the configuration file and `<log_path>` to the log file.

Alternatively, arguments `<config_path>` and `<log_path>` can be omitted. The validator script will then look for a `default.config` configuration file in the current working directory. Moreover, the script shall generate a `validator_script.log` file in the same directory.

The validator script can be run in the background by encapsulating the above command in `(&>/dev/null <python ...> &)`, where `<python ...>` should be substituted by the command.

## Build

- (if applicable) Set up and activate a virtual environment.
- Install `requirements.txt`, for example, using `pip -r requirements.txt`
- Run `python -m build`

### Notes on the dependencies

The dependencies for setting up a virtual environment, that will be used for both running the script and for building it are stored in `requrirements.txt`.
The dependencies required only for the `igoprotect_validator_script` module are listed in `pyproject.toml`.

## Outlook

### Resilience

A node might undergo a reboot due to undergoing maintenance or suffering from a power loss, among others reasons. A restart of the node currently terminates the validator script. Therefore, an upcoming improvement is to increase the validator script's resilience, ensuring its continuous execution.

### Node runner training

One of the main motivation factors for this project is increasing the amount of online stake. A key enabler is a sufficient number of node runners. To this end, a tutorial on running a node, its significance for Algorand, and the available rewards, could help increase the number of trained node runners.
