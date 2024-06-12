import base64

import pytest
from algokit_utils import OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.config import config
from algokit_utils.logic_error import LogicError
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import OnComplete
from conftest import TestConsts, decode_val_config_man, progress_rounds

from smart_contracts.artifacts.delegator_contract.client import (
    DelegatorContractClient,
)


@pytest.fixture(scope="session")
def dispenser(algorand_client: AlgorandClient) -> AddressAndSigner:
    return algorand_client.account.dispenser()


@pytest.fixture(scope="session")
def creator(
    algorand_client: AlgorandClient, dispenser: AddressAndSigner
) -> AddressAndSigner:
    acc = algorand_client.account.random()
    algorand_client.send.payment(
        PayParams(
            sender=dispenser.address,
            receiver=acc.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )
    return acc


@pytest.fixture(scope="function")
def delegator_contract_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> DelegatorContractClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = DelegatorContractClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]

    res = client.create_create(
        del_acc=creator.address,
        noticeboard_app_id=0,
        round_start=current_round + TestConsts.round_start,
        round_end=current_round + TestConsts.round_end,
    )

    print(res.confirmed_round)

    return client


def test_set_mandatory(
    delegator_contract_client: DelegatorContractClient,
) -> None:

    result = delegator_contract_client.set_mandatory(
        val_config_man=TestConsts.val_config_man,
    )

    assert result.confirmed_round


def test_set_extra(
    delegator_contract_client: DelegatorContractClient,
) -> None:

    result = delegator_contract_client.set_extra(
        val_config_extra=TestConsts.val_config_extra,
    )

    assert result.confirmed_round


def test_deposit_keys(
    delegator_contract_client: DelegatorContractClient,
) -> None:

    # Configure mandatory
    result = delegator_contract_client.set_mandatory(
        val_config_man=TestConsts.val_config_man,
    )

    # Deposit keys
    gs = delegator_contract_client.get_global_state()
    result = delegator_contract_client.deposit_keys(
        sel_key=base64.b64decode(TestConsts.sel_key),
        vote_key=base64.b64decode(TestConsts.vote_key),
        state_proof_key=base64.b64decode(TestConsts.state_proof_key),
        vote_key_dilution=TestConsts.vote_key_dilution,
        round_start=gs.round_start,
        round_end=gs.round_end,
    )

    assert result.confirmed_round


def config_deposit_and_confirm(
    algorand_client: AlgorandClient,
    delegator_contract_client: DelegatorContractClient,
    creator: AddressAndSigner,
) -> None:

    # Configure mandatory
    result = delegator_contract_client.set_mandatory(
        val_config_man=TestConsts.val_config_man,
    )

    # Deposit keys
    gs = delegator_contract_client.get_global_state()
    result = delegator_contract_client.deposit_keys(
        sel_key=base64.b64decode(TestConsts.sel_key),
        vote_key=base64.b64decode(TestConsts.vote_key),
        state_proof_key=base64.b64decode(TestConsts.state_proof_key),
        vote_key_dilution=TestConsts.vote_key_dilution,
        round_start=gs.round_start,
        round_end=gs.round_end,
    )

    # Wait for first round when the key can be confirmed
    status = algorand_client.client.algod.status()
    current_round = status["last-round"]
    to_wait = gs.round_start - current_round + 1
    progress_rounds(algorand_client, creator, to_wait)

    # Confirm keys
    gs = delegator_contract_client.get_global_state()
    val_config_man_dec = decode_val_config_man(gs.val_config_man.as_bytes)
    result = delegator_contract_client.confirm_keys(
        fee_operation_payment_amount=(
            val_config_man_dec.fee_round * (gs.round_end - gs.round_start)
        ),
        sel_key=base64.b64decode(TestConsts.sel_key),
        vote_key=base64.b64decode(TestConsts.vote_key),
        state_proof_key=base64.b64decode(TestConsts.state_proof_key),
        vote_key_dilution=TestConsts.vote_key_dilution,
        round_start=gs.round_start,
        round_end=gs.round_end,
    )

    assert result.confirmed_round

    return


def test_confirm_keys(
    algorand_client: AlgorandClient,
    delegator_contract_client: DelegatorContractClient,
    creator: AddressAndSigner,
) -> None:

    # Configure delegator, deposit keys, and confirm keys
    config_deposit_and_confirm(algorand_client, delegator_contract_client, creator)

    return


def test_keys_not_generated(
    delegator_contract_client: DelegatorContractClient,
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> None:

    # Wait until it can be claimed that keys weren't generated
    gs = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs.val_config_man.as_bytes)

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]
    until = gs.round_start + del_config_man.setup_rounds + 1
    to_wait = until - current_round
    to_wait = to_wait if to_wait > 0 else 0
    progress_rounds(algorand_client, creator, to_wait)

    mbr_txn = TransactionWithSigner(
        algorand_client.transactions.payment(
            PayParams(
                sender=creator.address,
                receiver=creator.address,
                amount=TestConsts.mbr_delegatorcontract_creation,
                extra_fee=1_000,
            )
        ),
        signer=creator.signer,
    )

    atc = AtomicTransactionComposer()
    atc.add_transaction(mbr_txn)

    # Just to test how to compose a more complex call
    delegator_contract_client.app_client.compose_call(
        atc,
        "keys_not_confirmed",
        transaction_parameters=OnCompleteCallParameters(
            on_complete=OnComplete.DeleteApplicationOC
        ),
    )

    result = delegator_contract_client.app_client.execute_atc(atc)

    assert result.confirmed_round


