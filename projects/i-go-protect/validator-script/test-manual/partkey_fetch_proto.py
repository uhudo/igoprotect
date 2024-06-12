"""
Module containing the class and helper functions for reading participation keys.

"""
import logging
import subprocess

import numpy as np
import pandas as pd


def run_command_and_wait_for_output(command_args):
    """Run a command in the command line, wait for its output, and capture the output.

    Parameters
    ----------
    command_args: list
        Strings of individual words that make up the command.

    Returns
    -------
    bool, str
        Command validity (execution successful = 0) and the captured STDOUT.

    """
    command_validity = False
    result = None
    try:
        result = subprocess.run(command_args, capture_output=True, text=True)
        if result.returncode == 0:
            command_validity = True
        elif result.returncode < 0:
            logging.warning(f"`{' '.join(command_args)}` returned code {result.returncode} and {result.stdout}.")
        else:
            logging.warning(f"`{' '.join(command_args)}` returned error `{result.stderr}`.")
    except OSError as e:
        logging.warning(f"Calling `{' '.join(command_args)}` raised error {e}.")
    return command_validity, result.stdout


class PartkeyFetcher(object):

    COMMAND_LIST = ["algokit", "goal", "account", "listpartkeys"]

    COMMAND_INFO = ["algokit", "goal", "account", "partkeyinfo"]

    COLUMNS = dict(
        participation_id='Participation ID',
        parent_address='Parent address',
        last_vote_round='Last vote round',
        last_block_proposal_round='Last block proposal round',
        effective_first_round='Effective first round',
        effective_last_round='Effective last round',
        first_round='First round',
        last_round='Last round',
        key_dilution='Key dilution',
        selection_key='Selection key',
        voting_key='Voting key',
        state_proof_key='State proof key'
    )


    def __init__(self):
        pass


    def get_partkey_table(self):
        """Get the participation keys.

        Notes
        -----
        Issues blocking system calls to `algokit` in order to fetch the participation key information.

        Returns
        -------
        DataFrame or None

        """
        list_cmd_validity, list_cmd_result = run_command_and_wait_for_output(
            self.COMMAND_LIST
        )
        info_cmd_validity, info_cmd_result = run_command_and_wait_for_output(
            self.COMMAND_INFO
        )
        if list_cmd_validity and info_cmd_validity:
            # Keep the worker function separate for easier testing
            return self._get_partkey_table_from_stdout(self, list_cmd_result, info_cmd_result)
        else:
            return None


    def _get_partkey_table_from_stdout(self, list_cmd_result, info_cmd_result):
        """Get the participation keys from the `partkeyinfo` STDOUT.

        Parameters
        ----------
        list_cmd_result: str
            STDOUT from calling `listpartkeys`.
        info_cmd_result: str
            STDOUT from calling `partkeyinfo`.

        Returns
        -------
        DataFrame or None

        """
        # Get a reference number of keys for verifying master the output's validity
        num_of_keys = len(list_cmd_result.split('\n')) - 2  # Subtract header row and trailing new line
        partkey_list_raw = self._filter_partkeys_from_stdout(info_cmd_result)
        if len(partkey_list_raw) != num_of_keys:
            logging.warning(
                f'Number of keys from list {num_of_keys} and info {len(partkey_list_raw)} command do not match.'
            )
            return None
        partkey_table = self._convert_partkey_list_raw_to_table(partkey_list_raw)
        return partkey_table


    def _filter_partkeys_from_stdout(self, info_cmd_result):
        """Generate a list, containing a nested list of lines associated with an individual partkey.

        Parameters
        ----------
        info_cmd_result: str
            STDOUT from calling `partkeyinfo`.

        Returns
        -------
        list or None

        """
        # Convert string to list
        res = info_cmd_result.split('\n')[1:]  # Drop header

        # Get the start/end line indexes, separating individual partkeys
        delimiter_idx = np.array([], dtype=int)
        for i, r in enumerate(res):
            if r == ' ':
                delimiter_idx = np.r_[delimiter_idx, i]
        delimiter_idx = np.r_[delimiter_idx, len(res)-1]

        # Group the lines of a partkey
        partkey_list_raw = []
        for i in range(delimiter_idx.size - 1):
            start_idx = delimiter_idx[i] + 1
            end_idx = delimiter_idx[i + 1]
            partkey_list_raw.append(res[start_idx:end_idx])

        if self._check_partkey_list_raw_format_validity(partkey_list_raw):
            return partkey_list_raw
        else:
            logging.warning('Partkey format does not seem valid.')
            return None


    def _check_partkey_list_raw_format_validity(self, partkey_list_raw):
        """Check the number of lines and the names (and order) of the partkey data, obtained via STDOUT.

        Parameters
        ----------
        partkey_list_raw: list
            Nested list of lines associated with an individual partkey

        Returns
        -------
        bool

        """
        for partkey in partkey_list_raw:
            if len(partkey) != 12:
                return False
            for line, col_val in zip(partkey, self.COLUMNS.values()):
                if line[1:len(col_val)+1] != col_val:
                    return False
        return True


    def _convert_partkey_list_raw_to_table(self, partkey_list_raw):
        """Convert the nested list of partkey info to a table.

        Parameters
        ----------
        partkey_list_raw: list
            Nested list of lines associated with an individual partkey

        Returns
        -------
        DataFrame

        """
        partkey_table = pd.DataFrame(columns=(self.COLUMNS), index=[*range(len(partkey_list_raw))])
        for i, partkey in enumerate(partkey_list_raw):
            # df = pd.DataFrame(columns=list(self.COLUMNS), index=[i])
            for line in partkey:
                key, value = line.split(':')
                key = key.strip()   # Remove leading (and trailing spaces)
                value = value.strip()   # Remove leading (and trailing spaces)
                column = list(self.COLUMNS.keys())[np.squeeze(np.where( np.array(list(self.COLUMNS.values())) == key ))]
                partkey_table.loc[i, column] = value
            # partkey_table = pd.concat([partkey_table, df])
        return partkey_table


if __name__ == "__main__":

    logging.basicConfig( level=logging.DEBUG )

    ### Initialize
    pf = PartkeyFetcher()

    ### Test by running STDOUT
    partkey_table = pf.get_partkey_table()

    ### Test using imported STDOUT
    # list_cmd_result = []
    # with open('input/input_windows_list.txt') as f:
    #     for line in f.readlines():
    #         list_cmd_result.append(line)
    # list_cmd_result = ''.join(list_cmd_result)
    # info_cmd_result = []
    # with open('input/input_windows_info.txt') as f:
    #     for line in f.readlines():
    #         info_cmd_result.append(line)
    # info_cmd_result = ''.join(info_cmd_result)
    # partkey_table = pf._get_partkey_table_from_stdout(list_cmd_result, info_cmd_result)
    # partkey_table.to_csv('output/partkey_list.csv', index=False)

    # if partkey_table is not None:
    #     partkey_table.to_csv('output/partkey_list.csv', index=False)
