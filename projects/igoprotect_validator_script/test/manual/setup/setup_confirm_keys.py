"""Helper setup script that confirms partkeys for the selected delegator.
The partkeys have to be already deposited to the delegator application.
"""

from pathlib import Path
import sys
sys.path.append(str(Path(*Path(__file__).parent.parts[:-4])), 'i-go-protect')
sys.path.append(str(Path(*Path(__file__).parent.parts[:-3])))

import base64

from algokit_utils import OnCompleteCallParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algokit_utils.beta.algorand_client import AlgorandClient
from algokit_utils.beta.composer import PayParams
from algokit_utils.config import config
from algosdk import account, mnemonic
from algosdk.atomic_transaction_composer import (
    AtomicTransactionComposer,
    TransactionWithSigner,
)
from algokit_utils.beta.composer import OnlineKeyRegParams
from tests.conftest import TestConsts, decode_val_config_man, progress_rounds
from algosdk.atomic_transaction_composer import AccountTransactionSigner

from smart_contracts.artifacts.delegator_contract.client import (
    DelegatorContractClient,
)

from utils import get_del_state_list
from smart_contracts.artifacts.noticeboard.client import NoticeboardClient



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



if __name__ == "__main__":


    ### Begin: required input ##########################################################################################

    noticeboard_app_id = 1006
    val_app_id = 1018
    del_app_id = 1030

    # Whoever created the delegator app
    del_creator_address = 'GKGLRLE4VEFZLHOBW6NDY4ANKPTSDCCBWKEYHAMTQAG3MI6FFIP6EI7FPY'
    del_creator_pkey = 'zH0ZsSe+g2hu4jhWusKGMff+nTHFBsPrd21soneS5JQyjLisnKkLlZ3Bt5o8cA1T5yGIQbKJg4GTgA22I8UqHw=='


    ### End: required input ############################################################################################


    algorand_client = AlgorandClient.default_local_net()
    algorand_client.set_suggested_params_timeout(0)


    creator = AddressAndSigner(
        address=del_creator_address,
        signer=AccountTransactionSigner(del_creator_pkey)
    )
    algorand_client.set_signer(sender=creator.address, signer=creator.signer)
    algorand_client.send.payment(
        PayParams(
            sender=algorand_client.account.dispenser().address,
            receiver=creator.address,
            amount=TestConsts.acc_dispenser_amt,
        )
    )



    del_app_state = get_del_state_list(
        algorand_client.client.algod,
        [del_app_id]
    )[0]


    noticeboard_client = NoticeboardClient(
        algod_client=algorand_client.client.algod,
        app_id=noticeboard_app_id
    )


    atc = AtomicTransactionComposer()

    # Create key registration transaction
    keyreg_txn = TransactionWithSigner(
        algorand_client.transactions.online_key_reg(
            OnlineKeyRegParams(
                sender=creator.address,
                selection_key=del_app_state.sel_key.as_base64,
                vote_key=del_app_state.vote_key.as_base64,
                state_proof_key=del_app_state.state_proof_key.as_base64,
                vote_key_dilution=del_app_state.vote_key_dilution,
                vote_first=del_app_state.round_start,
                vote_last=del_app_state.round_end,
            )
        ),
        signer=creator.signer,
    )
    atc.add_transaction(keyreg_txn)

    del_config_man = decode_val_config_man(del_app_state.val_config_man.as_bytes)

    sp = algorand_client.client.algod.suggested_params()

    # Create operational fee payment transaction
    fee_operation_pay_txn = TransactionWithSigner(
        algorand_client.transactions.payment(
            PayParams(
                sender=creator.address,
                receiver=noticeboard_client.app_address,
                amount=del_config_man.fee_round * (del_app_state.round_end - del_app_state.round_start),
                extra_fee=4*sp.min_fee,
            )
        ),
        signer=creator.signer,
    )

    noticeboard_client.app_client.compose_call(
        atc,
        "confirm_keys",
        transaction_parameters=OnCompleteCallParameters(
            sender=creator.address,
            signer=creator.signer,
            foreign_apps=[val_app_id, del_app_id],
            suggested_params=sp,
        ),
        keyreg_txn_index=0,
        fee_operation_payment=fee_operation_pay_txn,
    )

    result = noticeboard_client.app_client.execute_atc( atc )

    pass
