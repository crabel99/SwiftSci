struct Worker { enum Output { case values([Double]) } }
struct BenchmarkFailure: Error { init(_ text: String) {} }
