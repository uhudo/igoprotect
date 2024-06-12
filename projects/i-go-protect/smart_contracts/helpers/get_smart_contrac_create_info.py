import base64
import json

import algokit_utils


def get_smart_contrac_create_info(path: "str") -> None:
    """
    Function reads from path the .approval.teal, .clear.teal, and .arc32.json files
    all the information needed to create the contract, i.e. the byte code for the
    approval and clear programs, state schema, and extra pages.
    For compiling, the localnet is used (it has to be running).
    """
    # Read the TEAL programs
    with open(path + ".approval.teal") as f:
        approval_program = f.read()

    with open(path + ".clear.teal") as f:
        clear_state_program = f.read()

    # Initialize the Algorand client
    algod_client = algokit_utils.get_algod_client(
        algokit_utils.get_default_localnet_config("algod")
    )

    # Compile the approval program
    approval_response = algod_client.compile(approval_program)
    approval_bytecode = base64.b64decode(approval_response["result"])

    # Compile the clear state program
    clear_response = algod_client.compile(clear_state_program)
    clear_bytecode = base64.b64decode(clear_response["result"])

    # Print the compiled bytecode in \x format
    print("\nApproval Program Bytecode:")
    print("".join([f"\\x{x:02x}" for x in approval_bytecode]))

    print("\nClear State Program Bytecode:")
    print("".join([f"\\x{x:02x}" for x in clear_bytecode]))

    info = {}
    with open(path + ".arc32.json") as file:
        data = json.load(file)

    info["global_num_bytes"] = data["state"]["global"]["num_byte_slices"]

    info["global_num_uint"] = data["state"]["global"]["num_uints"]

    info["local_num_bytes"] = data["state"]["local"]["num_byte_slices"]

    info["local_num_uint"] = data["state"]["local"]["num_uints"]

    # Calculate the total size of the bytecode
    total_size = len(approval_bytecode) + len(clear_bytecode)

    # Calculate the number of extra pages needed
    extra_program_pages = total_size // 1024  # Integer division to get extra pages

    # If there's any remainder, add an additional page
    if total_size % 1024 > 0:
        extra_program_pages += 1

    # Subtract 1 because the first page is free
    extra_program_pages = max(0, extra_program_pages - 1)

    info["extra_program_pages"] = extra_program_pages

    # in microAlgos
    COST_APP_PAGE = 100_000
    COST_STATE_ENTRY = 25_000
    COST_UINT = COST_STATE_ENTRY + 3_500
    COST_BYTES = COST_STATE_ENTRY + 25_000

    mbr = (
        (info["extra_program_pages"] + 1) * COST_APP_PAGE
        + info["global_num_uint"] * COST_UINT
        + info["global_num_bytes"] * COST_BYTES
    )

    print()
    print("global_num_bytes: ", info["global_num_bytes"])
    print()
    print("global_num_uint: ", info["global_num_uint"])
    print()
    print("local_num_bytes: ", info["local_num_bytes"])
    print()
    print("local_num_uint: ", info["local_num_uint"])
    print()
    print("extra_program_pages: ", info["extra_program_pages"])
    print()
    print("MBR increase for creation: ", mbr)


# For DelegatorContract
print("----- Delegator Contract -----")
pathDelegatorContract = "../artifacts/delegator_contract/DelegatorContract"

get_smart_contrac_create_info(pathDelegatorContract)

# For GeneralValidatorAd
print("----- Validator Ad -----")
pathGeneralValidatorAd = "../artifacts/general_validator_ad/GeneralValidatorAd"

get_smart_contrac_create_info(pathGeneralValidatorAd)

# For GfactoryValidatorAd
print("----- Factory of Validator Ads -----")
pathGfactoryValidatorAd = "../artifacts/gfactory_validator_ad/GfactoryValidatorAd"

get_smart_contrac_create_info(pathGfactoryValidatorAd)

# For Noticeboard
print("----- Noticeboard -----")
pathNoticeboard = "../artifacts/noticeboard/Noticeboard"

get_smart_contrac_create_info(pathNoticeboard)
