import base64
from typing import List

import pytest
from algokit_utils import OnCompleteCallParameters, TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.config import config
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import OnComplete
from conftest import (
    TestConsts,
    decode_val_config_extra,
    decode_val_config_man,
    progress_rounds,
)

from smart_contracts.artifacts.delegator_contract.client import (
    DelegatorContractClient,
)
from smart_contracts.artifacts.general_validator_ad.client import (
    GeneralValidatorAdClient,
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


@pytest.fixture(scope="session")
def validators(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
) -> List[AddressAndSigner]:
    accs = []
    for i in range(TestConsts.num_vals):
        acc = algorand_client.account.random()
        algorand_client.send.payment(
            PayParams(
                sender=dispenser.address,
                receiver=acc.address,
                amount=TestConsts.acc_dispenser_amt,
            )
        )
        accs.append(acc)
    return accs


@pytest.fixture(scope="session")
def delegators(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
) -> List[AddressAndSigner]:
    accs = []
    for i in range(TestConsts.num_dels):
        acc = algorand_client.account.random()
        algorand_client.send.payment(
            PayParams(
                sender=dispenser.address,
                receiver=acc.address,
                amount=TestConsts.acc_dispenser_amt,
            )
        )
        accs.append(acc)
    return accs


@pytest.fixture(scope="function")
def validator_ad_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> GeneralValidatorAdClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = GeneralValidatorAdClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )

    res = client.create_create(
        owner=creator.address,
        noticeboard_app_id=0,
        val_earn_factor=TestConsts.val_earn_factor,
        deposit=TestConsts.val_min_deposit,
    )

    print(res.confirmed_round)

    return client


def test_set_mandatory(
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
) -> None:

    result = validator_ad_client.set_mandatory(
        val_config_man=TestConsts.val_config_man,
        live=True,
        manager=creator.address,
        max_del_cnt=2,
    )

    assert result.confirmed_round

    gs = validator_ad_client.get_global_state()
    val_config_man_dec = decode_val_config_man(gs.val_config_man.as_bytes)

    assert val_config_man_dec == TestConsts.val_config_man


def test_set_extra(
    validator_ad_client: GeneralValidatorAdClient,
) -> None:

    result = validator_ad_client.set_extra(
        val_config_extra=TestConsts.val_config_extra,
    )

    assert result.confirmed_round

    gs = validator_ad_client.get_global_state()
    val_config_extra_dec = decode_val_config_extra(gs.val_config_extra.as_bytes)

    assert val_config_extra_dec == TestConsts.val_config_extra


def test_end_validator_ad(
    validator_ad_client: GeneralValidatorAdClient,
) -> None:

    result = validator_ad_client.delete_end_validator_ad()

    assert result.confirmed_round
    assert result.return_value == 0


def test_withdraw_earnings(
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
) -> None:

    result = validator_ad_client.withdraw_earnings()

    assert result.confirmed_round
    assert result.return_value == 0


# ----- ----- ----- --------------------------------- ----- ----- -----
# ----- ----- ----- For delegator contract management ----- ----- -----
# ----- ----- ----- --------------------------------- ----- ----- -----


def create_delegator_contract(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    manager: AddressAndSigner,
) -> DelegatorContractClient:
    # Set validator
    result = validator_ad_client.set_mandatory(
        val_config_man=TestConsts.val_config_man,
        live=True,
        manager=manager.address,
        max_del_cnt=TestConsts.max_del_cnt,
    )

    # Create gtxn for delegator contract creation
    atc = AtomicTransactionComposer()
    mbr_txn = TransactionWithSigner(
        algorand_client.transactions.payment(
            PayParams(
                sender=creator.address,
                receiver=validator_ad_client.app_address,
                amount=TestConsts.mbr_delegatorcontract_creation + 100_000,
                extra_fee=3 * 1_000,
            )
        ),
        signer=creator.signer,
    )
    atc.add_transaction(mbr_txn)

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]

    validator_ad_client.app_client.compose_call(
        atc,
        "create_delegator_contract",
        transaction_parameters=OnCompleteCallParameters(on_complete=OnComplete.NoOpOC),
        deposit_payment_amount=TestConsts.val_config_man.deposit,
        fee_setup_payment_amount=TestConsts.val_config_man.fee_setup,
        del_acc=creator.address,
        round_start=current_round + TestConsts.round_start,
        round_end=current_round + TestConsts.round_end,
    )

    result = validator_ad_client.app_client.execute_atc(atc)
    print(f"Transaction sent with txID: {result.tx_ids}")

    assert result.confirmed_round

    created_app_id = result.abi_results[0].return_value

    delegator_contract_client = DelegatorContractClient(
        algod_client=algorand_client.client.algod,
        app_id=created_app_id,
        signer=creator.signer,
        sender=creator.address,
    )

    return delegator_contract_client


