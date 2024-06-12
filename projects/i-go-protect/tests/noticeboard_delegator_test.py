import base64
from typing import List

import algokit_utils
import pytest
from algokit_utils import LogicError, OnCompleteCallParameters, TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import OnlineKeyRegParams, PayParams
from algokit_utils.config import config
from algosdk import abi
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.error import AlgodHTTPError
from algosdk.transaction import KeyregOfflineTxn
from algosdk.v2client import algod
from artifacts.general_validator_ad.client import GeneralValidatorAdClient
from conftest import (
    TestConsts,
    decode_uint64_list,
    decode_val_config_man,
    progress_rounds,
)

from smart_contracts.artifacts.delegator_contract.client import DelegatorContractClient
from smart_contracts.artifacts.gfactory_validator_ad.client import (
    GfactoryValidatorAdClient,
)
from smart_contracts.artifacts.noticeboard.client import NoticeboardClient


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


def set_noticeboard_client(
    algorand_client: AlgorandClient,
    noticeboard_client: NoticeboardClient,
    creator: AddressAndSigner,
) -> NoticeboardClient:

    # Create validator ad factory
    validator_factory_client = GfactoryValidatorAdClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )

    validator_factory_client.create_bare()
    # Needs to be funded with account MBR to be able to create validator ads later
    algokit_utils.ensure_funded(
        algorand_client.client.algod,
        algokit_utils.EnsureBalanceParameters(
            account_to_fund=validator_factory_client.app_address,
            min_spending_balance_micro_algos=0,
        ),
    )

    # Setup noticeboard
    # MBR for validator list box creation
    mbr_txn = TransactionWithSigner(
        algorand_client.transactions.payment(
            PayParams(
                sender=creator.address,
                receiver=noticeboard_client.app_address,
                amount=TestConsts.mbr_box_val_list_creation,
            )
        ),
        signer=creator.signer,
    )

    # Setup noticeboard
    result = noticeboard_client.setup(
        deposit_del_min=TestConsts.del_min_deposit,
        deposit_val_min=TestConsts.val_min_deposit,
        val_earn_factor=TestConsts.val_earn_factor,
        val_factory_app_id=validator_factory_client.app_id,
        manager=creator.address,
        mbr=mbr_txn,
        transaction_parameters=TransactionParameters(
            sender=creator.address,
            signer=creator.signer,
            boxes=[(noticeboard_client.app_id, "val_list")],
        ),
    )

    return noticeboard_client


def create_validators(
    algorand_client: AlgorandClient,
    noticeboard_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> NoticeboardClient:

    val_fact_app_id = noticeboard_client.get_global_state().val_factory_app_id
    val_fact_client = GfactoryValidatorAdClient(
        algod_client=algorand_client.client.algod,
        app_id=val_fact_app_id,
    )

    for val in validators:

        result = noticeboard_client.opt_in_user_opt_in(
            transaction_parameters=TransactionParameters(
                sender=val.address,
                signer=val.signer,
            ),
        )

        deposit = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=val.address,
                    receiver=noticeboard_client.app_address,
                    amount=TestConsts.val_min_deposit + 1,
                    extra_fee=3
                    * algorand_client.client.algod.suggested_params().min_fee,
                )
            ),
            signer=val.signer,
        )

        mbr_factory_txn = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=val.address,
                    receiver=val_fact_client.app_address,
                    amount=TestConsts.mbr_validatorad_creation,
                )
            ),
            signer=val.signer,
        )

        mbr_val_txn = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=val.address,
                    receiver=noticeboard_client.app_address,
                    amount=100_000,
                )
            ),
            signer=val.signer,
        )

        result = noticeboard_client.create_validator_ad(
            deposit=deposit,
            mbr_factory=mbr_factory_txn,
            mbr_val=mbr_val_txn,
            transaction_parameters=TransactionParameters(
                sender=val.address,
                signer=val.signer,
                foreign_apps=[val_fact_app_id],
                boxes=[(noticeboard_client.app_id, "val_list")],
            ),
        )

    assert result.confirmed_round

    return noticeboard_client


