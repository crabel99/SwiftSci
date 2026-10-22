import simd
import Foundation

@inline(never) func reference(_ mask: SIMDMask<SIMD16<Int8>>) -> UInt16 {
    let weights = SIMD16<UInt8>(1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32, 64, 128)
    let selected = SIMD16<UInt8>.zero.replacing(with: weights, where: mask)
    return UInt16(selected.lowHalf.wrappedSum()) | (UInt16(selected.highHalf.wrappedSum()) << 8)
}
@inline(never) func apple(_ mask: SIMDMask<SIMD16<Int8>>) -> UInt16 {
    let weights = SIMD16<UInt8>(1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32, 64, 128)
    let selected = SIMD16<UInt8>.zero.replacing(with: weights, where: mask)
    return UInt16(simd_reduce_add(selected.lowHalf)) | (UInt16(simd_reduce_add(selected.highHalf)) << 8)
}
@inline(never) func widened(_ mask: SIMDMask<SIMD16<Int8>>) -> UInt16 {
    let weights = SIMD16<UInt8>(1, 2, 4, 8, 16, 32, 64, 128, 1, 2, 4, 8, 16, 32, 64, 128)
    let selected = SIMD16<UInt8>.zero.replacing(with: weights, where: mask)
    let low = SIMD8<UInt16>(truncatingIfNeeded: selected.lowHalf)
    let high = SIMD8<UInt16>(truncatingIfNeeded: selected.highHalf)
    return (low | (high &<< 8)).wrappedSum()
}
@inline(never) func appleFull(_ mask: SIMDMask<SIMD16<Int8>>) -> UInt16 {
    let lowWeights = SIMD16<UInt8>(1,2,4,8,16,32,64,128,0,0,0,0,0,0,0,0)
    let highWeights = SIMD16<UInt8>(0,0,0,0,0,0,0,0,1,2,4,8,16,32,64,128)
    let low = SIMD16<UInt8>.zero.replacing(with: lowWeights, where: mask)
    let high = SIMD16<UInt8>.zero.replacing(with: highWeights, where: mask)
    return UInt16(simd_reduce_add(low)) | (UInt16(simd_reduce_add(high)) << 8)
}
@inline(never) func appleWide(_ mask: SIMDMask<SIMD16<Int8>>) -> UInt16 {
    let weights = SIMD16<UInt8>(1,2,4,8,16,32,64,128,1,2,4,8,16,32,64,128)
    let selected = SIMD16<UInt8>.zero.replacing(with: weights, where: mask)
    let low = SIMD8<UInt16>(truncatingIfNeeded: selected.lowHalf)
    let high = SIMD8<UInt16>(truncatingIfNeeded: selected.highHalf)
    return simd_reduce_add(low | (high &<< 8))
}
@main struct MaskProof {
    static func main() {
        for bits in 0..<65536 {
            var mask = SIMDMask<SIMD16<Int8>>(repeating: false)
            for lane in 0..<16 { mask[lane] = bits & (1 << lane) != 0 }
            precondition(reference(mask) == UInt16(bits))
            precondition(apple(mask) == UInt16(bits))
            precondition(widened(mask) == UInt16(bits))
            precondition(appleFull(mask) == UInt16(bits))
            precondition(appleWide(mask) == UInt16(bits))
        }
        print("65536 masks passed for all five expressions")
    }
}
