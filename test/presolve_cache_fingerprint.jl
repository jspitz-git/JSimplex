function canonical(io,x)
 if x isa SparseMatrixCSC
  print(io,typeof(x),size(x));canonical(io,x.colptr);canonical(io,x.rowval);canonical(io,x.nzval)
 elseif x isa AbstractArray
  print(io,"ArrayValues",eltype(x),size(x))
  E=eltype(x)
  if E<:Number && isbitstype(E)
   if x isa Array;write(io,x);else;for v in x;write(io,v);end;end
  elseif E<:Enum
   for v in x;write(io,Int(v));end
  elseif E==Union{Nothing,Float64} || E==Union{Nothing,Float32}
   for v in x
    write(io,UInt8(v!==nothing));v===nothing || write(io,v)
   end
  elseif E==JSimplex.Bound{Float64} || E==JSimplex.Bound{Float32}
   for v in x;write(io,isfinite(v));write(io,v.value);end
  elseif E==Tuple{Int,Float64} || E==Tuple{Int,Float32}
   for v in x;write(io,v[1]);write(io,v[2]);end
  else
   for v in x;canonical(io,v);end
  end
 elseif x isa BigFloat
  print(io,precision(x),':',repr(x))
 elseif x isa AbstractString || x isa Symbol || x isa BigInt
  v=string(x);write(io,ncodeunits(v));write(io,v)
 elseif x isa Enum
  write(io,Int(x))
 elseif x isa Number && isbitstype(typeof(x))
  write(io,x)
 else
  print(io,typeof(x))
  for f in fieldnames(typeof(x));canonical(io,getfield(x,f));end
 end
 write(io,UInt8(0xff))
end
digest(x)=begin io=IOBuffer();canonical(io,x);bytes2hex(sha256(take!(io))) end
# Model/history-specific field encoding; avoid per-element type formatting and
# preserve signed zero, enum values and union tags. Never traverse CSC densely.
@assert digest([0.])!=digest([-0.])
@assert digest([JS.BASIC])!=digest([JS.AT_LOWER])
@assert digest(Union{Nothing,Float64}[nothing])!=digest(Union{Nothing,Float64}[0.])