def get_del_list(
    algod_client: algod.AlgodClient,
    validator_ad_app_id: int,
) -> List[int]:

    val_client = GeneralValidatorAdClient(
        algod_client=algod_client, app_id=validator_ad_app_id
    )

    del_list_all = decode_uint64_list(
        val_client.get_global_state().del_contracts.as_bytes
    )

    del_list = [i for i in del_list_all if i != 0]

    return del_list


def get_val_list(
    algod_client: algod.AlgodClient,
    noitceboard_app_id: int,
) -> List[int]:

    response = algod_client.application_box_by_name(
        application_id=noitceboard_app_id,
        box_name=b"val_list",
    )

    # Decode the box contents from base64
    box_contents = base64.b64decode(response["value"])

    val_list_all = decode_uint64_list(box_contents)

    val_list = [i for i in val_list_all if i != 0]

    return val_list


def set_validator_ad(
    algorand_client: AlgorandClient,
    noticeboard_client: NoticeboardClient,
    val: AddressAndSigner,
    manager: AddressAndSigner,
) -> NoticeboardClient:

    val_app_id = noticeboard_client.get_local_state(val.address).val_app_id

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * sp.min_fee

    result = noticeboard_client.set_validator_ad_mandatory(
        val_config_man=TestConsts.val_config_man,
        live=True,
        manager=manager.address,
        max_del_cnt=TestConsts.max_del_cnt,
        transaction_parameters=OnCompleteCallParameters(
            sender=val.address,
            signer=val.signer,
            foreign_apps=[val_app_id],
            suggested_params=sp,
        ),
    )

    val_client = GeneralValidatorAdClient(
        algod_client=algorand_client.client.algod, app_id=val_app_id
    )

    assert val_client.get_global_state().live

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * sp.min_fee
    result = noticeboard_client.set_validator_ad_extra(
        val_config_extra=TestConsts.val_config_extra,
        transaction_parameters=OnCompleteCallParameters(
            sender=val.address,
            signer=val.signer,
            foreign_apps=[val_app_id],
            suggested_params=sp,
        ),
    )

    return noticeboard_client


@pytest.fixture(scope="session")
def noticeboard_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner],
) -> NoticeboardClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = NoticeboardClient(
        algorand_client.client.algod,
        creator=creator.address,
        signer=creator.signer,
        indexer_client=algorand_client.client.indexer,
    )

    client.create_bare()
    # Needs to be funded with account MBR to be able to set (and create box later during setup)
    algokit_utils.ensure_funded(
        algorand_client.client.algod,
        algokit_utils.EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=0,
        ),
    )

    client = set_noticeboard_client(
        algorand_client,
        client,
        creator,
    )

    client = create_validators(
        algorand_client,
        client,
        validators,
    )

    for idx, val in enumerate(validators):
        client = set_validator_ad(
            algorand_client,
            client,
            val,
            validators[(idx + 1) % len(validators)],
        )

    return client


