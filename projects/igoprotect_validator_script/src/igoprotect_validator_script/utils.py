import struct
from typing import List

from algosdk.v2client import algod
from algosdk.abi import TupleType, UintType

from .GeneralValidatorAdClient import GeneralValidatorAdClient
from .DelegatorContractClient import DelegatorContractClient, ValConfigMan



def decode_uint64_list(
    data: bytes
) -> list:
    """Decode a string of bytes.

    Args:
        data (bytes): String of bytes.

    Returns:
        list: Decoded bytes.

    """
    # Determine the number of uint64 values in the bytes object
    num_uint64 = len(data) // 8

    # Unpack the bytes object into a list of uint64 values (big-endian)
    int_list = list(struct.unpack(f">{num_uint64}Q", data))

    return int_list



def get_del_id_list(
    algod_client: algod.AlgodClient,
    validator_ad_app_id: int,
) -> List[int]:
    """Get a list of Delegator app IDs, associated with the Validator app.

    Args:
        algod_client (algod.AlgodClient): Configured client.
        validator_ad_app_id (int): Validator app.

    Returns:
        List[int]: List of Delegator app IDs.

    """
    val_client = GeneralValidatorAdClient(
        algod_client=algod_client, app_id=validator_ad_app_id
    )

    del_list_all = decode_uint64_list(
        val_client.get_global_state().del_contracts.as_bytes
    )

    del_list = [i for i in del_list_all if i != 0]

    return del_list



def get_del_state_list(
    algod_client: algod.AlgodClient,
    del_app_id_list: List[int],
) -> List[object]:
    """Get a list of Delegator app states (parameter groups).

    Args:
        algod_client (algod.AlgodClient): Configured client.
        del_app_id_list (List[int]): Delegator app IDs.

    Returns:
        List[object]: Delegator app states (parameter groups).

    """
    del_state_list = []
    for del_app_id in del_app_id_list:
        del_state_list.append(get_del_state(
            algod_client,
            del_app_id
        ))
    return del_state_list



def get_del_state(
    algod_client: algod.AlgodClient,
    del_app_id: int,
) -> object:
    """Get Delegator app state (parameter group).

    Args:
        algod_client (algod.AlgodClient): Configured client.
        del_app_id_list (int): Delegator app IDs.

    Returns:
        List[object]: Delegator app states (parameter groups).

    """
    del_client = DelegatorContractClient(
        algod_client=algod_client,
        app_id=del_app_id
    )

    return del_client.get_global_state()



def get_del_app_list(
    algod_client: algod.AlgodClient,
    validator_ad_app_id: int,
) -> List[object]:
    """Get a list of Delegator app IDs, associated with the Validator app.

    Args:
        algod_client (algod.AlgodClient): Configured client.
        validator_ad_app_id (int): Validator app.

    Returns:
        List[int]: List of Delegator app IDs.

    """

    del_app_id_list = get_del_id_list( algod_client, validator_ad_app_id )
    del_app_state_list = get_del_state_list( algod_client, del_app_id_list )

    return [ dict(id=id, state=state) for id, state in zip(del_app_id_list, del_app_state_list) ]



def get_val_app_state(
    algod_client: algod.AlgodClient,
    val_app_id: int,
) -> object:
    """Get Validatpr app state (parameter group).

    Args:
        algod_client (algod.AlgodClient): Configured client.
        del_app_id_list (int): Delegator app IDs.

    Returns:
        List[object]: Delegator app states (parameter groups).

    """
    val_client = GeneralValidatorAdClient(
        algod_client=algod_client,
        app_id=val_app_id
    )

    return val_client.get_global_state()



def decode_val_config_man(data: bytes):
    val_config_man_type = TupleType(
        [
            UintType(64),  # hw_cat
            UintType(64),  # min_amt
            UintType(64),  # max_amt
            UintType(64),  # fee_setup
            UintType(64),  # fee_round
            UintType(64),  # deposit
            UintType(64),  # setup_rounds
            UintType(64),  # confirmation_rounds
            UintType(64),  # max_breach
            UintType(64),  # breach_rounds
            UintType(64),  # uptime_gar
        ]
    )

    decoded_tuple = val_config_man_type.decode(data)

    val_config = ValConfigMan(
        hw_cat=decoded_tuple[0],
        min_amt=decoded_tuple[1],
        max_amt=decoded_tuple[2],
        fee_setup=decoded_tuple[3],
        fee_round=decoded_tuple[4],
        deposit=decoded_tuple[5],
        setup_rounds=decoded_tuple[6],
        confirmation_rounds=decoded_tuple[7],
        max_breach=decoded_tuple[8],
        breach_rounds=decoded_tuple[9],
        uptime_gar=decoded_tuple[10],
    )

    return val_config
