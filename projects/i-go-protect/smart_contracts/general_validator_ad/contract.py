# pyright: reportMissingModuleSource=false


from algopy import *
from algopy import (
    Application,
    ARC4Contract,
    Global,
    OnCompleteAction,
    UInt64,
    arc4,
    op,
    subroutine,
    urange,
)

from ..delegator_contract.contract import DelegatorContract
from ..helpers.common import *
from ..helpers.common import (
    MAX_DEL_CNT,
    MBR_DELEGATORCONTRACT_CREATION,
    DelegatorList,
    SelKey,
    StateProofKey,
    Struct3UInt64,
    ValConfigExtra,
    ValConfigMan,
    VoteKey,
    pay_to_acc,
)

# ------- Import manutally DelegatorContract create info -------

DEL_APPROVAL_PROGRAM = b"\x0a\x20\x04\x00\x01\x05\x20\x26\x13\x0e\x76\x61\x6c\x5f\x63\x6f\x6e\x66\x69\x67\x5f\x6d\x61\x6e\x0b\x72\x6f\x75\x6e\x64\x5f\x73\x74\x61\x72\x74\x09\x72\x6f\x75\x6e\x64\x5f\x65\x6e\x64\x11\x63\x6f\x6e\x74\x72\x61\x63\x74\x5f\x62\x72\x65\x61\x63\x68\x65\x64\x04\x15\x1f\x7c\x75\x13\x70\x61\x72\x74\x5f\x6b\x65\x79\x73\x5f\x64\x65\x70\x6f\x73\x69\x74\x65\x64\x0e\x6b\x65\x79\x73\x5f\x63\x6f\x6e\x66\x69\x72\x6d\x65\x64\x07\x64\x65\x6c\x5f\x61\x63\x63\x0a\x76\x61\x6c\x5f\x61\x70\x70\x5f\x69\x64\x11\x6c\x61\x73\x74\x5f\x62\x72\x65\x61\x63\x68\x5f\x72\x6f\x75\x6e\x64\x0a\x6e\x75\x6d\x5f\x62\x72\x65\x61\x63\x68\x11\x76\x6f\x74\x65\x5f\x6b\x65\x79\x5f\x64\x69\x6c\x75\x74\x69\x6f\x6e\x07\x73\x65\x6c\x5f\x6b\x65\x79\x08\x76\x6f\x74\x65\x5f\x6b\x65\x79\x0f\x73\x74\x61\x74\x65\x5f\x70\x72\x6f\x6f\x66\x5f\x6b\x65\x79\x12\x6e\x6f\x74\x69\x63\x65\x62\x6f\x61\x72\x64\x5f\x61\x70\x70\x5f\x69\x64\x10\x76\x61\x6c\x5f\x63\x6f\x6e\x66\x69\x67\x5f\x65\x78\x74\x72\x61\x00\x01\x00\x31\x18\x40\x00\x03\x88\x03\xf7\x80\x04\xa8\xd3\x65\x85\x80\x04\xb5\xb9\xc1\xa0\x80\x04\xbd\x72\x1b\x6e\x80\x04\xf0\x03\xbc\xc9\x80\x04\x26\x64\x3f\x0a\x80\x04\xb6\x81\x7e\xee\x80\x04\x85\x3a\xe7\xbc\x80\x04\x6c\x74\x2f\x6a\x80\x04\xe8\xde\x3a\x63\x80\x04\xee\x25\xaf\x2c\x36\x1a\x00\x8e\x0a\x00\x01\x00\x1a\x00\x29\x00\x38\x00\x5b\x00\x81\x00\x93\x00\xa5\x00\xb7\x00\xc8\x00\x31\x19\x14\x44\x31\x18\x14\x44\x36\x1a\x01\x36\x1a\x02\x36\x1a\x03\x36\x1a\x04\x88\x00\xc1\x23\x43\x31\x19\x14\x44\x31\x18\x44\x36\x1a\x01\x88\x00\xdb\x23\x43\x31\x19\x14\x44\x31\x18\x44\x36\x1a\x01\x88\x00\xe4\x23\x43\x31\x19\x14\x44\x31\x18\x44\x36\x1a\x01\x36\x1a\x02\x36\x1a\x03\x36\x1a\x04\x36\x1a\x05\x36\x1a\x06\x88\x00\xd3\x27\x04\x4c\x50\xb0\x23\x43\x31\x19\x14\x44\x31\x18\x44\x36\x1a\x01\x36\x1a\x02\x36\x1a\x03\x36\x1a\x04\x36\x1a\x05\x36\x1a\x06\x36\x1a\x07\x88\x00\xef\x27\x04\x4c\x50\xb0\x23\x43\x31\x19\x24\x12\x44\x31\x18\x44\x88\x01\x4e\x27\x04\x4c\x50\xb0\x23\x43\x31\x19\x24\x12\x44\x31\x18\x44\x88\x01\x6b\x27\x04\x4c\x50\xb0\x23\x43\x31\x19\x24\x12\x44\x31\x18\x44\x88\x01\x91\x27\x04\x4c\x50\xb0\x23\x43\x31\x19\x14\x44\x31\x18\x44\x88\x02\x0b\x27\x04\x4c\x50\xb0\x23\x43\x31\x19\x14\x44\x31\x18\x44\x88\x02\x95\x27\x04\x4c\x50\xb0\x23\x43\x8a\x04\x00\x27\x07\x8b\xfc\x67\x8b\xfe\x17\x29\x4c\x67\x8b\xff\x17\x2a\x4c\x67\x8b\xfd\x17\x27\x0f\x4c\x67\x27\x08\x32\x0d\x67\x22\x29\x65\x44\x27\x09\x4c\x67\x89\x8a\x01\x00\x88\x00\x06\x44\x28\x8b\xff\x67\x89\x8a\x00\x01\x32\x0d\x22\x27\x08\x65\x44\x12\x89\x8a\x01\x00\x88\xff\xee\x44\x27\x10\x8b\xff\x67\x89\x8a\x06\x01\x88\xff\xe1\x44\x22\x27\x05\x65\x44\x14\x44\x22\x29\x65\x44\x16\x8b\xfe\xa8\x44\x22\x2a\x65\x44\x16\x8b\xff\xa8\x44\x8b\xfd\x17\x27\x0b\x4c\x67\x27\x0c\x8b\xfa\x67\x27\x0d\x8b\xfb\x67\x27\x0e\x8b\xfc\x67\x27\x05\x23\x67\x22\x28\x65\x44\x57\x18\x08\x89\x8a\x07\x01\x88\xff\x9f\x44\x22\x27\x05\x65\x44\x23\x12\x44\x22\x29\x65\x44\x32\x06\x0c\x44\x22\x27\x0c\x65\x44\x8b\xfa\x12\x44\x22\x27\x0d\x65\x44\x8b\xfb\x12\x44\x22\x27\x0e\x65\x44\x8b\xfc\x12\x44\x22\x27\x0b\x65\x44\x16\x8b\xfd\xa8\x44\x22\x29\x65\x44\x16\x8b\xfe\xa8\x44\x22\x2a\x65\x44\x16\x8b\xff\xa8\x44\x22\x28\x65\x44\x57\x20\x08\x17\x22\x2a\x65\x44\x22\x29\x65\x44\x09\x0b\x16\x8b\xf9\xa8\x44\x27\x06\x23\x67\x22\x28\x65\x44\x57\x18\x08\x89\x8a\x00\x01\x88\xff\x2e\x44\x22\x27\x05\x65\x44\x14\x44\x32\x06\x22\x29\x65\x44\x22\x28\x65\x44\x57\x30\x08\x17\x08\x0d\x44\x22\x28\x65\x44\x57\x28\x08\x22\x28\x65\x44\x57\x18\x08\x50\x89\x8a\x00\x01\x88\xfe\xff\x44\x22\x27\x06\x65\x44\x14\x44\x32\x06\x22\x29\x65\x44\x22\x28\x65\x44\x57\x30\x08\x17\x08\x22\x28\x65\x44\x57\x38\x08\x17\x08\x0d\x44\x22\x28\x65\x44\x57\x28\x08\x22\x28\x65\x44\x57\x18\x08\x50\x89\x8a\x00\x01\x27\x11\x47\x04\x88\xfe\xc3\x44\x22\x27\x05\x65\x44\x44\x22\x27\x06\x65\x44\x44\x32\x06\x22\x2a\x65\x44\x0d\x41\x00\x04\x22\x42\x00\x07\x22\x2a\x65\x44\x32\x06\x09\x22\x28\x65\x44\x57\x28\x08\x17\x49\x8c\x00\x22\x28\x65\x44\x57\x20\x08\x17\x4f\x02\x49\x4e\x02\x0b\x8c\x02\x22\x28\x65\x44\x57\x20\x08\x17\x22\x2a\x65\x44\x22\x29\x65\x44\x09\x4f\x02\x09\x0b\x49\x8c\x03\x22\x2b\x65\x44\x4c\x8c\x04\x4c\x8c\x01\x41\x00\x0a\x8b\x03\x8b\x00\x08\x22\x8c\x01\x8c\x04\x8b\x04\x8b\x01\x16\x8b\x02\x16\x4f\x02\x16\x4c\x4f\x02\x4c\x50\x4c\x50\x8c\x00\x89\x8a\x00\x01\x27\x11\x22\x2b\x65\x44\x14\x44\x22\x27\x06\x65\x44\x44\x22\x28\x65\x44\x57\x48\x08\x17\x22\x27\x09\x65\x44\x08\x32\x06\x0c\x44\x22\x28\x65\x44\x57\x10\x08\x22\x27\x07\x65\x44\x73\x00\x44\x16\xa4\x40\x00\x14\x22\x28\x65\x44\x57\x08\x08\x22\x27\x07\x65\x44\x73\x00\x44\x16\xa5\x41\x00\x04\x23\x42\x00\x01\x22\x44\x22\x29\x65\x44\x32\x06\x49\x8c\x00\x0c\x41\x00\x0e\x22\x2a\x65\x44\x8b\x00\x0d\x41\x00\x04\x23\x42\x00\x01\x22\x44\x22\x27\x0a\x65\x44\x23\x08\x27\x0a\x4c\x67\x22\x28\x65\x44\x57\x40\x08\x22\x27\x0a\x65\x44\x16\xa6\x2b\x4c\x67\x27\x09\x32\x06\x67\x22\x2b\x65\x44\x27\x12\x22\x4f\x02\x54\x4c\x89\x8a\x00\x01\x88\xfd\xa1\x44\x22\x2b\x65\x44\x14\x44\x22\x27\x06\x65\x44\x44\x22\x27\x08\x65\x44\x80\x07\x6d\x61\x6e\x61\x67\x65\x72\x65\x44\x31\x00\x4c\x49\x15\x25\x12\x44\x12\x44\x2b\x23\x67\x22\x2b\x65\x44\x27\x12\x22\x4f\x02\x54\x89\x8a\x00\x00\x27\x0f\x22\x67\x27\x08\x22\x67\x27\x07\x32\x03\x67\x28\x80\x58\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x67\x81\x1e\xaf\x81\x46\xaf\x50\x27\x10\x4c\x67\x29\x22\x67\x2a\x22\x67\x27\x0b\x22\x67\x25\xaf\x27\x0c\x4b\x01\x67\x27\x0d\x4c\x67\x81\x40\xaf\x27\x0e\x4c\x67\x27\x05\x22\x67\x27\x06\x22\x67\x27\x0a\x22\x67\x27\x09\x22\x67\x2b\x22\x67\x89"