@pytest.fixture(scope="session")
def noticeboard_w_validators_and_delegators_client(
    algorand_client: AlgorandClient,
    noticeboard_client: NoticeboardClient,
    delegators: List[AddressAndSigner],
) -> NoticeboardClient:

    val_list = get_val_list(
        algod_client=algorand_client.client.algod,
        noitceboard_app_id=noticeboard_client.app_id,
    )

    for idx, delegator in enumerate(delegators):

        # First opt in delegator to Noticeboard
        result = noticeboard_client.opt_in_user_opt_in(
            transaction_parameters=TransactionParameters(
                sender=delegator.address,
                signer=delegator.signer,
            ),
        )

        # Choose one validator
        val_app_id = val_list[idx % len(val_list)]

        val_client = GeneralValidatorAdClient(
            algod_client=algorand_client.client.algod,
            app_id=val_app_id,
        )

        # Get validator's requirements
        val_config_man = decode_val_config_man(
            val_client.get_global_state().val_config_man.as_bytes
        )

        sp = algorand_client.client.algod.suggested_params()

        # Create payment transaction for deposit to noticeboard
        deposit_txn = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=delegator.address,
                    receiver=noticeboard_client.app_address,
                    amount=val_config_man.deposit,
                    extra_fee=5 * sp.min_fee,
                )
            ),
            signer=delegator.signer,
        )

        # Create payment transaction for setup fee to noticeboard
        fee_txn = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=delegator.address,
                    receiver=noticeboard_client.app_address,
                    amount=val_config_man.fee_setup,
                )
            ),
            signer=delegator.signer,
        )

        # Create payment transaction for MBR increase to chosen validator
        mbr_txn = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=delegator.address,
                    receiver=val_client.app_address,
                    amount=TestConsts.mbr_delegatorcontract_creation,
                )
            ),
            signer=delegator.signer,
        )

        status = algorand_client.client.algod.status()
        current_round = status["last-round"]

        # Call noticeboard to create the delegator
        result = noticeboard_client.create_delegator_contract(
            val_app_id=val_app_id,
            deposit_payment=deposit_txn,
            fee_setup_payment=fee_txn,
            mbr=mbr_txn,
            round_start=current_round + TestConsts.round_start,
            round_end=current_round + TestConsts.round_end,
            transaction_parameters=TransactionParameters(
                sender=delegator.address,
                signer=delegator.signer,
                foreign_apps=[val_app_id],
            ),
        )

    assert result.confirmed_round

    return noticeboard_client


def test_delegator_contract(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
) -> None:

    assert noticeboard_w_validators_and_delegators_client.app_id


def deposit_keys_to_all_del_of_val(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
    val: AddressAndSigner,
    manager: AddressAndSigner,
) -> None:

    # Get validator's ad app ID for its local state in noticeboard
    val_app_id = noticeboard_w_validators_and_delegators_client.get_local_state(
        val.address
    ).val_app_id

    # Get validator's list of delegator contracts
    del_list = get_del_list(algorand_client.client.algod, val_app_id)

    # Deposit keys for each of its delegators
    for del_app_id in del_list:

        # Select one delegator contracts
        del_client = DelegatorContractClient(
            algod_client=algorand_client.client.algod,
            app_id=del_app_id,
        )
        # Get owner of the contract
        del_app_global = del_client.get_global_state()
        delegator = abi.AddressType().decode(del_app_global.del_acc.as_bytes)

        # Get suggested params
        sp = algorand_client.client.algod.suggested_params()
        sp.fee = 3 * sp.min_fee

        result = noticeboard_w_validators_and_delegators_client.deposit_keys(
            del_acc=delegator,
            sel_key=base64.b64decode(TestConsts.sel_key),
            vote_key=base64.b64decode(TestConsts.vote_key),
            state_proof_key=base64.b64decode(TestConsts.state_proof_key),
            vote_key_dilution=TestConsts.vote_key_dilution,
            round_start=del_app_global.round_start,
            round_end=del_app_global.round_end,
            transaction_parameters=TransactionParameters(
                sender=manager.address,
                signer=manager.signer,
                foreign_apps=[val_app_id, del_app_id],
                accounts=[delegator],
                suggested_params=sp,
            ),
        )

        del_app_global = del_client.get_global_state()

        assert del_app_global.part_keys_deposited == 1

    return


