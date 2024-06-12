import logging
from dataclasses import dataclass
from decimal import getcontext

# Set the precision to accommodate 16 digits before the decimal point and 2 digits after
getcontext().prec = 2

import algokit_utils
from algokit_utils import TransactionParameters
from algosdk.atomic_transaction_composer import (
    TransactionWithSigner,
)
from algosdk.transaction import PaymentTxn
from algosdk.v2client.algod import AlgodClient
from algosdk.v2client.indexer import IndexerClient

logger = logging.getLogger(__name__)

PATH_TO_FRONTEND = "../frontend/src/noticeboardAppID.tsx"


@dataclass
class DeployConst:
    mbr_box_val_list_creation: int = 325_700
    del_min_deposit: int = 100_000
    val_min_deposit: int = 400_000
    val_earn_factor: int = 33


# define deployment behaviour based on supplied app spec
def deploy(
    algod_client: AlgodClient,
    indexer_client: IndexerClient,
    app_spec: algokit_utils.ApplicationSpecification,
    deployer: algokit_utils.Account,
) -> None:
    from smart_contracts.artifacts.gfactory_validator_ad.client import (
        GfactoryValidatorAdClient,
    )
    from smart_contracts.artifacts.noticeboard.client import (
        NoticeboardClient,
    )

    print("----- Deploying noticeboard... -----\n")
    # Deploy factory for validator ads
    validator_factory_client = GfactoryValidatorAdClient(
        algod_client=algod_client,
        creator=deployer.address,
        signer=deployer.signer,
        indexer_client=indexer_client,
    )

    validator_factory_client.create_bare()

    print(
        f"Created validator ad factory with app ID: {validator_factory_client.app_id}\n"
    )

    # Needs to be funded with account MBR to be able to create validator ads later
    algokit_utils.ensure_funded(
        algod_client,
        algokit_utils.EnsureBalanceParameters(
            account_to_fund=validator_factory_client.app_address,
            min_spending_balance_micro_algos=0,
        ),
    )
    print("Funded factory with MBR.\n")

    # Deploy noticeboard
    client = NoticeboardClient(
        algod_client=algod_client,
        creator=deployer.address,
        signer=deployer.signer,
        indexer_client=indexer_client,
    )

    client.create_bare()

    print(f"Created noticeboard with app ID: {client.app_id}\n")

    with open(PATH_TO_FRONTEND, "w") as file:
        file.write(f"export const noticeboardAppID = {client.app_id}")

    # Needs to be funded with account MBR to be able to set (and create box later during setup)
    algokit_utils.ensure_funded(
        algod_client,
        algokit_utils.EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=0,
        ),
    )
    print("Funded noticeboard with MBR.\n")

    # Setup noticeboard
    sp = algod_client.suggested_params()
    # MBR for validator list box creation in noticeboard
    mbr_txn = TransactionWithSigner(
        txn=PaymentTxn(  # type: ignore
            sender=deployer.address,
            sp=sp,
            receiver=client.app_address,
            amt=DeployConst.mbr_box_val_list_creation,
        ),
        signer=deployer.signer,
    )

    # Setup noticeboard
    result = client.setup(
        deposit_del_min=DeployConst.del_min_deposit,
        deposit_val_min=DeployConst.val_min_deposit,
        val_earn_factor=DeployConst.val_earn_factor,
        val_factory_app_id=validator_factory_client.app_id,
        manager=deployer.address,
        mbr=mbr_txn,
        transaction_parameters=TransactionParameters(
            sender=deployer.address,
            signer=deployer.signer,
            boxes=[(client.app_id, "val_list")],
        ),
    )
