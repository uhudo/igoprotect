export function stringToUint8ArrayWithLength(str: string, length: number): Uint8Array {
  const encoder = new TextEncoder()
  const encoded = encoder.encode(str)

  if (encoded.length > length) {
    // Truncate the array
    return encoded.slice(0, length)
  } else if (encoded.length < length) {
    // Pad the array
    const paddedArray = new Uint8Array(length)
    paddedArray.set(encoded)
    return paddedArray
  } else {
    // If the length is exactly the same
    return encoded
  }
}