def test_deposit_keys(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> None:

    # Select one validator
    idx = 0
    val = validators[idx]

    # Get manager of validator (earlier it was set to another validator account)
    manager = validators[(idx + 1) % len(validators)]

    deposit_keys_to_all_del_of_val(
        algorand_client,
        noticeboard_w_validators_and_delegators_client,
        val,
        manager,
    )

    assert True


def confirm_all_keys_of_val(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
    val: AddressAndSigner,
    delegators: List[AddressAndSigner],
    manager: AddressAndSigner,
) -> None:

    deposit_keys_to_all_del_of_val(
        algorand_client,
        noticeboard_w_validators_and_delegators_client,
        val,
        manager,
    )

    # Get validator's ad app ID from its local state in noticeboard
    val_app_id = noticeboard_w_validators_and_delegators_client.get_local_state(
        val.address
    ).val_app_id

    # Get validator's list of delegator contracts
    del_list = get_del_list(algorand_client.client.algod, val_app_id)

    # Confirm keys for each of its delegators
    for idx, del_app_id in enumerate(del_list):

        # Get delegator contract
        del_client = DelegatorContractClient(
            algod_client=algorand_client.client.algod,
            app_id=del_app_id,
        )
        # Get owner of the contract
        del_app_global = del_client.get_global_state()
        delegator_addr = abi.AddressType().decode(del_app_global.del_acc.as_bytes)
        # Get signer for the delegator
        delegator = []
        for dele in delegators:
            if dele.address == delegator_addr:
                delegator = dele
                break
        # Get agreed configuration of the delegator contract
        del_config_man = decode_val_config_man(del_app_global.val_config_man.as_bytes)

        # Keys can't be confirmed until after the contract start
        status = algorand_client.client.algod.status()
        current_round = status["last-round"]
        rdif = del_app_global.round_start - current_round
        round_wait = rdif + 1 if rdif > 0 else 0

        # Progress with rounds until it can be claimed that keys haven't been generated
        progress_rounds(
            algorand_client=algorand_client, acc=delegator, num_rounds=round_wait
        )

        # Get suggested params
        sp = algorand_client.client.algod.suggested_params()

        # Create gtxn for key registration confirmation
        atc = AtomicTransactionComposer()

        # Create key registration transaction
        keyreg_txn = TransactionWithSigner(
            algorand_client.transactions.online_key_reg(
                OnlineKeyRegParams(
                    sender=delegator.address,
                    selection_key=TestConsts.sel_key,
                    vote_key=TestConsts.vote_key,
                    state_proof_key=TestConsts.state_proof_key,
                    vote_key_dilution=TestConsts.vote_key_dilution,
                    vote_first=del_app_global.round_start,
                    vote_last=del_app_global.round_end,
                )
            ),
            signer=delegator.signer,
        )
        atc.add_transaction(keyreg_txn)

        # Create operational fee payment transaction
        fee_operation_pay_txn = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=delegator.address,
                    receiver=noticeboard_w_validators_and_delegators_client.app_address,
                    amount=del_config_man.fee_round
                    * (del_app_global.round_end - del_app_global.round_start),
                    extra_fee=4 * sp.min_fee,
                )
            ),
            signer=delegator.signer,
        )

        # No need to add it to the ATC becuase it is added with compose_call below as it's supplied as parameter to the call
        # atc.add_transaction(fee_operation_pay_txn)

        noticeboard_w_validators_and_delegators_client.app_client.compose_call(
            atc,
            "confirm_keys",
            transaction_parameters=OnCompleteCallParameters(
                sender=delegator.address,
                signer=delegator.signer,
                foreign_apps=[val_app_id, del_app_id],
                suggested_params=sp,
            ),
            keyreg_txn_index=0,
            fee_operation_payment=fee_operation_pay_txn,
        )

        result = noticeboard_w_validators_and_delegators_client.app_client.execute_atc(
            atc
        )

        del_app_global = del_client.get_global_state()

        assert del_app_global.keys_confirmed == 1


def test_confirm_keys(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
    delegators: List[AddressAndSigner],
) -> None:

    # Select one validator
    idx = 1
    val = validators[idx]

    # Get manager of validator (earlier it was set to another validator account)
    manager = validators[(idx + 1) % len(validators)]

    confirm_all_keys_of_val(
        algorand_client,
        noticeboard_w_validators_and_delegators_client,
        val,
        delegators,
        manager,
    )


