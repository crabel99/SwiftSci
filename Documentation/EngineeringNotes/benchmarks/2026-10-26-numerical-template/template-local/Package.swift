// swift-tools-version: 6.0
import PackageDescription

let package = Package(
    name: "ScientificWorkflow",
    platforms: [.macOS(.v14)],
    dependencies: [
        .package(name: "SwiftSci", path: "/private/tmp/swiftsci-llm-completion-20261026/source")
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