DEL_CLEAR_PROGRAM = b"\x0a\x81\x01\x43"

DEL_GLOBAL_NUM_BYTES = 6

DEL_GLOBAL_NUM_UINT = 10

DEL_LOCAL_NUM_BYTES = 0

DEL_LOCAL_NUM_UINT = 0

DEL_EXTRA_PAGES = 1


# ------- Smart contract -------
class GeneralValidatorAd(ARC4Contract):
    """
    Ad of an validator to offer node running services to users.
    Users, i.e. delegators, can open requests for the service and conclude an individual contract with this node runner.

    Global state
    ------------
        Configuration parameters
        ------------------------


        Variables
        ---------

    Methods
    -------

    """

    def __init__(self) -> None:
        # Define global state
        self.noticeboard_app_id = UInt64(0)
        self.owner = Global.zero_address
        self.manager = Global.zero_address
        self.val_config_man = ValConfigMan(
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
            arc4.UInt64(0),
        )
        self.val_config_extra = ValConfigExtra(
            ValName.from_bytes(op.bzero(30)),
            ValLink.from_bytes(op.bzero(70)),
        )
        self.val_deposit = UInt64(0)
        self.live = False
        self.del_cnt = UInt64(0)
        self.max_del_cnt = UInt64(MAX_DEL_CNT)
        self.max_max_del_cnt = UInt64(MAX_DEL_CNT)
        self.val_earnings = UInt64(0)
        self.val_earn_factor = UInt64(0)

        # self.del_contracts = arc4.StaticArray[arc4.UInt64, T_LITERAL_MAX_DEL_CNT](arc4.UInt64(0))
        # Couldn't get it to work otherwise
        self.del_contracts = DelegatorList(
            arc4.UInt64(0), arc4.UInt64(0), arc4.UInt64(0), arc4.UInt64(0)
        )

    @arc4.abimethod(create="require")
    def create(
        self,
        owner: arc4.Address,
        noticeboard_app_id: arc4.UInt64,
        val_earn_factor: arc4.UInt64,
        deposit: arc4.UInt64,
    ) -> None:
        self.noticeboard_app_id = noticeboard_app_id.native
        self.val_earn_factor = val_earn_factor.native
        self.owner = owner.native
        self.val_deposit = deposit.native
        return

    @arc4.abimethod()
    def set_mandatory(
        self,
        val_config_man: ValConfigMan,
        live: arc4.Bool,
        manager: arc4.Address,
        max_del_cnt: arc4.UInt64,
    ) -> None:
        assert self.called_by_noticeboard(), "Not called by noticeboard app."

        assert (
            max_del_cnt <= self.max_max_del_cnt
        ), "Requested maximum number of delegators does not fit into reserved memory."
        self.max_del_cnt = max_del_cnt.native

        self.val_config_man = val_config_man.copy()
        self.live = live.native
        self.manager = manager.native

        return

    @arc4.abimethod()
    def set_extra(self, val_config_extra: ValConfigExtra) -> None:
        assert self.called_by_noticeboard(), "Not called by noticeboard app."

        self.val_config_extra = val_config_extra.copy()

        return

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def end_validator_ad(
        self,
    ) -> arc4.UInt64:
        assert self.called_by_noticeboard(), "Not called by noticeboard app."

        assert (
            self.del_list_empty()
        ), "Can't delete validator if it has active delegator contracts."

        # Return values of validator earnings
        return arc4.UInt64(self.val_earnings)

    @arc4.abimethod()
    def withdraw_earnings(
        self,
    ) -> arc4.UInt64:
        assert self.called_by_noticeboard(), "Not called by noticeboard app."

        cur_earnings = self.val_earnings
        self.val_earnings = UInt64(0)

        # Return validator earnings
        return arc4.UInt64(cur_earnings)

    # ----- ----- ----- --------------------------------- ----- ----- -----
    # ----- ----- ----- For delegator contract management ----- ----- -----
    # ----- ----- ----- --------------------------------- ----- ----- -----

    @arc4.abimethod()
    def create_delegator_contract(
        self,
        deposit_payment_amount: arc4.UInt64,
        fee_setup_payment_amount: arc4.UInt64,
        del_acc: arc4.Address,
        round_start: arc4.UInt64,
        round_end: arc4.UInt64,
    ) -> arc4.UInt64:

        assert self.called_by_noticeboard(), "Not called by noticeboard app."
        assert self.live, "Validator is not accepting new delegators."
        assert self.del_cnt + 1 <= self.max_del_cnt, "Validator is full."

        assert round_start < round_end, "Contract end must be after its start."
        assert round_start >= Global.round, "Contract start can't be in the past."
        assert (
            round_start <= Global.round + self.val_config_man.setup_rounds.native
        ), "Contract should start at latest by allowed time for accepting the setup."

        # Assert minimum delegator deposit was paid to the noticeboard (receiver checked in Noticeboard)
        assert (
            deposit_payment_amount == self.val_config_man.deposit.native
        ), "Deposit was insufficient."

        # Assert correct amount of setup fee was paid to the noticeboard (receiver checked in Noticeboard)
        assert (
            fee_setup_payment_amount == self.val_config_man.fee_setup.native
        ), "Setup fee was insufficient."

        # Create DelegatorContract
        app_txn = arc4.abi_call(
            DelegatorContract.create,
            del_acc.copy(),
            arc4.UInt64(Global.caller_application_id),
            round_start,
            round_end,
            approval_program=DEL_APPROVAL_PROGRAM,
            clear_state_program=DEL_CLEAR_PROGRAM,
            global_num_uint=DEL_GLOBAL_NUM_UINT,
            global_num_bytes=DEL_GLOBAL_NUM_BYTES,
            local_num_uint=DEL_LOCAL_NUM_UINT,
            local_num_bytes=DEL_LOCAL_NUM_BYTES,
            extra_program_pages=DEL_EXTRA_PAGES,
            fee=0,
        )

        created_app_id = app_txn.created_app.id

        # Copy current mandatory and extra mandatory contract parameters to created delegator contract
        app_txn = arc4.abi_call(
            DelegatorContract.set_mandatory,
            self.val_config_man.copy(),
            app_id=created_app_id,
            fee=0,
        )

        app_txn = arc4.abi_call(
            DelegatorContract.set_extra,
            self.val_config_extra.copy(),
            app_id=created_app_id,
            fee=0,
        )

        self.add_del_to_list(created_app_id)

        # Return and propagate created UserContract back to Noticeboard's delegator's local storage
        return arc4.UInt64(created_app_id)

    @arc4.abimethod()
    def deposit_keys(
        self,
        caller: Account,
        del_app_id: arc4.UInt64,
        sel_key: SelKey,
        vote_key: VoteKey,
        state_proof_key: StateProofKey,
        vote_key_dilution: arc4.UInt64,
        round_start: arc4.UInt64,
        round_end: arc4.UInt64,
    ) -> arc4.UInt64:

        assert self.called_by_noticeboard(), "Not called by validator app."

        assert caller == arc4.Address(
            self.manager
        ), "Keys weren't deposited by validator manager account."

        fee_setup, app_txn = arc4.abi_call(
            DelegatorContract.deposit_keys,
            sel_key.copy(),
            vote_key.copy(),
            state_proof_key.copy(),
            vote_key_dilution,
            round_start,
            round_end,
            app_id=del_app_id.native,
            fee=0,
        )

        # Assign val_earn_factor of fee_setup to the validator
        earned = self.val_earning(fee_setup.native)
        self.val_earnings += earned

        # Return profit of platform, i.e. setup fee minus earnings of validator due to key deposition
        return arc4.UInt64(fee_setup.native - earned)

    @arc4.abimethod()
    def confirm_keys(
        self,
        del_app_id: arc4.UInt64,
        fee_operation_payment_amount: arc4.UInt64,
        sel_key: SelKey,
        vote_key: VoteKey,
        state_proof_key: StateProofKey,
        vote_key_dilution: arc4.UInt64,
        round_start: arc4.UInt64,
        round_end: arc4.UInt64,
    ) -> arc4.UInt64:

        assert self.called_by_noticeboard(), "Not called by noticeboard app."

        result, app_txn = arc4.abi_call(
            DelegatorContract.confirm_keys,
            fee_operation_payment_amount,
            sel_key.copy(),
            vote_key.copy(),
            state_proof_key.copy(),
            vote_key_dilution,
            round_start,
            round_end,
            app_id=del_app_id.native,
            fee=0,
        )
        fee_setup = result.native

        # Assign val_earn_factor of fee_setup to the validator
        earned = self.val_earning(fee_setup)
        self.val_earnings += earned

        # Return profit of platform, i.e. setup fee minus earnings of validator
        return arc4.UInt64(fee_setup - earned)

    @arc4.abimethod()
    def keys_not_generated(self, del_app_id: arc4.UInt64) -> arc4.UInt64:
        assert self.called_by_noticeboard(), "Not called by noticeboard app."

        result, app_txn = arc4.abi_call(
            DelegatorContract.keys_not_generated,
            app_id=del_app_id.native,
            on_completion=OnCompleteAction.DeleteApplication,
            fee=0,
        )
        deposit = result.a
        fee_setup = result.b

        assert self.remove_del_from_list(del_app_id.native)
        self.return_delegator_contract_mbr()

        # Return values of agreed setup fee
        return fee_setup

    @arc4.abimethod()
    def keys_not_confirmed(
        self,
        del_app_id: arc4.UInt64,
    ) -> arc4.UInt64:
        assert self.called_by_noticeboard(), "Not called by noticeboard app."

        result, app_txn = arc4.abi_call(
            DelegatorContract.keys_not_confirmed,
            app_id=del_app_id.native,
            on_completion=OnCompleteAction.DeleteApplication,
            fee=0,
        )
        deposit = result.a
        fee_setup = result.b

        # Assign val_earn_factor of fee_setup to the validator
        earned = self.val_earning(fee_setup.native)
        self.val_earnings += earned

        assert self.remove_del_from_list(del_app_id.native)
        self.return_delegator_contract_mbr()

        # Return profit of platform, i.e. setup fee minus earnings of validator
        return arc4.UInt64(fee_setup.native - earned)

    @arc4.abimethod()
    def end_delegator_contract(
        self,
        del_app_id: arc4.UInt64,
    ) -> Struct3UInt64:
        assert self.called_by_noticeboard(), "Not called by noticeboard app."

        result, app_txn = arc4.abi_call(
            DelegatorContract.end_contract,
            app_id=del_app_id.native,
            on_completion=OnCompleteAction.DeleteApplication,
            fee=0,
        )
        deposit = result.a
        refund = result.b
        earnings = result.c

        # Assign val_earn_factor of fee_setup to the validator
        earned = self.val_earning(earnings.native)
        self.val_earnings += earned

        assert self.remove_del_from_list(del_app_id.native)
        self.return_delegator_contract_mbr()

        # Return values of deposit, refund amount, and platform profit, i.e. percentage of earnings of validator
        return Struct3UInt64(
            deposit,
            refund,
            arc4.UInt64(earnings.native - earned),
        )

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Internal functions ----- ----- -----
    # ----- ----- ----- ------------------ ----- ----- -----

    @subroutine
    def add_del_to_list(self, del_app_id: UInt64) -> bool:
        # Assign created delegator contract to first free space in the array of delegator contracts
        del_added = False
        for del_idx in urange(MAX_DEL_CNT):
            if self.del_contracts[del_idx] == arc4.UInt64(0):
                self.del_contracts[del_idx] = arc4.UInt64(del_app_id)
                del_added = True
                self.del_cnt += 1
                break

        return del_added

    @subroutine
    def remove_del_from_list(self, del_app_id: UInt64) -> bool:
        """Remove the delegator contract from list of delegator contracts"""
        del_removed = False
        for del_idx in urange(MAX_DEL_CNT):
            if self.del_contracts[del_idx] == arc4.UInt64(del_app_id):
                self.del_contracts[del_idx] = arc4.UInt64(0)
                del_removed = True
                self.del_cnt -= 1
                break

        return del_removed

    @subroutine
    def del_list_empty(self) -> bool:
        """Checks if there are no delegator contracts in the list of delegator contracts."""
        del_empty = True
        for del_idx in urange(MAX_DEL_CNT):
            if self.del_contracts[del_idx] != arc4.UInt64(0):
                del_empty = False
                break

        return del_empty

    @subroutine
    def val_earning(self, total: UInt64) -> UInt64:
        # Below in 10**2 <- the power needs to be the same as in definition of val_earn_factor
        earned = (total * self.val_earn_factor) // 10**2
        return earned

    @subroutine
    def called_by_noticeboard(self) -> bool:
        return Global.caller_application_id == self.noticeboard_app_id

    @subroutine
    def return_delegator_contract_mbr(self) -> None:
        """
        Send to noticeboard the MBR for delegator contract creation.
        To be used after deleting of a delegator contract.
        """

        pay_to_acc(
            UInt64(MBR_DELEGATORCONTRACT_CREATION),
            Application(self.noticeboard_app_id).address,
        )
        return
