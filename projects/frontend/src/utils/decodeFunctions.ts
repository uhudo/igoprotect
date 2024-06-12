import { ABIArrayStaticType, ABIByteType, ABITupleType, ABIUintType, decodeUint64 } from 'algosdk'
import { ValConfigMan } from '../contracts/GeneralValidatorAd'
import { ValConfigExtra } from '../interfaces/contract-specs'

export const decodeUint64List = (data: Uint8Array): bigint[] => {
  const numUint64 = data.length / 8
  const uint64Array: bigint[] = []

  for (let i = 0; i < numUint64; i++) {
    const slice = data.slice(i * 8, (i + 1) * 8)
    const value = decodeUint64(slice, 'bigint')
    uint64Array.push(value)
  }

  return uint64Array
}

export function decodeValConfigMan(data: Uint8Array): ValConfigMan {
  const valConfigManType = new ABITupleType([
    new ABIUintType(64), // hw_cat
    new ABIUintType(64), // min_amt
    new ABIUintType(64), // max_amt
    new ABIUintType(64), // fee_setup
    new ABIUintType(64), // fee_round
    new ABIUintType(64), // deposit
    new ABIUintType(64), // setup_rounds
    new ABIUintType(64), // confirmation_rounds
    new ABIUintType(64), // max_breach
    new ABIUintType(64), // breach_rounds
    new ABIUintType(64), // uptime_gar
  ])

  const decodedTuple = valConfigManType.decode(data) as bigint[]

  return ValConfigMan(decodedTuple as [bigint, bigint, bigint, bigint, bigint, bigint, bigint, bigint, bigint, bigint, bigint])
}

export function decodeValConfigExtra(data: Uint8Array): ValConfigExtra {
  const valConfigExtraType = new ABITupleType([
    new ABIArrayStaticType(new ABIByteType(), 30), // name
    new ABIArrayStaticType(new ABIByteType(), 70), // link
  ])

  const decodedTuple = valConfigExtraType.decode(data) as [Uint8Array, Uint8Array]

  const name_decoder = new TextDecoder('utf-8')
  const name_string = name_decoder.decode(new Uint8Array(decodedTuple[0]))

  const link_decoder = new TextDecoder('utf-8')
  const link_string = link_decoder.decode(new Uint8Array(decodedTuple[1]))

  return {
    name: name_string,
    link: link_string,
  }
}

function concatenateUint8Arrays(arrays: Uint8Array[]): Uint8Array {
  // Calculate the total length of the resulting Uint8Array
  const totalLength = arrays.reduce((sum, arr) => sum + arr.length, 0)

  // Create a new Uint8Array of the total length
  const result = new Uint8Array(totalLength)

  // Copy each Uint8Array into the result
  let offset = 0
  for (const arr of arrays) {
    result.set(arr, offset)
    offset += arr.length
  }

  return result
}

export function decodeStaticByteArray2String(data: Uint8Array, length: number): string {
  const decoded = new ABIArrayStaticType(new ABIByteType(), length).decode(data) as Uint8Array[]

  const decoder = new TextDecoder('utf-8')
  const jointDecoded = concatenateUint8Arrays(decoded)
  const decoded_string = decoder.decode(jointDecoded)

  return decoded_string
}
