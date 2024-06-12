from pathlib import Path
import sys
sys.path.append(str(Path(*Path(__file__).parent.parts[:-2])))
sys.path.append(str(Path(*Path(__file__).parent.parts[:-3])))

import base64
from typing import List

import algokit_utils
from algosdk.v2client import algod
from algosdk import account, mnemonic
from algokit_utils import LogicError, OnCompleteCallParameters, TransactionParameters
from algokit_utils.config import config
from algokit_utils.beta.composer import OnlineKeyRegParams, PayParams
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.account_manager import AddressAndSigner
from smart_contracts.artifacts.gfactory_validator_ad.client import (
    GfactoryValidatorAdClient,
)
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.atomic_transaction_composer import AccountTransactionSigner, TransactionSigner

from smart_contracts.artifacts.general_validator_ad.client import GeneralValidatorAdClient
from smart_contracts.artifacts.noticeboard.client import NoticeboardClient
from tests.conftest import (
    TestConsts,
    decode_uint64_list,
    decode_val_config_man,
    progress_rounds,
)



def create_validator_list(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    num_of_validators
) -> List[AddressAndSigner]:
    return create_account_list( algorand_client, dispenser, num_of_validators )


def create_delegator_list(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    num_of_validators
) -> List[AddressAndSigner]:
    return create_account_list( algorand_client, dispenser, num_of_validators )


def create_account_list(
    algorand_client: AlgorandClient,
    dispenser: AddressAndSigner,
    num_of_validators
) -> List[AddressAndSigner]:
    accs = []
    for i in range(num_of_validators):
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

        ## Ustvari transakcijo na validatorju
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
        val_config_man=TestConsts.val_config_man, # Read in data `from conftest.py`
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



def noticeboard_client(
    algorand_client: AlgorandClient,
    creator: AddressAndSigner,
    validators: List[AddressAndSigner], # Naslov denarnice in private key
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

    client.create_bare() ## Do tukaj naredi contract

    ## Tukaj se doda (poslje) minimal balance na smart contract
    # Needs to be funded with account MBR to be able to set (and create box later during setup)
    algokit_utils.ensure_funded(
        algorand_client.client.algod,
        algokit_utils.EnsureBalanceParameters(
            account_to_fund=client.app_address,
            min_spending_balance_micro_algos=0,
        ),
    )

    client = set_noticeboard_client( ## Konfiguracija notice boarda
        algorand_client,
        client,
        creator,
    )

    client = create_validators( ## 
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



def fund_account(sender, receiver, amount):
    algorand_client.send.payment(
        PayParams(
            sender=sender.address,
            receiver=receiver.address,
            amount=amount,
        )
    )


def make_creator(
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



if __name__ == '__main__':
    
    # creator = AddressAndSigner(
    #     # address='V63CU7LIOOJ53LWK7V5EAUZ3F5Y3F737AGJJSXUSZJVPMAGAJFVLJZOWCY',
    #     # signer=AccountTransactionSigner('ds9eqoqfoswV9NVi4LLTiNPfjZ6M6NuraVrCg1/8AKmvtip9aHOT3a7K/XpAUzsvcbL/fwGSmV6Symr2AMBJag==')
    #     # address='V63CU7LIOOJ53LWK7V5EAUZ3F5Y3F737AGJJSXUSZJVPMAGAJFVLJZOWCY',
    #     # signer=AccountTransactionSigner('ds9eqoqfoswV9NVi4LLTiNPfjZ6M6NuraVrCg1/8AKmvtip9aHOT3a7K/XpAUzsvcbL/fwGSmV6Symr2AMBJag==')
    #     address='V63CU7LIOOJ53LWK7V5EAUZ3F5Y3F737AGJJSXUSZJVPMAGAJFVLJZOWCY',
    #     signer=AccountTransactionSigner('ds9eqoqfoswV9NVi4LLTiNPfjZ6M6NuraVrCg1/8AKmvtip9aHOT3a7K/XpAUzsvcbL/fwGSmV6Symr2AMBJag==')
    # )


    algorand_client = AlgorandClient.default_local_net()
    algorand_client.set_suggested_params_timeout(0)


    manager_mnemonic_str = 'pony trust lottery inject retire bind wood wagon absurd bubble south coach ' + \
        'diet swift ring churn runway evoke science boost inch pledge select abandon crucial'
    manager_private_key = mnemonic.to_private_key(manager_mnemonic_str)
    manager_address = account.address_from_private_key(manager_private_key)

    # manager_private_key='V63CU7LIOOJ53LWK7V5EAUZ3F5Y3F737AGJJSXUSZJVPMAGAJFVLJZOWCY',
    # manager_address='ds9eqoqfoswV9NVi4LLTiNPfjZ6M6NuraVrCg1/8AKmvtip9aHOT3a7K/XpAUzsvcbL/fwGSmV6Symr2AMBJag=='

    creator = AddressAndSigner(
        address=manager_address,
        signer=AccountTransactionSigner(manager_private_key)
    )
    algorand_client.set_signer(sender=creator.address, signer=creator.signer)
    
    algorand_client.send.payment(
        PayParams(
            sender=algorand_client.account.dispenser().address,
            receiver=creator.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )

    # algorand_client = AlgorandClient.default_local_net()

    # creator = make_creator(
    #     algorand_client,
    #     algorand_client.account.dispenser()
    # )

    algorand_client.send.payment(
        PayParams(
            sender=creator.address,
            receiver=creator.address,
            amount=0,
        )
    )

    fund_account(
        algorand_client.account.dispenser(),
        creator,
        TestConsts.acc_dispenser_amt
    )

    # validator_list = create_validator_list(
    #     algorand_client,
    #     algorand_client.account.dispenser(),
    #     1
    # )
    validator_list = [creator]

    delegator_list = create_delegator_list(
        algorand_client,
        algorand_client.account.dispenser(),
        2
    )

    print()
    for i, _delegator in enumerate(delegator_list):
        print(f'Delegator {i} has got:')
        print(f'\tAddress: {_delegator.address}')
        print(f'\tPr. key: {_delegator.signer.private_key}')
    print()

    # validators = [AddressAndSigner(
    #     address='V63CU7LIOOJ53LWK7V5EAUZ3F5Y3F737AGJJSXUSZJVPMAGAJFVLJZOWCY',
    #     signer=AccountTransactionSigner('ds9eqoqfoswV9NVi4LLTiNPfjZ6M6NuraVrCg1/8AKmvtip9aHOT3a7K/XpAUzsvcbL/fwGSmV6Symr2AMBJag==')
    # )]

    nbrd_client = noticeboard_client(
        algorand_client,
        creator,
        validator_list
    )

    noticeboard_w_validators_and_delegators_client(
        algorand_client,
        nbrd_client,
        delegator_list,
    )
 
    pass