def test_keys_not_generated(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
    delegators: List[AddressAndSigner],
) -> None:

    # Select one validator
    idx = 2
    val = validators[idx]

    # Get validator's ad app ID from its local state in noticeboard
    val_app_id = noticeboard_w_validators_and_delegators_client.get_local_state(
        val.address
    ).val_app_id

    # Get validator's list of delegator contracts
    del_list = get_del_list(algorand_client.client.algod, val_app_id)

    # Select first delegator from validator's list which didn't have keys deposited
    for delegator in delegators:
        # Get delegator's selected validator ad app ID and delegator contract app ID from its local state in noticeboard
        del_local_state = (
            noticeboard_w_validators_and_delegators_client.get_local_state(
                delegator.address
            )
        )
        val_app_id = del_local_state.val_app_id
        del_app_id = del_local_state.del_app_id

        if del_app_id not in del_list:
            continue

        # Get info about the delegator contract
        del_client = DelegatorContractClient(
            algod_client=algorand_client.client.algod,
            app_id=del_app_id,
        )

        del_global_state = del_client.get_global_state()

        if del_global_state.part_keys_deposited == 0:
            break

    # Select an account that is opted-in to the Noticeboard
    trigger_acc = validators[-1]

    del_val_config_man = decode_val_config_man(del_global_state.val_config_man.as_bytes)
    round_claim = del_global_state.round_start + del_val_config_man.setup_rounds + 1
    status = algorand_client.client.algod.status()
    current_round = status["last-round"]
    rdif = round_claim - current_round
    round_wait = rdif if rdif > 0 else 0

    # Progress with rounds until it can be claimed that keys haven't been generated
    progress_rounds(
        algorand_client=algorand_client, acc=trigger_acc, num_rounds=round_wait
    )

    # Get suggested params
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 4 * sp.min_fee

    result = noticeboard_w_validators_and_delegators_client.keys_not_generated(
        del_acc=delegator.address,
        transaction_parameters=TransactionParameters(
            sender=trigger_acc.address,
            signer=trigger_acc.signer,
            foreign_apps=[val_app_id, del_app_id],
            accounts=[delegator.address],
            suggested_params=sp,
        ),
    )


def test_keys_not_confirmed(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
    delegators: List[AddressAndSigner],
) -> None:

    # Select one validator
    idx = 0
    val = validators[idx]

    # Get manager of validator (earlier it was set to another validator account)
    manager = validators[(idx + 1) % len(validators)]

    try:
        # Will fail in case of full file test because accounts were already opted in or keys deposited
        deposit_keys_to_all_del_of_val(
            algorand_client,
            noticeboard_w_validators_and_delegators_client,
            val,
            manager,
        )
    except AlgodHTTPError:
        pass
    except LogicError:
        pass

    # Get validator's ad app ID from its local state in noticeboard
    val_app_id = noticeboard_w_validators_and_delegators_client.get_local_state(
        val.address
    ).val_app_id

    # Get validator's list of delegator contracts
    del_list = get_del_list(algorand_client.client.algod, val_app_id)

    # Select first delegator contract from validator's list which didn't have keys confirmed
    for del_app_id in del_list:
        # Get info about the delegator contract
        del_client = DelegatorContractClient(
            algod_client=algorand_client.client.algod,
            app_id=del_app_id,
        )

        del_global_state = del_client.get_global_state()

        if del_global_state.keys_confirmed == 0:
            break

    # Check how long to wait before keys not confirmed can be claimed
    del_val_config_man = decode_val_config_man(del_global_state.val_config_man.as_bytes)
    round_claim = (
        del_global_state.round_start
        + del_val_config_man.setup_rounds
        + del_val_config_man.confirmation_rounds
        + 1
    )
    status = algorand_client.client.algod.status()
    current_round = status["last-round"]
    rdif = round_claim - current_round
    round_wait = rdif if rdif > 0 else 0

    # Select an account that is opted-in to the Noticeboard
    trigger_acc = validators[-1]

    # Progress with rounds until it can be claimed that keys haven't been confirmed
    progress_rounds(
        algorand_client=algorand_client, acc=trigger_acc, num_rounds=round_wait
    )

    delegator_addr = abi.AddressType().decode(del_global_state.del_acc.as_bytes)

    # Get suggested params
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 3 * sp.min_fee

    result = noticeboard_w_validators_and_delegators_client.keys_not_confirmed(
        del_acc=delegator_addr,
        transaction_parameters=TransactionParameters(
            sender=trigger_acc.address,
            signer=trigger_acc.signer,
            foreign_apps=[val_app_id, del_app_id],
            accounts=[delegator_addr],
            suggested_params=sp,
        ),
    )

    assert True


