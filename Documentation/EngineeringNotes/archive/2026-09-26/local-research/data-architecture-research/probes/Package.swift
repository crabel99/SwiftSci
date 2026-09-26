// swift-tools-version: 6.0
import PackageDescription
let package = Package(name: "BoundaryProbe", platforms: [.macOS(.v14)], dependencies: [.package(path: "/Users/crabel/Documents/src/SwiftSci")], targets: [.executableTarget(name: "BoundaryProbe", dependencies: [.product(name: "SwiftDataFrame", package: "SwiftSci"), .product(name: "SwiftStats", package: "SwiftSci")])])
