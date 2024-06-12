import base64
from typing import List

import algokit_utils
import pytest
from algokit_utils import OnCompleteCallParameters, TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.config import config
from algosdk.atomic_transaction_composer import (
    TransactionWithSigner,
)
from algosdk.error import AlgodHTTPError
from algosdk.v2client import algod
from artifacts.general_validator_ad.client import GeneralValidatorAdClient
from conftest import TestConsts, decode_uint64_list

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


@pytest.fixture(scope="session")
def noticeboard_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
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

    return client


@pytest.fixture(scope="session")
def validator_factory_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
) -> GfactoryValidatorAdClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

    client = GfactoryValidatorAdClient(
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

    return client


@pytest.fixture(scope="session")
def set_noticeboard_client(
    algorand_client: AlgorandClient,
    noticeboard_client: NoticeboardClient,
    creator: AddressAndSigner,
) -> NoticeboardClient:
    config.configure(
        debug=True,
        # trace_all=True,
    )

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


def test_setup_noticeboard(
    set_noticeboard_client: NoticeboardClient,
) -> None:

    assert set_noticeboard_client.get_global_state().live == 1


@pytest.fixture(scope="session")
def noticeboard_w_validators_client(
    algorand_client: AlgorandClient,
    set_noticeboard_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> NoticeboardClient:

    val_fact_app_id = set_noticeboard_client.get_global_state().val_factory_app_id
    val_fact_client = GfactoryValidatorAdClient(
        algod_client=algorand_client.client.algod,
        app_id=val_fact_app_id,
    )

    for val in validators:

        result = set_noticeboard_client.opt_in_user_opt_in(
            transaction_parameters=TransactionParameters(
                sender=val.address,
                signer=val.signer,
            ),
        )

        deposit = TransactionWithSigner(
            algorand_client.transactions.payment(
                PayParams(
                    sender=val.address,
                    receiver=set_noticeboard_client.app_address,
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
                    receiver=set_noticeboard_client.app_address,
                    amount=100_000,
                )
            ),
            signer=val.signer,
        )

        result = set_noticeboard_client.create_validator_ad(
            deposit=deposit,
            mbr_factory=mbr_factory_txn,
            mbr_val=mbr_val_txn,
            transaction_parameters=TransactionParameters(
                sender=val.address,
                signer=val.signer,
                foreign_apps=[val_fact_app_id],
                boxes=[(set_noticeboard_client.app_id, "val_list")],
            ),
        )

    assert result.confirmed_round

    return set_noticeboard_client


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


def test_create_validators(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_client: NoticeboardClient,
) -> None:

    val_list = get_val_list(
        algod_client=algorand_client.client.algod,
        noitceboard_app_id=noticeboard_w_validators_client.app_id,
    )

    assert len(val_list) == TestConsts.num_vals


def set_validator_ad(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_client: NoticeboardClient,
    val: AddressAndSigner,
    manager: AddressAndSigner,
) -> NoticeboardClient:

    val_app_id = noticeboard_w_validators_client.get_local_state(val.address).val_app_id

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * sp.min_fee

    result = noticeboard_w_validators_client.set_validator_ad_mandatory(
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
    result = noticeboard_w_validators_client.set_validator_ad_extra(
        val_config_extra=TestConsts.val_config_extra,
        transaction_parameters=OnCompleteCallParameters(
            sender=val.address,
            signer=val.signer,
            foreign_apps=[val_app_id],
            suggested_params=sp,
        ),
    )

    return noticeboard_w_validators_client


def test_set_validator_ads(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> None:

    for idx, val in enumerate(validators):
        assert set_validator_ad(
            algorand_client,
            noticeboard_w_validators_client,
            val,
            validators[(idx + 1) % len(validators)],
        )


def test_end_validator_ad(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> None:

    val = validators[-1]

    val_app_id = noticeboard_w_validators_client.get_local_state(val.address).val_app_id

    val_list_start = get_val_list(
        algod_client=algorand_client.client.algod,
        noitceboard_app_id=noticeboard_w_validators_client.app_id,
    )

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * sp.min_fee

    result = noticeboard_w_validators_client.end_validator_ad(
        transaction_parameters=OnCompleteCallParameters(
            sender=val.address,
            signer=val.signer,
            foreign_apps=[val_app_id],
            boxes=[(noticeboard_w_validators_client.app_id, "val_list")],
            suggested_params=sp,
        ),
    )

    val_list_end = get_val_list(
        algod_client=algorand_client.client.algod,
        noitceboard_app_id=noticeboard_w_validators_client.app_id,
    )

    assert len(val_list_start) - 1 == len(val_list_end)
    assert val_app_id not in val_list_end

    with pytest.raises(AlgodHTTPError, match="application does not exist"):
        algorand_client.client.algod.application_info(application_id=val_app_id)


def test_val_withdraw_earnings(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> None:

    val = validators[0]

    val_app_id = noticeboard_w_validators_client.get_local_state(val.address).val_app_id

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * sp.min_fee

    result = noticeboard_w_validators_client.val_withdraw_earnings(
        transaction_parameters=OnCompleteCallParameters(
            sender=val.address,
            signer=val.signer,
            foreign_apps=[val_app_id],
            suggested_params=sp,
        ),
    )

    assert result.return_value == 0


# ----- ----- ----- --------------------------------- ----- ----- -----
# ----- ----- -----           For all users           ----- ----- -----
# ----- ----- ----- --------------------------------- ----- ----- -----


def test_withdraw_balance(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> None:

    val = validators[0]

    val_app_id = noticeboard_w_validators_client.get_local_state(val.address).val_app_id

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * sp.min_fee

    result = noticeboard_w_validators_client.withdraw_balance(
        transaction_parameters=OnCompleteCallParameters(
            sender=val.address,
            signer=val.signer,
            foreign_apps=[val_app_id],
            suggested_params=sp,
        ),
    )

    assert result.return_value == 0


def test_withdraw_depoist(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> None:
    """
    Note: Test will fail if run individually because validator first has to be freed.
    This is done in the session earlier while deleting the (empty) validator ad.
    """

    val = validators[-1]

    val_app_id = noticeboard_w_validators_client.get_local_state(val.address).val_app_id

    sp = algorand_client.client.algod.suggested_params()
    sp.fee = 2 * sp.min_fee

    result = noticeboard_w_validators_client.withdraw_depoist(
        transaction_parameters=OnCompleteCallParameters(
            sender=val.address,
            signer=val.signer,
            foreign_apps=[val_app_id],
            suggested_params=sp,
        ),
    )

    assert result.return_value == TestConsts.val_min_deposit + 1


def test_user_opt_in(
    algorand_client: AlgorandClient,
    noticeboard_w_validators_client: NoticeboardClient,
    validators: List[AddressAndSigner],
) -> None:

    val = validators[0]

    val_app_id = noticeboard_w_validators_client.get_local_state(val.address).val_app_id

    with pytest.raises(AlgodHTTPError, match="has already opted in to app"):
        result = noticeboard_w_validators_client.opt_in_user_opt_in(
            transaction_parameters=OnCompleteCallParameters(
                sender=val.address,
                signer=val.signer,
            ),
        )
