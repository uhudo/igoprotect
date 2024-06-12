from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import *
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algosdk import mnemonic, account

NUM_ROUNDS = 400


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
 
        print(f"Transaction sent with txID: {res.tx_ids}")
 
    return


algorand_client = AlgorandClient.default_local_net()
algorand_client.set_suggested_params_timeout(0)


manager_mnemonic_str = 'pony trust lottery inject retire bind wood wagon absurd bubble south coach ' + \
    'diet swift ring churn runway evoke science boost inch pledge select abandon crucial'
manager_private_key = mnemonic.to_private_key(manager_mnemonic_str)
manager_address = account.address_from_private_key(manager_private_key)
creator = AddressAndSigner(
    address=manager_address,
    signer=AccountTransactionSigner(manager_private_key)
)
algorand_client.set_signer(sender=creator.address, signer=creator.signer)

progress_rounds(
    algorand_client,
    creator,
    NUM_ROUNDS,
)
