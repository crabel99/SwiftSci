import Accelerate
import Foundation
let root = URL(fileURLWithPath: "/private/tmp/swiftsci-suite-finish/vision/Benchmarks/Fixtures/vision/inputs")
var worst: Float = 0
var planes = 0
for url in try FileManager.default.contentsOfDirectory(at: root, includingPropertiesForKeys: nil).sorted(by: { $0.path < $1.path }) {
 let p = try JSONSerialization.jsonObject(with: Data(contentsOf:url)) as! [String:Any]
 let w=p["width"] as! Int, h=p["height"] as! Int, tw=p["target_width"] as! Int, th=p["target_height"] as! Int
 let channels=p["channels"] as! Int, values=(p["pixels"] as! [Double]).map(Float.init)
 let scale=min(Double(tw)/Double(w),Double(th)/Double(h))
 let dw=min(tw,max(1,Int((Double(w)*scale).rounded()))), dh=min(th,max(1,Int((Double(h)*scale).rounded())))
 for c in 0..<channels {
  var src=Array(values[(c*w*h)..<((c+1)*w*h)])
  var dst=[Float](repeating:0,count:dw*dh)
  src.withUnsafeMutableBufferPointer { s in dst.withUnsafeMutableBufferPointer { d in
   var sb=vImage_Buffer(data:s.baseAddress,height:UInt(h),width:UInt(w),rowBytes:w*4)
   var db=vImage_Buffer(data:d.baseAddress,height:UInt(dh),width:UInt(dw),rowBytes:dw*4)
   precondition(vImageScale_PlanarF(&sb,&db,nil,vImage_Flags(kvImageHighQualityResampling)) == 0)
  }}
  let expected = dw == w && dh == h ? src : [Float](repeating:src[0],count:dw*dh)
  worst=max(worst,zip(dst,expected).map { abs($0-$1) }.max()!)
  precondition(zip(dst,expected).allSatisfy { abs($0-$1) <= 0.000002+0.000002*abs($1) })
  planes += 1
 }
}
print("Checked \(planes) Accelerate planes from eight fixtures; maximum absolute error \(worst)")
