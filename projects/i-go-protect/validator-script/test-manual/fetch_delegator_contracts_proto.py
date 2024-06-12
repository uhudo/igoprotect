import base64
from typing import List
from algokit_utils import get_algod_client
from algosdk.v2client import algod
from algosdk.encoding import encode_address

# todo: Clean way of including or callingfrom base path
from pathlib import Path
import sys
sys.path.append(str(Path(*Path(__file__).parent.parts[:-1])))

from utils import get_del_id_list, get_del_state_list, decode_uint64_list



def base32_to_hex(base32_encoded, trim_end_bytes=4):
    # Function to add correct padding for Base32 decoding
    def add_base32_padding(s):
        return s + "=" * ((8 - len(s) % 8) % 8)

    # Add padding if necessary and decode from Base32
    base32_padded = add_base32_padding(base32_encoded)
    try:
        base32_decoded = base64.b32decode(base32_padded)
    except Exception as e:
        return f"Error decoding: {str(e)}"

    # Convert decoded bytes to hex and trim the specified number of bytes from the end
    hex_result = base32_decoded[:-trim_end_bytes].hex() if trim_end_bytes else base32_decoded.hex()

    return base32_decoded.hex()


def hex_to_base32(hex_encoded, remove_padding=False):
    # Convert hex to bytes
    bytes_data = bytes.fromhex(hex_encoded)

    # Encode bytes to Base32
    base32_encoded = base64.b32encode(bytes_data).decode()

    # Base32 padding correction to ensure full length matching if necessary
    necessary_padding = (-len(base32_encoded)) % 8
    base32_encoded += '=' * necessary_padding

    return base32_encoded


if __name__ == '__main__':

    ### Config 
    # val_app_id = "1921"
    val_app_id = "2664"
    algod_address = "http://localhost:4001"
    algod_token = "a" * 64


    del_acc_reference = 'JQLISQ4SUTQIJTL6YI5WVT32YIJJJCTAM7TNQQGYJDEBPX6XZWWX74RQHQ'
    del_acc_reference_hex = base32_to_hex(del_acc_reference)

    print(del_acc_reference)
    print(del_acc_reference_hex)
    print(hex_to_base32(del_acc_reference_hex))

    ### Run
    algod_client = algod.AlgodClient(algod_token, algod_address)

    del_app_id_list = get_del_id_list( algod_client, val_app_id )
    del_app_state_list = get_del_state_list( algod_client, del_app_id_list )

    print('\n')
    
    for del_app_id, del_app_state in zip(del_app_id_list, del_app_state_list):

        print(f'DelApp {del_app_id}')
        print(f'Keys deposited: {del_app_state.part_keys_deposited}')
        print(f'Keys confirmed: {del_app_state.keys_confirmed}')

        # print(decode_uint64_list(del_app_state.del_acc.as_base64)) 7ff2303c
        # print(del_app_state.del_acc.as_hex)
        # print(hex_to_base32(del_app_state.del_acc.as_hex))
        # print(hex_to_base32(del_app_state.del_acc.as_hex + '7ff2303c'))

        # b32 = hex_to_base32(del_app_state.del_acc.as_hex)

        # https://developer.algorand.org/docs/get-details/accounts/
        b32_with_checksum = (encode_address(del_app_state.del_acc.as_bytes))

        print(b32_with_checksum)

        print('\n')
