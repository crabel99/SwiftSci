import Foundation
import XCTest
let suite = LocalEmbeddingEngineTests.defaultTestSuite
suite.run()
exit(suite.testRun!.hasSucceeded ? 0 : 1)
