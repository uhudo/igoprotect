# pyright: reportMissingModuleSource=false
import typing as t

from algopy import *
from algopy import (
    Account,
    TransactionType,
    Txn,
    UInt64,
    arc4,
    itxn,
    op,
    subroutine,
)

""" Contants """
# Maximum number of delegators per validator
#  ! Note: Manually check the below are same because I don't know why it doesn't work as t.Literal[MAX_DEL_CNT]
MAX_DEL_CNT: int = 4
T_LITERAL_MAX_DEL_CNT = t.Literal[4]

# Contract creation
MBR_VALIDATORAD_CREATION = 899_500

# Increase in MBR for adding new delegator contract
MBR_DELEGATORCONTRACT_CREATION = 785_000

# ------- Definition of types -------
# Selection key generated for the delegator
SelKey: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[32]]
# Vote key generated for the delegator
VoteKey: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[32]]
# State proof key dilution generated for the delegator
StateProofKey: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[64]]

# EarnFactor: t.TypeAlias = arc4.UFixedNxM[t.Literal[16], t.Literal[2]]

DelegatorList: t.TypeAlias = arc4.StaticArray[arc4.UInt64, t.Literal[4]]

MAX_VAL_CNT = 100
VAL_LIST_EL_BYTE_SIZE = 8
ValidatorList: t.TypeAlias = arc4.StaticArray[arc4.UInt64, t.Literal[100]]

VAL_LIST = b"val_list"  # is of length 8
# Increase in MBR for adding new delegator contract
MBR_BOX_VAL_LIST_CREATION = 2_500 + 400 * (VAL_LIST_EL_BYTE_SIZE * MAX_VAL_CNT + 8)


# ------- Definition of structs -------
class Struct2UInt64(arc4.Struct):
    """Struct with two arc4.UInt64 for returning multiple values"""

    a: arc4.UInt64
    b: arc4.UInt64


class Struct3UInt64(arc4.Struct):
    """Struct with three arc4.UInt64 for returning multiple values"""

    a: arc4.UInt64
    b: arc4.UInt64
    c: arc4.UInt64


class Struct4UInt64(arc4.Struct):
    """Struct with four arc4.UInt64 for returning multiple values"""

    a: arc4.UInt64
    b: arc4.UInt64
    c: arc4.UInt64
    d: arc4.UInt64


class ValConfigMan(arc4.Struct):
    """Struct with mandatory information of a validator ad"""

    # Number denoting the category of hardware
    hw_cat: arc4.UInt64
    min_amt: arc4.UInt64  # Minimum amount that user must keep in one's account
    max_amt: arc4.UInt64  # Maximum amount that user can keep in one's account
    fee_setup: arc4.UInt64  # Fee charged for setting up the node (i.e. generating keys)
    fee_round: arc4.UInt64  # Fee charged for operation per round
    deposit: arc4.UInt64  # Deposit made by user to Noticeboard
    # Maximum number of rounds the validator promises to respond to generate the keys for the user
    setup_rounds: arc4.UInt64
    # Maximum number of round the validator is willing to wait for user to confirm the generated keys
    confirmation_rounds: arc4.UInt64
    max_breach: arc4.UInt64  # Maximum number of contract breaches allowed
    # Minimum number of rounds between two contract breaches to consider them separate events
    breach_rounds: arc4.UInt64
    uptime_gar: arc4.UInt64  # Guaranteed uptime for the node by the validator (0-1)


"""
ValConfigManDefault = ValConfigMan(
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
"""


ValName: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[30]]
ValLink: t.TypeAlias = arc4.StaticArray[arc4.Byte, t.Literal[70]]


class ValConfigExtra(arc4.Struct):
    """
    Struct with extra information of a validator ad
    """

    name: ValName  # Name of validator
    link: ValLink  # Link to more info (w/o http://www.)


"""
ValConfigExtraDefault = ValConfigExtra(
    arc4.String("0"),
    arc4.String("0"),
    arc4.String("0"),
    arc4.String("0"),
)
"""


# ------- Functions -------
@subroutine
def pay_to_sender(amount: UInt64) -> None:
    itxn.Payment(
        amount=amount,
        receiver=Txn.sender,
        fee=0,
    ).submit()


@subroutine
def pay_to_acc(amount: UInt64, account: Account) -> None:
    itxn.Payment(
        amount=amount,
        receiver=account,
        fee=0,
    ).submit()


@subroutine
def is_key_dereg(tx_idx: UInt64) -> bool:
    assert (
        op.GTxn.type_enum(tx_idx) == TransactionType.KeyRegistration
    ), "Key (de)reg transaction."

    # Check if key reg is deregistration
    assert op.GTxn.selection_pk(tx_idx) == op.bzero(32)
    assert op.GTxn.vote_pk(tx_idx) == op.bzero(32)
    assert op.GTxn.state_proof_pk(tx_idx) == op.bzero(64)
    assert op.GTxn.vote_key_dilution(tx_idx) == UInt64(0)
    assert op.GTxn.vote_first(tx_idx) == UInt64(0)
    assert op.GTxn.vote_last(tx_idx) == UInt64(0)

    return True
