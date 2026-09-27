import Accelerate
import Foundation
for (w,h,dw,dh) in [(3,2,7,5),(7,5,3,2),(5,3,5,3),(1,3,3,7)] {
 var src = (0..<(w*h)).map {Float(($0 * 7 + $0 / w * 3) % 17) / 16}
 var dst = [Float](repeating:0,count:dw*dh)
 src.withUnsafeMutableBufferPointer { s in dst.withUnsafeMutableBufferPointer { d in
 var sb = vImage_Buffer(data:s.baseAddress,height:UInt(h),width:UInt(w),rowBytes:w*4)
 var db = vImage_Buffer(data:d.baseAddress,height:UInt(dh),width:UInt(dw),rowBytes:dw*4)
 let e = vImageScale_PlanarF(&sb,&db,nil,vImage_Flags(kvImageHighQualityResampling))
 assert(e == 0)
 }}
 print(String(data:try! JSONSerialization.data(withJSONObject:["w":w,"h":h,"dw":dw,"dh":dh,"src":src,"dst":dst]),encoding:.utf8)!)
}