def test_end_expired_or_breached_delegator_contract(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
    delegators: List[AddressAndSigner],
) -> None:

    # Select one validator
    idx = 1
    val = validators[idx]

    # Select an account that is opted-in to the Noticeboard
    trigger_acc = validators[-1]

    # Get manager of validator (earlier it was set to another validator account)
    manager = validators[(idx + 1) % len(validators)]

    try:
        # Will fail in case of full file test because accounts were already opted in, keys deposited or keys confirmed
        confirm_all_keys_of_val(
            algorand_client,
            noticeboard_w_validators_and_delegators_client,
            val,
            delegators,
            manager,
        )
    except AlgodHTTPError:
        pass
    except LogicError:
        pass

    # Get validator's ad app ID from its local state in noticeboard
    val_app_id = noticeboard_w_validators_and_delegators_client.get_local_state(
        val.address
    ).val_app_id

    # Get validator's list of delegator contracts
    del_list = get_del_list(algorand_client.client.algod, val_app_id)

    # Select last delegator contract from validator's list
    del_app_id = del_list[-1]
    # Get info about the delegator contract
    del_client = DelegatorContractClient(
        algod_client=algorand_client.client.algod,
        app_id=del_app_id,
    )

    del_global_state = del_client.get_global_state()
    delegator_addr = abi.AddressType().decode(del_global_state.del_acc.as_bytes)

    # Check how long to wait before contract expires
    status = algorand_client.client.algod.status()
    current_round = status["last-round"]
    rdif = del_global_state.round_end - current_round
    round_wait = rdif if rdif > 0 else 0

    del_config_man = decode_val_config_man(del_global_state.val_config_man.as_bytes)
    # Report breaches until contract breached
    for i in range(del_config_man.max_breach):
        progress_rounds(algorand_client, trigger_acc, del_config_man.breach_rounds + 1)

        # Report breach
        result = del_client.stake_limit_breach(
            transaction_parameters=TransactionParameters(
                sender=trigger_acc.address,
                signer=trigger_acc.signer,
                accounts=[delegator_addr],
            ),
        )
        assert result.confirmed_round

    # Get suggested params
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 3 * sp.min_fee

    result = noticeboard_w_validators_and_delegators_client.end_expired_or_breached_delegator_contract(
        del_acc=delegator_addr,
        transaction_parameters=TransactionParameters(
            sender=trigger_acc.address,
            signer=trigger_acc.signer,
            foreign_apps=[val_app_id, del_app_id],
            accounts=[delegator_addr],
            suggested_params=sp,
        ),
    )

    with pytest.raises(AlgodHTTPError, match="application does not exist"):
        # Contract was deleted
        del_client.get_global_state()

    # Get new validator's list of delegator contracts
    del_list_new = get_del_list(algorand_client.client.algod, val_app_id)

    assert del_app_id not in del_list_new
    assert len(del_list) == len(del_list_new) + 1

    # Select an account that is opted-in to the Noticeboard
    trigger_acc = validators[-1]

    # Select anotther delegator contract from validator's list
    del_app_id = del_list_new[-1]
    # Get info about the delegator contract
    del_client = DelegatorContractClient(
        algod_client=algorand_client.client.algod,
        app_id=del_app_id,
    )

    del_global_state = del_client.get_global_state()

    # Check how long to wait before contract expires
    status = algorand_client.client.algod.status()
    current_round = status["last-round"]
    rdif = del_global_state.round_end - current_round
    round_wait = rdif if rdif > 0 else 0

    # Progress with rounds until the contract expires
    progress_rounds(
        algorand_client=algorand_client, acc=trigger_acc, num_rounds=round_wait
    )

    delegator_addr = abi.AddressType().decode(del_global_state.del_acc.as_bytes)

    # Get suggested params
    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 3 * sp.min_fee

    result = noticeboard_w_validators_and_delegators_client.end_expired_or_breached_delegator_contract(
        del_acc=delegator_addr,
        transaction_parameters=TransactionParameters(
            sender=trigger_acc.address,
            signer=trigger_acc.signer,
            foreign_apps=[val_app_id, del_app_id],
            accounts=[delegator_addr],
            suggested_params=sp,
        ),
    )

    with pytest.raises(AlgodHTTPError, match="application does not exist"):
        # Contract was deleted
        del_client.get_global_state()


