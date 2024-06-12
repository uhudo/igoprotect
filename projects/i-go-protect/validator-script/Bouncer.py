from algokit_utils import TransactionParameters
from algokit_utils.beta.account_manager import AddressAndSigner
from algosdk.transaction import SuggestedParams

from DelegatorContractClient import GlobalState
from utils import decode_val_config_man



class Bouncer(object):


    def __init__(
        self,
        suggested_params: SuggestedParams
    ) -> None:
        self.suggested_params = suggested_params


    @staticmethod
    def has_del_app_partkey_confirmation_time_elapsed(
        current_round: int,
        del_app_state: GlobalState
    ) -> bool:
        del_app_config_man = decode_val_config_man(
            del_app_state.val_config_man.as_bytes
        )
        deadline = \
            del_app_state.round_start + \
            del_app_config_man.setup_rounds + \
            del_app_config_man.confirmation_rounds
        return current_round > deadline


    @staticmethod
    def has_del_app_expired(
        current_round: int,
        del_app_state: GlobalState
    ) -> bool:
        deadline = del_app_state.round_end
        return current_round > deadline


    @staticmethod
    def has_del_indefinitely_breached_terms(
        current_round: int,
        del_app_state: GlobalState
    ) -> bool:
        return False


    def end_del_app_due_to_unconfirmed_keys(
        self,
        del_acc: str,
        del_app_id: int,
        val_app_id: int,
        manager: AddressAndSigner,
        noticeboard_client
    ) -> None:
        result = noticeboard_client.keys_not_confirmed(
            del_acc=del_acc,
            transaction_parameters=TransactionParameters(
                sender=manager.address,
                signer=manager.signer,
                foreign_apps=[val_app_id, del_app_id],
                accounts=[del_acc],
                suggested_params=self.suggested_params
            ),
        )
        assert(result)


    def end_del_app_due_to_expiry(
        self,
        del_acc: str,
        del_app_id: int,
        val_app_id: int,
        manager: AddressAndSigner,
        noticeboard_client
    ) -> None:
        result = noticeboard_client.end_expired_or_breached_delegator_contract(
            del_acc=del_acc,
            transaction_parameters=TransactionParameters(
                sender=manager.address,
                signer=manager.signer,
                foreign_apps=[val_app_id, del_app_id],
                accounts=[del_acc],
                suggested_params=self.suggested_params
            ),
        )
        assert(result)
