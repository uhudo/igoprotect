import algokit_utils
import pytest
from algokit_utils import OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.config import config
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.transaction import OnComplete
from conftest import TestConsts

from smart_contracts.artifacts.gfactory_validator_ad.client import (
    GfactoryValidatorAdClient,
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


def test_factory_generate_validator_ad(
    algorand_client: AlgorandClient,
    validator_factory_client: GfactoryValidatorAdClient,
    creator: AddressAndSigner,
) -> None:

    mbr_txn = TransactionWithSigner(
        algorand_client.transactions.payment(
            PayParams(
                sender=creator.address,
                receiver=validator_factory_client.app_address,
                amount=TestConsts.mbr_validatorad_creation,
                extra_fee=2 * 1_000_00,
            )
        ),
        signer=creator.signer,
    )

    # Send the transaction
    atc = AtomicTransactionComposer()
    atc.add_transaction(mbr_txn)

    validator_factory_client.app_client.compose_call(
        atc,
        "generate_validator_ad",
        transaction_parameters=OnCompleteCallParameters(
            sender=creator.address,
            signer=creator.signer,
            on_complete=OnComplete.NoOpOC,
        ),
        owner=creator.address,
        val_earn_factor=TestConsts.val_earn_factor,
        deposit=TestConsts.del_min_deposit,
    )

    res = atc.execute(algorand_client.client.algod, 4)
    print(f"Transaction sent with txID: {res.tx_ids}")

    assert res.confirmed_round
