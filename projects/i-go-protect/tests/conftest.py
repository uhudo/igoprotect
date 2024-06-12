import struct
from math import sqrt
from pathlib import Path

import pytest
from algokit_utils import (
    get_algod_client,
    get_indexer_client,
    is_localnet,
)
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import *
from algosdk.abi import ArrayStaticType, ByteType, TupleType, UintType
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient
from dotenv import load_dotenv

from smart_contracts.artifacts.general_validator_ad.client import (
    ValConfigExtra,
    ValConfigMan,
)


def progress_rounds(
    algorand_client: AlgorandClient,
    acc: AddressAndSigner,
    num_rounds: int,
) -> None:
    # Progress with rounds by sending transactions
    for i in range(num_rounds):
        # Send the transaction
        mbr_txn = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=acc.address,
                    receiver=acc.address,
                    amount=0,
                    extra_fee=1_000,
                )
            ),
            signer=acc.signer,
        )

        atc = AtomicTransactionComposer()
        atc.add_transaction(mbr_txn)

        res = atc.execute(algorand_client.client.algod, 4)

        # print(f"Transaction sent with txID: {res.tx_ids}")

    return


def fixed_length_str(input_string: str, length: int):
    if len(input_string) > length:
        return input_string[:length]
    else:
        return input_string.ljust(length, "-")


def StaticArrayLen(string: str, length: int) -> bytes:
    return bytes(fixed_length_str(string, length), encoding="UTF-8")


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


def decode_val_config_extra(data: bytes):
    val_config_extra_type = TupleType(
        [
            ArrayStaticType(ByteType(), 30),  # name
            ArrayStaticType(ByteType(), 70),  # link
        ]
    )

    decoded_tuple = val_config_extra_type.decode(data)

    val_config = ValConfigExtra(
        name=bytes(decoded_tuple[0]),
        link=bytes(decoded_tuple[1]),
    )

    return val_config


def decode_uint64_list(data: bytes):
    # Determine the number of uint64 values in the bytes object
    num_uint64 = len(data) // 8

    # Unpack the bytes object into a list of uint64 values (big-endian)
    int_list = list(struct.unpack(f">{num_uint64}Q", data))

    return int_list


class TestConsts:
    acc_dispenser_amt = 40_000_000
    num_vals = 3
    num_dels = 11
    del_min_deposit = 10_000
    val_min_deposit = 40_000
    mbr_box_val_list_creation = 325_700
    max_del_cnt = 4
    val_earn_factor = 33
    mbr_validatorad_creation = 899_500
    mbr_delegatorcontract_creation = 785_000

    round_start = 2
    round_end = 331

    val_config_man = ValConfigMan(
        hw_cat=0,
        min_amt=300_000_000,
        max_amt=500_000_000,
        fee_setup=9_999,
        fee_round=11,
        deposit=14_141,
        setup_rounds=11,
        confirmation_rounds=16,
        max_breach=3,
        breach_rounds=2,
        uptime_gar=24,
    )

    sel_key = "TyPKJHa8IcFFwJ0xvx4/uUeGgVk4pp8r90S5J/xya4M="
    vote_key = "CrPTVLdfR0z5U5Vx2MbcY8pMM8MDq7uSmKL8YJgGwuw="
    state_proof_key = "wcT8pSuOGU84gHJr67NiasgsMpr5pFir6wnzYCmEddnsp5Ys7mh9zWZ6jJJY7VK8jM3FsBoEnHFboYci8VbNpQ=="
    vote_key_dilution = round(sqrt(round_end - round_start))

    val_config_extra = ValConfigExtra(
        name=StaticArrayLen("My name", 30),
        link=StaticArrayLen(
            "Very very very very very loooooooooooooooooooooooooooooooooong liiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiiink.",
            70,
        ),
    )


@pytest.fixture(autouse=True, scope="session")
def environment_fixture() -> None:
    env_path = Path(__file__).parent.parent / ".env.localnet"
    load_dotenv(env_path)


@pytest.fixture(scope="session")
def algod_client() -> AlgodClient:
    client = get_algod_client()

    # you can remove this assertion to test on other networks,
    # included here to prevent accidentally running against other networks
    assert is_localnet(client)
    return client


@pytest.fixture(scope="session")
def indexer_client() -> IndexerClient:
    return get_indexer_client()


@pytest.fixture(scope="session")
def algorand_client() -> AlgorandClient:
    client = AlgorandClient.default_local_net()
    client.set_suggested_params_timeout(0)
    return client


@pytest.fixture(scope="session")
def test_consts() -> TestConsts:
    return TestConsts
