using JSimplex,Serialization,LinearAlgebra,SparseArrays
BLAS.set_num_threads(1)
const JS=JSimplex
ws=deserialize(".superpowers/adaptive-degeneracy/runtime-failure-repair/jump-primal-final.bin")
B=JS.basis_matrix(ws);m=size(B,1);policy=ws.progress.numerical_policy
for (row,entering) in ((23224,18805),(12418,17609))
    column=zeros(m);JS._pivot_column!(column,ws,entering)
    unit=zeros(m);unit[row]=1
    direction=similar(column);rho=similar(unit)
    JS._ordinary_forward_solve!(direction,ws.factorization,column)
    JS.transpose_solve!(rho,ws.factorization,unit)
    prices=similar(ws.reduced_costs)
    scratch=JS.SolveQualityScratch(Float64,m);delta=zeros(m)
    println("PIVOT row=",row," entering=",entering)
    for k in 0:3
        JS.price!(prices,ws,rho)
        exact_dot=sum(BigFloat(rho[i])*BigFloat(column[i]) for i in eachindex(column))
        println("STEP ",k," ftran=",direction[row]," btran=",prices[entering]," gap=",direction[row]-prices[entering]," exact_stored_row_price=",exact_dot)
        for (name,x,rhs,tr) in (("ftran",direction,column,false),("btran",rho,unit,true))
            q=JS._compensated_solve_quality!(scratch,B,x,rhs,policy,tr)
            println("QUALITY ",name," relative=",q.relative_error," absolute=",q.absolute_error)
            if k<3
                tr ? JS.transpose_solve!(delta,ws.factorization,scratch.residual) : JS._ordinary_forward_solve!(delta,ws.factorization,scratch.residual)
                if tr
                    function product_pair(a,b,c)
                        total=0.0;error=0.0
                        for i in eachindex(c),value in (a[i],b[i])
                            product=value*c[i];pe=fma(value,c[i],-product)
                            next=total+product;part=next-total
                            error+=(total-(next-part))+(product-part)+pe;total=next
                        end
                        total+error
                    end
                    println("NATIVE_SPLIT_PRICE ",product_pair(x,delta,column))
                end
                x .+= delta
            end
        end
        flush(stdout)
    end
    factor=lu(B)
    reference=JS._refined_basis_solution(factor,B,column,256,()->false)
    println("REFERENCE ",isnothing(reference) ? nothing : reference[row]);flush(stdout)
end
