# Dataframe semantic fixture v1

Implement only tests/adapters, no production fixes.
Payload exact keys: operation='dataframe-semantics', action, columns, parameters.
columns is nonempty list of exact {name,type,values}; names unique/nonempty; each values length=request.rows>0.
Types int64,float64,bool,utf8. Null is missing. int64 stored canonical decimal strings (String(Int64(s))==s); float64 finite JSON number or string NaN,+Inf,-Inf; bool strict JSON bool; utf8 strings.
Action parameters exact fields:
gather: {indices:[Int]} valid 0..<rows, may empty/duplicate.
select: {columns:[String]} nonempty unique existing.
sort: {column:String,ascending:Bool} int64 or float64 (no present NaN sorting).
filter: {column:String,predicate:String,value:cell} predicate eq/ne/lt/le/gt/ge/isNull/isNotNull. int64 or float64 only; null predicate value must null, ordinary value nonnull valid typed cell. nil always fails ordinary comparison; NaN IEEE rules.
matrix: {columns:[String],target:String} numeric/bool columns; may empty/repeat; target numeric/bool.
replace: {column:String,values:[cells]} same column type/rows, int64 only for this version. Copy source, extract Int64 array, replace contents by provided values, build replacement named temporary then source.withColumn(target,column:replacement); return original, result, original selected target, retained original TypedColumn as one-column frame. This checks functional replacement and retained values; no cell setters.
group-count: {columns:[String],value:String} 1 or2 distinct keys of utf8/int64 type, numeric value distinct from keys. Execute group.count() AND group.agg([value:.count]). Return original plus both results. Key columns String, count row column name? Inspect source, encode observed actual name. Oracle uses documented existing API names. All rows incl null keys grouped first appearance; agg count excludes only nil.

Output exact finite [Double] words, zero atol/rtol. All actions return frame list beginning number of frames. For gather/select/sort/filter: [source,result]. replace: [source,result,selectedOriginal,retainedOriginalColumnFrame]. group-count: [source,rowCounts,presentCounts]. matrix special described below.
Each frame: [rows,numberColumns], followed by columns in actual order. Each column: [typeCode, nameUtf8Length, nameUtf8Bytes...,nullCount], then cells. Codes int64=1,float64=2,bool=3,utf8=4. Cell nil=[0]. Present=[1,payload...]. int64 payload unsigned high32,low32 of Int64 two's complement. float64 same limbs IEEE754; canonicalize NaN bits=0x7ff8000000000000, preserve signed zero/infinity. bool payload0/1. utf8 payload length then bytes. Require actual concrete typed access, unsupported output type throws.
Matrix output: encoded frames([source]) followed by [rows,cols], then float limbs for nested matrix flattened row-major, then float limbs for flat matrix export (validate actual reported dimensions match nested), then [targetCount], target float limbs. Include actual returned dimensions, do not fill from input. Matrix nil=>NaN. Logical layout only, no claim physical buffer layout or zero-copy.
Decode outside timing. Frame construction, operations and exact output encoding inside timing, diagnostic only.