def test_end_active_delegator_contract(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_and_delegators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
    delegators: List[AddressAndSigner],
) -> None:

    # Select one validator
    idx = 1
    val = validators[idx]

    # Get manager of validator (earlier it was set to another validator account)
    manager = validators[(idx + 1) % len(validators)]

    try:
        # Will fail in case of full file test because accounts were already opted in, keys deposited or keys confirmed
        confirm_all_keys_of_val(
            algorand_client,
            noticeboard_w_validators_and_delegators_client,
            val,
            delegators,
            manager,
        )
    except AlgodHTTPError as e:
        print(e)
        pass
    except LogicError as e:
        print(e)
        pass

    # Get validator's ad app ID from its local state in noticeboard
    val_app_id = noticeboard_w_validators_and_delegators_client.get_local_state(
        val.address
    ).val_app_id

    # Get validator's list of delegator contracts
    del_list = get_del_list(algorand_client.client.algod, val_app_id)

    # Select last delegator contract from validator's list
    del_app_id = del_list[-1]
    # Get info about the delegator contract
    del_client = DelegatorContractClient(
        algod_client=algorand_client.client.algod,
        app_id=del_app_id,
    )

    del_global_state = del_client.get_global_state()
    delegator_addr = abi.AddressType().decode(del_global_state.del_acc.as_bytes)

    for dele in delegators:
        if dele.address == delegator_addr:
            delegator = dele
            break

    # Get suggested params
    sp = algorand_client.client.algod.suggested_params()

    # Create gtxn for key registration confirmation
    atc = AtomicTransactionComposer()

    # Create key deregistration transaction
    keydereg_txn = TransactionWithSigner(
        KeyregOfflineTxn(sender=delegator.address, sp=sp),
        signer=delegator.signer,
    )
    atc.add_transaction(keydereg_txn)
    # Need to add it to the ATC becuase it is passed in app only as index

    sp.fee = 3 * sp.min_fee
    noticeboard_w_validators_and_delegators_client.app_client.compose_call(
        atc,
        "end_active_delegator_contract",
        transaction_parameters=OnCompleteCallParameters(
            sender=delegator.address,
            signer=delegator.signer,
            foreign_apps=[val_app_id, del_app_id],
            suggested_params=sp,
        ),
        keyreg_txn_index=0,
    )

    result = noticeboard_w_validators_and_delegators_client.app_client.execute_atc(atc)

    with pytest.raises(AlgodHTTPError, match="application does not exist"):
        # Contract was deleted
        del_client.get_global_state()
