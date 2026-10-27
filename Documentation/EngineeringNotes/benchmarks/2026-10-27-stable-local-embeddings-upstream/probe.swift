import Foundation
@main struct EmbeddingProbe {
 static func main() async throws {
  let engine = LocalEmbeddingEngine(dimension:64)
  let text = "neural network processor computation software algorithm"
  let result = try await ZeroShotTextClassifier(embeddingProvider:engine).classify(text:text,candidateLabels:["technology","food"])
  let golden=LocalEmbeddingEngine(dimension:16).embed("abc")
  let payload:[String:Any] = ["vector":engine.embed(text),"prediction":result.predictedLabel,"scores":result.scores,"golden":golden]
  print(String(data:try JSONSerialization.data(withJSONObject:payload,options:[.sortedKeys]),encoding:.utf8)!)
 }
}