def test_create_delegator_contract(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> None:

    assert create_delegator_contract(
        algorand_client, validator_ad_client, creator, validators[0]
    )


def create_and_deposit_keys(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> DelegatorContractClient:
    manager = validators[0]
    # Create delegator contract
    delegator_contract_client = create_delegator_contract(
        algorand_client,
        validator_ad_client,
        creator,
        manager,
    )

    # Create client for delegator contract
    gs_del = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs_del.val_config_man.as_bytes)

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * 1_000

    result = validator_ad_client.deposit_keys(
        caller=manager.address,
        del_app_id=delegator_contract_client.app_id,
        sel_key=base64.b64decode(TestConsts.sel_key),
        vote_key=base64.b64decode(TestConsts.vote_key),
        state_proof_key=base64.b64decode(TestConsts.state_proof_key),
        vote_key_dilution=TestConsts.vote_key_dilution,
        round_start=gs_del.round_start,
        round_end=gs_del.round_end,
        transaction_parameters=OnCompleteCallParameters(
            foreign_apps=[delegator_contract_client.app_id],
            suggested_params=sp,
        ),
    )

    gs_val = validator_ad_client.get_global_state()

    assert result.confirmed_round
    assert result.return_value == del_config_man.fee_setup - (
        (del_config_man.fee_setup * gs_val.val_earn_factor) // 100
    )

    return delegator_contract_client


def test_deposit_keys(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> None:

    assert create_and_deposit_keys(
        algorand_client, validator_ad_client, creator, validators
    )


def create_deposit_and_confirm(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
):

    delegator_contract_client = create_and_deposit_keys(
        algorand_client, validator_ad_client, creator, validators
    )

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * 1_000

    gs_del = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs_del.val_config_man.as_bytes)

    result = validator_ad_client.confirm_keys(
        del_app_id=delegator_contract_client.app_id,
        fee_operation_payment_amount=del_config_man.fee_round
        * (gs_del.round_end - gs_del.round_start),
        sel_key=base64.b64decode(TestConsts.sel_key),
        vote_key=base64.b64decode(TestConsts.vote_key),
        state_proof_key=base64.b64decode(TestConsts.state_proof_key),
        vote_key_dilution=TestConsts.vote_key_dilution,
        round_start=gs_del.round_start,
        round_end=gs_del.round_end,
        transaction_parameters=TransactionParameters(
            foreign_apps=[delegator_contract_client.app_id],
            suggested_params=sp,
        ),
    )

    gs_val = validator_ad_client.get_global_state()

    assert result.confirmed_round
    assert result.return_value == del_config_man.fee_setup - (
        (del_config_man.fee_setup * gs_val.val_earn_factor) // 100
    )

    return delegator_contract_client


def test_confirm_keys(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> None:

    assert create_deposit_and_confirm(
        algorand_client, validator_ad_client, creator, validators
    )


def test_keys_not_generated(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> None:

    # Create delegator contract
    delegator_contract_client = create_delegator_contract(
        algorand_client, validator_ad_client, creator, validators[0]
    )

    # Need to wait for contract to start and for setup rounds to pass before claiming keys weren't generated
    progress_rounds(
        algorand_client,
        creator,
        TestConsts.round_start + TestConsts.val_config_man.setup_rounds + 1,
    )

    # Need to check global state of delegator contract before deleting it
    gs_del = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs_del.val_config_man.as_bytes)

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * 1_000

    result = validator_ad_client.keys_not_generated(
        del_app_id=delegator_contract_client.app_id,
        transaction_parameters=TransactionParameters(
            foreign_apps=[delegator_contract_client.app_id],
            suggested_params=sp,
        ),
    )

    assert result.return_value == del_config_man.fee_setup


def test_keys_not_confirmed(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> None:

    # Create delegator contract and deposit keys
    delegator_contract_client = create_and_deposit_keys(
        algorand_client,
        validator_ad_client,
        creator,
        validators,
    )

    # Need to wait for setup + confirm rounds to pass before claiming keys weren't confirmed
    progress_rounds(
        algorand_client,
        creator,
        TestConsts.val_config_man.setup_rounds
        + TestConsts.val_config_man.confirmation_rounds
        + 1,
    )

    # Need to check global state of delegator contract before deleting it
    gs_del = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs_del.val_config_man.as_bytes)

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * 1_000

    result = validator_ad_client.keys_not_confirmed(
        del_app_id=delegator_contract_client.app_id,
        transaction_parameters=OnCompleteCallParameters(
            foreign_apps=[delegator_contract_client.app_id],
            suggested_params=sp,
        ),
    )

    gs_val = validator_ad_client.get_global_state()

    assert result.return_value == del_config_man.fee_setup - (
        (del_config_man.fee_setup * gs_val.val_earn_factor) // 100
    )


def test_end_delegator_contract_prematurely(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> None:

    # Create delegator contract, deposit and confirm keys
    delegator_contract_client = create_deposit_and_confirm(
        algorand_client, validator_ad_client, creator, validators
    )

    # Need to check global state of delegator contract before deleting it
    gs_del = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs_del.val_config_man.as_bytes)

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * 1_000

    result = validator_ad_client.end_delegator_contract(
        del_app_id=delegator_contract_client.app_id,
        transaction_parameters=OnCompleteCallParameters(
            foreign_apps=[delegator_contract_client.app_id],
            suggested_params=sp,
        ),
    )

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]

    gs_val = validator_ad_client.get_global_state()

    assert result.return_value.a == del_config_man.deposit
    assert result.return_value.b == del_config_man.fee_round * (
        gs_del.round_end - current_round
    )

    full_earnings = del_config_man.fee_round * (current_round - gs_del.round_start)
    platform_earnings = full_earnings - (
        (full_earnings * gs_val.val_earn_factor) // 100
    )

    assert result.return_value.c == platform_earnings


def test_end_delegator_contract_successfully(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> None:

    # Create delegator contract, deposit and confirm keys
    delegator_contract_client = create_deposit_and_confirm(
        algorand_client, validator_ad_client, creator, validators
    )

    # Progress rounds for delegator contract to end
    progress_rounds(algorand_client, creator, TestConsts.round_end + 1)

    # Need to check global state of delegator contract before deleting it
    gs_del = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs_del.val_config_man.as_bytes)

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * 1_000

    result = validator_ad_client.end_delegator_contract(
        del_app_id=delegator_contract_client.app_id,
        transaction_parameters=OnCompleteCallParameters(
            foreign_apps=[delegator_contract_client.app_id],
            suggested_params=sp,
        ),
    )

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]

    gs_val = validator_ad_client.get_global_state()

    assert result.return_value.a == del_config_man.deposit
    assert result.return_value.b == 0

    full_earnings = del_config_man.fee_round * (gs_del.round_end - gs_del.round_start)
    platform_earnings = full_earnings - (
        (full_earnings * gs_val.val_earn_factor) // 100
    )

    assert result.return_value.c == platform_earnings


