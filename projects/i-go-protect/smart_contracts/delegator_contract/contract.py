# pyright: reportMissingModuleSource=false
from algopy import *
from algopy import (
    Account,
    ARC4Contract,
    Bytes,
    Global,
    Txn,
    UInt64,
    arc4,
    op,
    subroutine,
)

from ..helpers.common import *
from ..helpers.common import (
    SelKey,
    StateProofKey,
    Struct2UInt64,
    Struct3UInt64,
    ValConfigExtra,
    ValConfigMan,
    VoteKey,
)


# ------- Smart contract -------
class DelegatorContract(ARC4Contract):
    """
    Contract between a user, i.e. delegator, and node runner, i.e. valdiator, for the latter to participate in consensus
    on the behalf of the user for specific amount of time and for a specific fee.
    The contract terms are defined in this contract.

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
        self.val_app_id = UInt64(0)
        self.del_acc = Global.zero_address
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
        self.round_start = UInt64(0)
        self.round_end = UInt64(0)
        self.vote_key_dilution = UInt64(0)
        self.sel_key = SelKey.from_bytes(op.bzero(32))
        self.vote_key = VoteKey.from_bytes(op.bzero(32))
        self.state_proof_key = StateProofKey.from_bytes(op.bzero(64))

        self.part_keys_deposited = False
        self.keys_confirmed = False

        self.num_breach = UInt64(0)
        self.last_breach_round = UInt64(0)
        self.contract_breached = False

    @arc4.abimethod(create="require")
    def create(
        self,
        del_acc: arc4.Address,
        noticeboard_app_id: arc4.UInt64,
        round_start: arc4.UInt64,
        round_end: arc4.UInt64,
    ) -> None:

        # Set global variables
        self.del_acc = del_acc.native
        self.round_start = round_start.native
        self.round_end = round_end.native
        self.noticeboard_app_id = noticeboard_app_id.native
        self.val_app_id = Global.caller_application_id

        self.last_breach_round = self.round_start
        return

    @arc4.abimethod()
    def set_mandatory(self, val_config_man: ValConfigMan) -> None:
        assert self.called_by_validator_ad(), "Not called by validator app."
        self.val_config_man = val_config_man.copy()
        return

    @arc4.abimethod()
    def set_extra(self, val_config_extra: ValConfigExtra) -> None:
        assert self.called_by_validator_ad(), "Not called by validator app."
        self.val_config_extra = val_config_extra.copy()
        return

    @arc4.abimethod()
    def deposit_keys(
        self,
        sel_key: SelKey,
        vote_key: VoteKey,
        state_proof_key: StateProofKey,
        vote_key_dilution: arc4.UInt64,
        round_start: arc4.UInt64,
        round_end: arc4.UInt64,
    ) -> arc4.UInt64:

        assert self.called_by_validator_ad(), "Not called by validator app."
        assert self.part_keys_deposited == False, "Keys can be set only once."

        assert self.round_start == round_start, "Start round isn't as agreed."
        assert self.round_end == round_end, "End round isn't as agreed."

        self.vote_key_dilution = vote_key_dilution.native
        self.sel_key = sel_key.copy()
        self.vote_key = vote_key.copy()
        self.state_proof_key = state_proof_key.copy()

        self.part_keys_deposited = True

        # Return the agreed fee for setting up the validator
        return self.val_config_man.fee_setup

    @arc4.abimethod()
    def confirm_keys(
        self,
        fee_operation_payment_amount: arc4.UInt64,
        sel_key: SelKey,
        vote_key: VoteKey,
        state_proof_key: StateProofKey,
        vote_key_dilution: arc4.UInt64,
        round_start: arc4.UInt64,
        round_end: arc4.UInt64,
    ) -> arc4.UInt64:

        assert self.called_by_validator_ad(), "Not called by validator app."

        assert (
            self.part_keys_deposited == True
        ), "Keys can't be accepted if they haven't been deposited."

        assert (
            self.round_start < Global.round
        ), "Keys can't be confirmed for future (requirement of consensus protocol)."

        # Check if key reg parameters are the same as were deposited
        assert sel_key == self.sel_key, "Selection key"
        assert vote_key == self.vote_key, "Vote key"
        assert state_proof_key == self.state_proof_key, "State proof key"
        assert vote_key_dilution == self.vote_key_dilution, "Vote key dilution"
        assert round_start == self.round_start, "Round start"
        assert round_end == self.round_end, "Round end"

        # Assert correct amount of operational fee was paid to the noticeboard (receiver checked in Noticeboard)
        assert fee_operation_payment_amount == self.val_config_man.fee_round.native * (
            self.round_end - self.round_start
        ), "Operational fee was insufficient."

        self.keys_confirmed = True

        # Return earned agreed setup fee
        return self.val_config_man.fee_setup

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def keys_not_generated(self) -> Struct2UInt64:
        assert self.called_by_validator_ad(), "Not called by validator app."

        assert not self.part_keys_deposited, "Keys were deposited."

        assert (
            Global.round > self.round_start + self.val_config_man.setup_rounds.native
        ), "Only if enough time has passed since contract start, can it be claimed that keys haven't been generated."

        # Return agreed deposit and setup fee
        return Struct2UInt64(
            self.val_config_man.deposit,
            self.val_config_man.fee_setup,
        )

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def keys_not_confirmed(self) -> Struct2UInt64:
        assert self.called_by_validator_ad(), "Not called by validator app."

        assert not self.keys_confirmed, "Keys haven't been confirmed."

        assert (
            Global.round
            > self.round_start
            + self.val_config_man.setup_rounds.native
            + self.val_config_man.confirmation_rounds.native
        ), "Only if enough time has passed since contract start, can it be claimed that keys haven't been confirmed."

        # Return agreed deposit and setup fee
        return Struct2UInt64(
            self.val_config_man.deposit,
            self.val_config_man.fee_setup,
        )

    @arc4.abimethod(allow_actions=["DeleteApplication"])
    def end_contract(self) -> Struct3UInt64:
        assert self.called_by_validator_ad(), "Not called by validator app."

        assert (
            self.part_keys_deposited
        ), "Can't end contract this way if keys haven't yet been deposited."

        assert self.keys_confirmed, "Can't end contract if keys haven't been confirmed."

        # Calculate any refund amount and validator earnings
        if Global.round > self.round_end:
            # Contract has successfully ended
            rounds_remain = UInt64(0)
        else:
            # Contract has prematurely ended
            rounds_remain = self.round_end - Global.round

        deposit = self.val_config_man.deposit.native
        refund_amount = self.val_config_man.fee_round.native * rounds_remain
        validator_earns = self.val_config_man.fee_round.native * (
            self.round_end - self.round_start - rounds_remain
        )

        # If contract was breached,  the validator gets also the deposit
        if self.contract_breached:
            validator_earns += deposit
            deposit = UInt64(0)

        # Return agreed deposit, unused operational fee, and used operational fee (i.e. validator earning)
        return Struct3UInt64(
            arc4.UInt64(deposit),
            arc4.UInt64(refund_amount),
            arc4.UInt64(validator_earns),
        )

    @arc4.abimethod()
    def stake_limit_breach(
        self,
    ) -> arc4.Bool:
        """Anyone can trigger storing of a stake limit breach event."""

        assert (
            not self.contract_breached
        ), "No need to store further breaches if contract has already been breached."

        assert (
            self.keys_confirmed
        ), "Keys need to be confirmed before tracking of breaches is enabled."

        assert (
            self.val_config_man.breach_rounds.native + self.last_breach_round
            < Global.round
        ), "Check if more than agreed number of rounds has passed since last breach."

        assert (
            self.del_acc.balance > self.val_config_man.max_amt
            or self.del_acc.balance < self.val_config_man.min_amt
        ), "Delegator account balance is outside of agreed limits."

        assert (
            self.round_start < Global.round < self.round_end
        ), "Breaching is relevant only inside contract validity."

        self.num_breach += 1
        self.contract_breached = self.num_breach >= self.val_config_man.max_breach
        self.last_breach_round = Global.round

        return arc4.Bool(self.contract_breached)

    @arc4.abimethod()
    def dereg_breach(
        self,
    ) -> arc4.Bool:
        """
        Work in progress
        """

        assert self.called_by_validator_ad(), "Not called by validator app."

        assert not self.contract_breached, "Already has been breached."

        assert (
            self.keys_confirmed
        ), "Keys need to be confirmed before tracking of breaches is enabled."

        val_mng, val_mng_exist = op.AppGlobal.get_ex_bytes(
            self.val_app_id, Bytes(b"manager")
        )
        assert val_mng_exist, "Vlidator contract has manager."
        assert Txn.sender == Account(val_mng), "Manager called brecah key dereg."

        self.contract_breached = True

        return arc4.Bool(self.contract_breached)

    # ----- ----- ----- ------------------ ----- ----- -----
    # ----- ----- ----- Internal functions ----- ----- -----
    # ----- ----- ----- ------------------ ----- ----- -----
    @subroutine
    def called_by_validator_ad(self) -> bool:
        return Global.caller_application_id == self.val_app_id
