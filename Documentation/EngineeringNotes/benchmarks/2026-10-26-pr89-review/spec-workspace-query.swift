import Accelerate
for dimension: Int32 in [23_169, 23_170, 24_000, 26_000, 26_753] {
    var m = dimension, n = dimension, lda = dimension, ldu = dimension, ldvt = dimension
    var job: Int8 = 83
    var a = 0.0, s = 0.0, u = 0.0, vt = 0.0, work = 0.0
    var lwork: Int32 = -1, iw: Int32 = 0, info: Int32 = 0
    dgesdd_(&job, &m, &n, &a, &lda, &s, &u, &ldu, &vt, &ldvt, &work, &lwork, &iw, &info)
    print("dimension=\(dimension) info=\(info) query=\(work) Int32=\(Int32(exactly: work) as Any)")
}