def test_keys_not_confirmed(
    delegator_contract_client: DelegatorContractClient,
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> None:

    # Configure mandatory
    result = delegator_contract_client.set_mandatory(
        val_config_man=TestConsts.val_config_man,
    )

    # Deposit keys
    gs = delegator_contract_client.get_global_state()
    result = delegator_contract_client.deposit_keys(
        sel_key=base64.b64decode(TestConsts.sel_key),
        vote_key=base64.b64decode(TestConsts.vote_key),
        state_proof_key=base64.b64decode(TestConsts.state_proof_key),
        vote_key_dilution=TestConsts.vote_key_dilution,
        round_start=gs.round_start,
        round_end=gs.round_end,
    )

    # Progress rounds
    progress_rounds(algorand_client, creator, 2)

    # Claim keys not confirmed
    try:
        delegator_contract_client.delete_keys_not_confirmed(),
    except LogicError as e:
        print(f"Error: {e}")
        print(f"Error type: {type(e).__name__}")

    # Wait until it can be claimed that keys weren't confirmed
    gs = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs.val_config_man.as_bytes)

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]
    until = (
        gs.round_start
        + del_config_man.setup_rounds
        + del_config_man.confirmation_rounds
        + 1
    )
    to_wait = until - current_round
    to_wait = to_wait if to_wait > 0 else 0
    progress_rounds(algorand_client, creator, to_wait)

    result = delegator_contract_client.delete_keys_not_confirmed()

    assert result.confirmed_round


def test_end_contract_prematurely(
    delegator_contract_client: DelegatorContractClient,
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> None:

    # Configure delegator, deposit keys, and confirm keys
    config_deposit_and_confirm(algorand_client, delegator_contract_client, creator)

    # Progress rounds
    progress_rounds(algorand_client, creator, 1)

    gs = delegator_contract_client.get_global_state()

    result = delegator_contract_client.delete_end_contract()

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]

    assert result.return_value.a == TestConsts.val_config_man.deposit
    assert result.return_value.b == TestConsts.val_config_man.fee_round * (
        gs.round_end - current_round
    )
    assert result.return_value.c == TestConsts.val_config_man.fee_round * (
        current_round - gs.round_start
    )

    assert result.confirmed_round


def test_end_contract_successfully(
    delegator_contract_client: DelegatorContractClient,
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> None:

    # Configure delegator, deposit keys, and confirm keys
    config_deposit_and_confirm(algorand_client, delegator_contract_client, creator)

    # Progress rounds
    gs = delegator_contract_client.get_global_state()

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]
    rdif = gs.round_end - current_round
    round_wait = rdif if rdif > 0 else 0
    progress_rounds(algorand_client, creator, round_wait)

    result = delegator_contract_client.delete_end_contract()

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]

    assert result.return_value.a == TestConsts.val_config_man.deposit
    assert result.return_value.b == 0
    assert result.return_value.c == TestConsts.val_config_man.fee_round * (
        gs.round_end - gs.round_start
    )

    assert result.confirmed_round


def test_end_contract_prematurely_breached(
    delegator_contract_client: DelegatorContractClient,
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> None:

    # Configure delegator, deposit keys, and confirm keys
    config_deposit_and_confirm(algorand_client, delegator_contract_client, creator)

    # Report breach
    result = delegator_contract_client.stake_limit_breach()
    assert result.confirmed_round

    # Try breach
    try:
        result = delegator_contract_client.stake_limit_breach()
        assert result.confirmed_round
    except LogicError as e:
        print(e)

    # Progress rounds
    for i in range(TestConsts.val_config_man.max_breach - 1):
        progress_rounds(
            algorand_client, creator, TestConsts.val_config_man.breach_rounds + 1
        )

        # Report breach again
        result = delegator_contract_client.stake_limit_breach()
        assert result.confirmed_round

    # Progress rounds
    progress_rounds(algorand_client, creator, 0)

    gs = delegator_contract_client.get_global_state()

    result = delegator_contract_client.delete_end_contract()

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]

    rdif = gs.round_end - current_round

    assert result.return_value.a == 0
    assert result.return_value.b == TestConsts.val_config_man.fee_round * (
        rdif if rdif > 0 else 0
    )
    assert (
        result.return_value.c
        == TestConsts.val_config_man.fee_round
        * (
            gs.round_end - gs.round_start
            if rdif < 0
            else current_round - gs.round_start
        )
        + TestConsts.val_config_man.deposit
    )

    assert result.confirmed_round
