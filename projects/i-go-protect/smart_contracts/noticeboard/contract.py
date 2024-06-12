# pyright: reportMissingModuleSource=false

from algopy import *
from algopy import (
    Account,
    Application,
    ARC4Contract,
    Bytes,
    Global,
    LocalState,
    OnCompleteAction,
    TransactionType,
    Txn,
    UInt64,
    arc4,
    gtxn,
    op,
    subroutine,
    urange,
)

from ..general_validator_ad.contract import GeneralValidatorAd
from ..gfactory_validator_ad.contract import GfactoryValidatorAd
from ..helpers.common import *
from ..helpers.common import (
    MAX_VAL_CNT,
    MBR_BOX_VAL_LIST_CREATION,
    MBR_DELEGATORCONTRACT_CREATION,
    MBR_VALIDATORAD_CREATION,
    VAL_LIST,
    VAL_LIST_EL_BYTE_SIZE,
    SelKey,
    StateProofKey,
    ValConfigExtra,
    ValConfigMan,
    VoteKey,
    is_key_dereg,
    pay_to_acc,
    pay_to_sender,
)


# ------- Smart contract -------
class Noticeboard(ARC4Contract):
    """
    Platform for peer-to-peer consensus delegation.
    Node runners, i.e. validators can post ads to offer their services to users.
    Users, i.e. delegators, can open requests for the service and conclude a contract with a node runner.

    Global state
    ------------
        Configuration parameters
        ------------------------
        deposit_val_min : UInt64
            Minimum deposit required to be made by validator to the Noticeboard
        deposit_del_min : UInt64
            Minimum deposit required to be made by delegator to the Noticeboard
        val_earn_factor : UInt64
            Value scaled to (1-0), representing 1 - percentage of fees taken by the platform

        Variables
        ---------
        live : bool
            Whether the contract is live (true) or has ended (false)
        blocked_amt : UInt64
            Balance on the Noticeboard account that can't be withdrawn.
            It is part either of active deposits or not finalized payments.

    Local state
    -----------
        val_app_id : UInt64
            GeneralValidatorAd ID of the asccount - either as owner of validator or selected validator for UserContract
        del_app_id : UInt64
            UserContract ID of the account if the account is user; equals 0 for validator accounts.
        deposit_amt : UInt64
            Amount the account has deposited in the Noticeboard

    Boxes
    -----
        val_list : Box
            {key = val_id, value = [val_app_id: UInt64, prev_val_id: UInt64, next_val_id: UInt64] }

    Methods
    -------

    """

    def __init__(self) -> None:
        # Define global state
        self.deposit_val_min = UInt64(0)
        self.deposit_del_min = UInt64(0)
        self.val_earn_factor = UInt64(0)
        self.val_factory_app_id = UInt64(0)
        self.manager = Global.zero_address

        self.live = False
        self.blocked_amt = UInt64(0)

        # Define local state
        self.val_app_id = LocalState(UInt64)
        self.del_app_id = LocalState(UInt64)
        self.deposit_amt = LocalState(UInt64)
        self.balance = LocalState(UInt64)

    @arc4.abimethod()
    def setup(
        self,
        deposit_val_min: arc4.UInt64,
        deposit_del_min: arc4.UInt64,
        val_earn_factor: arc4.UInt64,
        val_factory_app_id: arc4.UInt64,
        manager: arc4.Address,
        mbr: gtxn.PaymentTransaction,
    ) -> None:
        assert not self.live, "Noticeboard is not yet live."
        assert (
            Txn.sender == Global.creator_address
        ), "Setup can be done only by contract creator."

        assert (
            deposit_del_min.native * MAX_DEL_CNT <= deposit_val_min.native
        ), "Validator's deposit must cover at least each delegator's deposit."

        self.deposit_val_min = deposit_val_min.native
        self.deposit_del_min = deposit_del_min.native

        assert (
            UInt64(0) < val_earn_factor.native < UInt64(100)
        ), "Validator factor can't be larger than 100 or smaller than 0."

        self.val_earn_factor = val_earn_factor.native
        self.val_factory_app_id = val_factory_app_id.native
        self.manager = manager.native

        # Create box for list of validators
        assert op.Box.create(Bytes(VAL_LIST), VAL_LIST_EL_BYTE_SIZE * MAX_VAL_CNT)

        # Assert increase in minimum balance requirement for box for validator list
        assert (
            mbr.receiver == Global.current_application_address
        ), "MBR increase for box of validator list needs to be covered."
        assert mbr.amount == MBR_BOX_VAL_LIST_CREATION

        self.live = True

        return

    # ----- ----- ----- --------------------------------- ----- ----- -----
    # ----- ----- -----    For validator ad management    ----- ----- -----
    # ----- ----- ----- --------------------------------- ----- ----- -----

    @arc4.abimethod()
    def create_validator_ad(
        self,
        deposit: gtxn.PaymentTransaction,
        mbr_factory: gtxn.PaymentTransaction,
        mbr_val: gtxn.PaymentTransaction,
    ) -> None:
        assert self.live, "Noticeboard is live."
        """assert Txn.sender.is_opted_in(
            Global.current_application_id
        ), "Account has already opted-in the app and thus is already either a delegator or a validator."
        """
        # An account can have only one role in the platform - either UserContract or GeneralValidatorAd
        assert self.val_app_id[Txn.sender] == 0, "Account doesn't yet have a role."

        # Assert minimum validator deposit was paid
        assert (
            deposit.receiver == Global.current_application_address
        ), "Validator deposit wasn't made to noticeboard."
        assert (
            deposit.amount >= self.deposit_val_min
        ), "Validator didn't deposit minimum required amount."

        # Mark deposit amount in user's local storage
        self.deposit_amt[Txn.sender] = deposit.amount

        # Create ValdiatorAd
        result, app_txn = arc4.abi_call(
            GfactoryValidatorAd.generate_validator_ad,
            arc4.Address(Txn.sender),
            self.val_earn_factor,
            arc4.UInt64(deposit.amount),
            app_id=self.val_factory_app_id,
            fee=0,
        )
        created_app_id = result.native
        # Store created GeneralValidatorAd ID in validator's local storage
        self.val_app_id[Txn.sender] = created_app_id

        # Add new GeneralValidatorAd to list of validators
        assert val_list_add(created_app_id), "Validator list is full."

        # Assert increase in minimum balance requirement was paid for Noticeboard due to
        # GeneralValidatorAd creation
        assert (
            mbr_factory.receiver == Application(self.val_factory_app_id).address
        ), "MBR increase of factory of validator ads needs to be covered."
        assert mbr_factory.amount == MBR_VALIDATORAD_CREATION

        # Increase blocked balance in Noticeboard
        self.blocked_amt += deposit.amount

        # Assert MBR was paid for validator address, so that notice board can fund it
        assert (
            mbr_val.receiver == Global.current_application_address
        ), "MBR wasn't paid to noticeboard."
        assert mbr_val.amount == UInt64(
            100_000
        ), "Validator didn't deposit minimum required amount to validator ad."

        pay_to_acc(UInt64(100_000), Application(created_app_id).address)

    @arc4.abimethod()
    def set_validator_ad_mandatory(
        self,
        val_config_man: ValConfigMan,
        live: arc4.Bool,
        manager: arc4.Address,
        max_del_cnt: arc4.UInt64,
    ) -> None:
        """Creates or updates mandatory part of validator ad and sets liveliness status"""
        self.deposit_sufficient()

        val_app_id = self.val_app_id[Txn.sender]
        del_app_id = self.del_app_id[Txn.sender]

        assert del_app_id == UInt64(0), "User is not a validator."
        assert val_app_id != UInt64(0), "User doesn't have an active validator ad."

        txn = arc4.abi_call(
            GeneralValidatorAd.set_mandatory,
            val_config_man.copy(),
            live,
            manager.copy(),
            max_del_cnt,
            app_id=val_app_id,
            fee=0,
        )
        return

    @arc4.abimethod()
    def set_validator_ad_extra(self, val_config_extra: ValConfigExtra) -> None:
        """Creates or updates extra part of validator ad"""
        self.deposit_sufficient()

        val_app_id = self.val_app_id[Txn.sender]
        del_app_id = self.del_app_id[Txn.sender]

        assert del_app_id == UInt64(0), "User is not a validator."
        assert val_app_id != UInt64(0), "User doesn't have an active validator ad."

        txn = arc4.abi_call(
            GeneralValidatorAd.set_extra,
            val_config_extra.copy(),
            app_id=val_app_id,
            fee=0,
        )
        return

    @arc4.abimethod()
    def end_validator_ad(
        self,
    ) -> None:
        """Sender can delete the validator ad."""

        val_app_id = self.val_app_id[Txn.sender]
        del_app_id = self.del_app_id[Txn.sender]

        assert del_app_id == UInt64(0), "User is not a validator."
        assert val_app_id != UInt64(0), "User doesn't have an active validator ad."

        result, app_txn = arc4.abi_call(
            GeneralValidatorAd.end_validator_ad,
            app_id=val_app_id,
            on_completion=OnCompleteAction.DeleteApplication,
            fee=0,
        )
        val_earnings = result.native

        # Increase user's, i.e. validators, earnings
        self.balance[Txn.sender] += val_earnings

        # Remove GeneralValidatorAd from list of validators
        assert val_list_remove(val_app_id), "Validator list doesn't include the ad."

        # Free user
        assert self.free_user(Txn.sender), "Couldn't free validator."

        return

    @arc4.abimethod()
    def val_withdraw_earnings(
        self,
    ) -> arc4.UInt64:
        val_app_id = self.val_app_id[Txn.sender]
        del_app_id = self.del_app_id[Txn.sender]

        assert del_app_id == UInt64(0), "User is not a validator."
        assert val_app_id != UInt64(0), "User doesn't have an active validator ad."

        result, app_txn = arc4.abi_call(
            GeneralValidatorAd.withdraw_earnings,
            app_id=val_app_id,
            fee=0,
        )
        earnings = result.native

        # Release blocked balance in Noticeboard for difference between charged fee_setup and earnings of validator,
        # i.e. earnings of the platform
        self.blocked_amt -= earnings

        pay_to_sender(earnings)

        return arc4.UInt64(earnings)

    # ----- ----- ----- --------------------------------- ----- ----- -----
    # ----- ----- -----           For all users           ----- ----- -----
    # ----- ----- ----- --------------------------------- ----- ----- -----
    @arc4.abimethod()
    def withdraw_balance(
        self,
    ) -> arc4.UInt64:

        balance = self.balance[Txn.sender]

        # Release blocked balance in Noticeboard
        self.blocked_amt -= balance

        pay_to_sender(balance)

        # Set new balance to zero
        self.balance[Txn.sender] = UInt64(0)

        return arc4.UInt64(balance)

    @arc4.abimethod()
    def withdraw_depoist(
        self,
    ) -> arc4.UInt64:
        val_app_id = self.val_app_id[Txn.sender]
        del_app_id = self.del_app_id[Txn.sender]

        assert del_app_id == UInt64(0) and val_app_id == UInt64(
            0
        ), "Withdrawal of deposit is only possible if user is neither a validator nor a delegator."

        deposit = self.deposit_amt[Txn.sender]

        # Release blocked balance in Noticeboard for the deposit
        self.blocked_amt -= deposit

        pay_to_sender(deposit)

        # Set new deposit to zero
        self.deposit_amt[Txn.sender] = UInt64(0)

        return arc4.UInt64(deposit)

    @arc4.abimethod(allow_actions=["OptIn"])
    def user_opt_in(
        self,
    ) -> None:
        """
        assert not Txn.sender.is_opted_in(
            Global.current_application_id
        ), "Account has already opted-in the app."
        """

        self.val_app_id[Txn.sender] = UInt64(0)
        self.del_app_id[Txn.sender] = UInt64(0)
        self.deposit_amt[Txn.sender] = UInt64(0)
        self.balance[Txn.sender] = UInt64(0)

        return

    # ----- ----- ----- --------------------------------- ----- ----- -----
    # ----- ----- ----- For delegator contract management ----- ----- -----
    # ----- ----- ----- --------------------------------- ----- ----- -----

    @arc4.abimethod()
    def create_delegator_contract(
        self,
        val_app_id: arc4.UInt64,
        deposit_payment: gtxn.PaymentTransaction,
        fee_setup_payment: gtxn.PaymentTransaction,
        mbr: gtxn.PaymentTransaction,
        round_start: arc4.UInt64,
        round_end: arc4.UInt64,
    ) -> None:
        assert self.live, "Noticeboard is live."
        """
        assert Txn.sender.is_opted_in(
            Global.current_application_id
        ), "Account has already opted-in the app and thus is already either a delegator or a validator."
        """
        assert self.val_app_id[Txn.sender] == 0, "Account doesn't yet have a role."

        # Assert increase in minimum balance requirement was paid for ValdiatorAd due to
        # DelegatorContract creation
        assert (
            mbr.receiver == Application(val_app_id.native).address
        ), "MBR wasn't paid to the valdiator ad."
        assert (
            mbr.amount == MBR_DELEGATORCONTRACT_CREATION
        ), "MBR pay had insufficient amount for creation of new delegator contract."

        # Assert minimum delegator deposit was paid to the noticeboard (amount checked in GeneralValidatorAd)
        assert (
            deposit_payment.receiver == Global.current_application_address
        ), "Deposit wasn't paid to the noticeboard."
        # Assert correct amount of setup fee was paid to the noticeboard (amount checked in GeneralValidatorAd)
        assert (
            fee_setup_payment.receiver == Global.current_application_address
        ), "Setup fee wasn't paid to the noticeboard."

        # Create new delegator contract for the chosen validator
        created_del_app_id, txn = arc4.abi_call(
            GeneralValidatorAd.create_delegator_contract,
            arc4.UInt64(deposit_payment.amount),
            arc4.UInt64(fee_setup_payment.amount),
            arc4.Address(Txn.sender),
            round_start,
            round_end,
            app_id=val_app_id.native,
            fee=0,
        )
        # Store the created delegator contract app ID
        self.del_app_id[Txn.sender] = created_del_app_id.native
        # Store selected validator contract app ID
        self.val_app_id[Txn.sender] = val_app_id.native

        # Mark delegators deposit amount
        self.deposit_amt[Txn.sender] = deposit_payment.amount

        # Increase blocked balance
        self.blocked_amt += (
            deposit_payment.amount + fee_setup_payment.amount + mbr.amount
        )

        return

    @arc4.abimethod()
    def deposit_keys(
        self,
        del_acc: arc4.Address,
        sel_key: SelKey,
        vote_key: VoteKey,
        state_proof_key: StateProofKey,
        vote_key_dilution: arc4.UInt64,
        round_start: arc4.UInt64,
        round_end: arc4.UInt64,
    ) -> None:

        val_app_id = self.val_app_id[del_acc.native]
        del_app_id = self.del_app_id[del_acc.native]

        result, app_txn = arc4.abi_call(
            GeneralValidatorAd.deposit_keys,
            Txn.sender,
            arc4.UInt64(del_app_id),
            sel_key.copy(),
            vote_key.copy(),
            state_proof_key.copy(),
            vote_key_dilution,
            round_start,
            round_end,
            app_id=val_app_id,
            fee=0,
        )
        platform_earning = result.native

        # Release blocked balance in Noticeboard for earning of the platform
        self.blocked_amt -= platform_earning

        return

    @arc4.abimethod()
    def confirm_keys(
        self,
        keyreg_txn_index: arc4.UInt64,
        fee_operation_payment: gtxn.PaymentTransaction,
    ) -> None:

        val_app_id = self.val_app_id[Txn.sender]
        del_app_id = self.del_app_id[Txn.sender]

        assert val_app_id != UInt64(0) and del_app_id != UInt64(
            0
        ), "Sender doesn't have an active delegator contract."

        assert (
            Global.group_size == 3
        ), "Check gtxn size is exactly three - fee payment, app call, and key reg."

        # Assert correct amount of operational fee was paid to the noticeboard (amount checked in DelegatorContract)
        assert (
            fee_operation_payment.receiver == Global.current_application_address
        ), "Setup fee wasn't paid to the noticeboard."

        assert (
            op.GTxn.type_enum(keyreg_txn_index.native)
            == TransactionType.KeyRegistration
        ), "Key reg transaction."

        assert (
            op.GTxn.sender(keyreg_txn_index.native) == Txn.sender
        ), "Key reg is from the same account as the delegator contract."

        sel_key = SelKey.from_bytes(op.GTxn.selection_pk(keyreg_txn_index.native))
        vote_key = VoteKey.from_bytes(op.GTxn.vote_pk(keyreg_txn_index.native))
        state_proof_key = StateProofKey.from_bytes(
            op.GTxn.state_proof_pk(keyreg_txn_index.native)
        )

        vote_key_dilution = op.GTxn.vote_key_dilution(keyreg_txn_index.native)
        round_start = op.GTxn.vote_first(keyreg_txn_index.native)
        round_end = op.GTxn.vote_last(keyreg_txn_index.native)

        result, app_txn = arc4.abi_call(
            GeneralValidatorAd.confirm_keys,
            arc4.UInt64(del_app_id),
            arc4.UInt64(fee_operation_payment.amount),
            sel_key.copy(),
            vote_key.copy(),
            state_proof_key.copy(),
            arc4.UInt64(vote_key_dilution),
            arc4.UInt64(round_start),
            arc4.UInt64(round_end),
            app_id=val_app_id,
            fee=0,
        )
        platform_earning = result.native

        # Release blocked balance in Noticeboard for earning of the platform
        self.blocked_amt -= platform_earning

        # Increase blocked balance for opertional fee
        self.blocked_amt += fee_operation_payment.amount

        return

    @arc4.abimethod()
    def keys_not_generated(
        self,
        del_acc: arc4.Address,
    ) -> None:

        val_app_id = self.val_app_id[del_acc.native]
        del_app_id = self.del_app_id[del_acc.native]

        assert val_app_id != UInt64(0) and del_app_id != UInt64(
            0
        ), "Sender doesn't have an active delegator contract."

        result, app_txn = arc4.abi_call(
            GeneralValidatorAd.keys_not_generated,
            arc4.UInt64(del_app_id),
            app_id=val_app_id,
            fee=0,
        )
        fee_setup = result.native

        # Refund setup fee to delegator's balance
        self.balance[del_acc.native] += fee_setup

        # Free user
        assert self.free_user(Txn.sender), "Couldn't free delegator."

        return

    @arc4.abimethod()
    def keys_not_confirmed(
        self,
        del_acc: arc4.Address,
    ) -> None:

        val_app_id = self.val_app_id[del_acc.native]
        del_app_id = self.del_app_id[del_acc.native]

        assert val_app_id != UInt64(0) and del_app_id != UInt64(
            0
        ), "Account doesn't have an active delegator contract."

        result, app_txn = arc4.abi_call(
            GeneralValidatorAd.keys_not_confirmed,
            arc4.UInt64(del_app_id),
            app_id=val_app_id,
            fee=0,
        )
        platform_earning = result.native

        # Release blocked balance in Noticeboard for earnings of the platform
        self.blocked_amt -= platform_earning

        # Free user
        assert self.free_user(del_acc.native), "Couldn't free delegator."

        return

    @arc4.abimethod()
    def end_expired_or_breached_delegator_contract(
        self,
        del_acc: arc4.Address,
    ) -> None:
        """Anyone can delete the delegator contract after its expiry or when it was breached."""

        val_app_id = self.val_app_id[del_acc.native]
        del_app_id = self.del_app_id[del_acc.native]

        assert val_app_id != UInt64(0) and del_app_id != UInt64(
            0
        ), "Account doesn't have an active delegator contract."

        # Read global state of delegator contract
        del_end_round, del_end_round_exist = op.AppGlobal.get_ex_uint64(
            del_app_id, Bytes(b"round_end")
        )
        assert del_end_round_exist, "Delegator contract has round_end."
        del_contract_breached, del_contract_breached_exist = op.AppGlobal.get_ex_uint64(
            del_app_id, Bytes(b"contract_breached")
        )
        assert del_contract_breached_exist, "Delegator contract has contract_breached."

        assert (
            del_end_round < Global.round or del_contract_breached
        ), "Anyone can end contract if it has expired already or was breached."

        self.end_delegator_contract(del_app_id, val_app_id, del_acc.native)

        return

    @arc4.abimethod()
    def end_active_delegator_contract(
        self,
        keyreg_txn_index: arc4.UInt64,
    ) -> None:
        """Delegator can withdraw from contract and get refunded remaining operational fee."""

        val_app_id = self.val_app_id[Txn.sender]
        del_app_id = self.del_app_id[Txn.sender]

        assert val_app_id != UInt64(0) and del_app_id != UInt64(
            0
        ), "Sender doesn't have an active delegator contract."

        assert (
            Global.group_size == 2
        ), "Check gtxn size is exactly two - app call, and key dereg."

        assert (
            op.GTxn.sender(keyreg_txn_index.native) == Txn.sender
        ), "Key (de)reg is from the same account as the delegator contract."

        assert is_key_dereg(keyreg_txn_index.native), "Transaction is not key dereg."

        self.end_delegator_contract(del_app_id, val_app_id, Txn.sender)

        return

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Internal functions ----- ----- -----
    # ----- ----- ----- ------------------ ----- ----- -----
    @subroutine
    def end_delegator_contract(
        self,
        del_app_id: UInt64,
        val_app_id: UInt64,
        acc: Account,
    ) -> None:
        """
        Issue end_delegator_contract transaction to ValidatorAd and
        manage platfrom earnings, delegator deposit, and delegator balance.
        """
        result, app_txn = arc4.abi_call(
            GeneralValidatorAd.end_delegator_contract,
            arc4.UInt64(del_app_id),
            app_id=val_app_id,
            fee=0,
        )
        deposit = result.a
        refund = result.b
        platform_earning = result.c

        # Release blocked balance in Noticeboard for earnings of the platform
        self.blocked_amt -= platform_earning.native

        # Return refund unused operational fee to delegator's balance
        self.balance[acc] += refund.native

        # Set deposit to delegator's local state - because it could have been siezed due to breaches
        self.deposit_amt[acc] = deposit.native

        # Free user
        assert self.free_user(acc), "Couldn't free delegator."

        return

    @subroutine
    def free_user(self, user_acc: Account) -> bool:
        self.val_app_id[user_acc] = UInt64(0)
        self.del_app_id[user_acc] = UInt64(0)
        return True

    # ----- Check if below is needed at all ------
    @subroutine
    def deposit_sufficient(self) -> None:
        assert (
            self.deposit_amt[Txn.sender] > self.deposit_val_min
        ), "Action blocked due to insufficient deposit"