def test_end_delegator_contract_prematurely_breached(
    algorand_client: AlgorandClient,
    validator_ad_client: GeneralValidatorAdClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> None:

    # Create delegator contract, deposit and confirm keys
    delegator_contract_client = create_deposit_and_confirm(
        algorand_client, validator_ad_client, creator, validators
    )

    # Need to check global state of delegator contract before deleting it
    gs_del = delegator_contract_client.get_global_state()
    del_config_man = decode_val_config_man(gs_del.val_config_man.as_bytes)

    # Report breaches until contract breached
    for i in range(del_config_man.max_breach):
        progress_rounds(algorand_client, creator, del_config_man.breach_rounds + 1)

        # Report breach
        result = delegator_contract_client.stake_limit_breach()
        assert result.confirmed_round

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * 1_000

    result = validator_ad_client.end_delegator_contract(
        del_app_id=delegator_contract_client.app_id,
        transaction_parameters=OnCompleteCallParameters(
            foreign_apps=[delegator_contract_client.app_id],
            suggested_params=sp,
        ),
    )

    status = algorand_client.client.algod.status()
    current_round = status["last-round"]

    rdif = gs_del.round_end - current_round

    gs_val = validator_ad_client.get_global_state()

    assert result.return_value.a == 0
    assert result.return_value.b == del_config_man.fee_round * (rdif if rdif > 0 else 0)

    full_earnings = (
        del_config_man.fee_round
        * (
            gs_del.round_end - gs_del.round_start
            if rdif < 0
            else current_round - gs_del.round_start
        )
        + del_config_man.deposit
    )
    platform_earnings = full_earnings - (
        (full_earnings * gs_val.val_earn_factor) // 100
    )

    assert result.return_value.c == platform_earnings
