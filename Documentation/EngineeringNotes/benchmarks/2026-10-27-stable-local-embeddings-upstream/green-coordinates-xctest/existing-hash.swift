@inlinable
public func fnv1aTokenHash(_ string: String) -> Int {
    var hash: UInt64 = 0xcbf29ce484222325
    for byte in string.utf8 {
        hash ^= UInt64(byte)
        hash = hash &* 0x100000001b3
    }
    return Int(truncatingIfNeeded: hash)
}

