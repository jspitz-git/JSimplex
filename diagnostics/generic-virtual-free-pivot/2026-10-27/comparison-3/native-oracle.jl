const NATIVE_ORACLES=Dict{String,Any}[]
function native_direction_oracle(v)
 B=Matrix(v.w.problem.A[:,v.w.basis.basic_indices]);x=v.proposal.column
 rhs=Vector(v.w.problem.A[:,v.proposal.entering]);q=Rational{BigInt}
 M=q.(B);z=q.(x);b=q.(rhs);wanted=q.(v.wanted)
 residual=M*z-b
 scale=max(q(1),maximum(sum(abs(M[i,j]) for j in axes(M,2)) for i in axes(M,1))*maximum(abs,z),maximum(abs,b))
 bound=8*q(eps(Float64))*scale
 construction=M*wanted==b
 passed=construction&&maximum(abs,residual)<=bound
 push!(NATIVE_ORACLES,Dict("matrix"=>vec(B),"rows"=>size(B,1),"column"=>copy(x),"rhs"=>rhs,"wanted"=>copy(v.wanted),"residual"=>string.(residual),"bound"=>string(bound),"construction_exact"=>construction,"passed"=>passed))
 passed
end
