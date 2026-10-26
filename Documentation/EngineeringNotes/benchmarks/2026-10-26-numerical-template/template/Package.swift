// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "ScientificWorkflow",
    platforms: [.macOS(.v14)],
    dependencies: [
        .package(url: "https://github.com/crabel99/SwiftSci.git",
                 revision: "0e1635199654ac6a20b32ea53eea0ffdfa39e747")
    ],
    targets: [
        .executableTarget(name: "ScientificWorkflow", dependencies: [
            .product(name: "SwiftDataFrame", package: "SwiftSci"),
            .product(name: "SwiftPreprocessing", package: "SwiftSci"),
            .product(name: "SwiftCluster", package: "SwiftSci"),
            .product(name: "SwiftML", package: "SwiftSci")
        ])
    ]
)