# ------- Subroutine utils -------
@subroutine
def val_list_add(val_app_id: UInt64) -> bool:
    """
    Add element to list of validators.

    Arguments
    ---------
    val_app_id : UInt64
        New GeneralValidatorAd app ID to add to the list

    Returns
    -------
    none
    """

    # Get box with validator list
    val_list_box, box_get = op.Box.get(Bytes(VAL_LIST))
    assert box_get, "Got box"
    val_list = ValidatorList.from_bytes(val_list_box)

    # Add it to the first non-zero place
    val_added = False
    for val_idx in urange(MAX_VAL_CNT):
        if val_list[val_idx] == arc4.UInt64(0):
            val_list[val_idx] = arc4.UInt64(val_app_id)
            val_added = True
            break

    op.Box.put(Bytes(VAL_LIST), val_list.bytes)

    return val_added


@subroutine
def val_list_remove(val_app_id: UInt64) -> bool:
    """
    Remove validator ad from list of validators.

    Arguments
    ---------
    val_app_id : UInt64
        GeneralValidatorAd app ID to remove from the list

    Returns
    -------
    none
    """

    # Get box with validator list
    val_list_box, box_get = op.Box.get(Bytes(VAL_LIST))
    assert box_get, "Got box"
    val_list = ValidatorList.from_bytes(val_list_box)

    # Remove the element
    val_remove = False
    for val_idx in urange(MAX_VAL_CNT):
        if val_list[val_idx] == arc4.UInt64(val_app_id):
            val_list[val_idx] = arc4.UInt64(0)
            val_remove = True
            break

    op.Box.put(Bytes(VAL_LIST), val_list.bytes)

    return val_remove


@subroutine
def called_by_contract_creator() -> bool:
    return Txn.sender == Global.creator_address
