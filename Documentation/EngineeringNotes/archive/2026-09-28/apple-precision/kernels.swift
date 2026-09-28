@inline(never)
public func scalarFMA(_ accumulator: Double, _ x: Double, _ y: Double) -> Double {
    accumulator.addingProduct(x, y)
}

@inline(never)
public func vectorFMA(_ accumulator: SIMD2<Double>, _ x: SIMD2<Double>, _ y: SIMD2<Double>) -> SIMD2<Double> {
    accumulator.addingProduct(x, y)
}

@inline(never)
public func separateProduct(_ accumulator: Double, _ x: Double, _ y: Double) -> Double {
    let product = x * y
    return accumulator + product
}
