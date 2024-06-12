from pathlib import Path
import sys
sys.path.append(str(Path(*Path(__file__).parent.parts[:-1])))

import base64
from math import sqrt
 
from algokit_utils import (
    TransactionParameters,
)
from algokit_utils.beta.algorand_client import *
from algosdk import abi
 
from smart_contracts.artifacts.delegator_contract.client import (
    DelegatorContractClient,
)
from smart_contracts.artifacts.noticeboard.client import NoticeboardClient
 

from algosdk.atomic_transaction_composer import AccountTransactionSigner
from algokit_utils.beta.account_manager import AddressAndSigner

 
class TestConsts:
    sel_key = "02fNSBz3ll5PlN8QsfPfizabhv/zdn6mZIqd2VUvVUc="
    vote_key = "/IrjsljyVGSMmwbGyQCazJN+LImHtjxmP8fiTq83vbA="
    state_proof_key = "y2chLKRDH4H74lREfGWVUpUuvECXH7TzkkhDa/4G+DUg2qTLJijmye2W0pJK2A23DXuA7m9QVVQvbNFhQpAixQ=="
 
 
algorand_client = AlgorandClient.default_local_net()
algorand_client.set_suggested_params_timeout(0)

noticeboard_id = 1006
del_app_id = 1030
# manager = algorand_client.account.from_kmd(
#     "unencrypted-default-wallet",
#     lambda a: a["address"]
#     == "P3ZEO3CSQGR35O2A6QDVTAWCV2MJJRYOWCNT52CPIWCKEXC3MOGKQDU27E",
# )

manager_address='V63CU7LIOOJ53LWK7V5EAUZ3F5Y3F737AGJJSXUSZJVPMAGAJFVLJZOWCY'
manager_signer=AccountTransactionSigner(
    'ds9eqoqfoswV9NVi4LLTiNPfjZ6M6NuraVrCg1/8AKmvtip9aHOT3a7K/XpAUzsvcbL/fwGSmV6Symr2AMBJag=='
)
manager = AddressAndSigner(
    address=manager_address,
    signer=manager_signer
)
algorand_client.set_signer(
    sender=manager.address, 
    signer=manager.signer
)
 
print(manager.address)
 
noticeboard = NoticeboardClient(
    algod_client=algorand_client.client.algod,
    app_id=noticeboard_id,
)
 
# Select one delegator contracts
del_client = DelegatorContractClient(
    algod_client=algorand_client.client.algod,
    app_id=del_app_id,
)
# Get owner of the contract
del_app_global = del_client.get_global_state()
val_app_id = del_app_global.val_app_id
delegator = abi.AddressType().decode(del_app_global.del_acc.as_bytes)
round_start = del_app_global.round_start
round_end = del_app_global.round_end
 
# Get suggested params
sp = algorand_client.client.algod.suggested_params()
sp.fee = 3 * sp.min_fee
 
result = noticeboard.deposit_keys(
    del_acc=delegator,
    sel_key=base64.b64decode(TestConsts.sel_key),
    vote_key=base64.b64decode(TestConsts.vote_key),
    state_proof_key=base64.b64decode(TestConsts.state_proof_key),
    vote_key_dilution=round(sqrt(round_end - round_start)),
    round_start=round_start,
    round_end=round_end,
    transaction_parameters=TransactionParameters(
        sender=manager.address,
        signer=manager.signer,
        foreign_apps=[val_app_id, del_app_id],
        accounts=[delegator],
        suggested_params=sp,
    ),
)

pass
