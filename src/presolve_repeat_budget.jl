module _PresolveRepeat

const JS = parentmodule(@__MODULE__)
const _budget_key = gensym(:presolve_repeat_budget)

# One ledger belongs to one augmented presolve invocation, including abandoned
# staging attempts. The task-local binding also isolates concurrent solves.
mutable struct Ledger
    limit::Int
    term_visits::Int
    proof_edges::Int
    expansion_edges::Int
    singleton_term_visits::Int
    rounds::Int
    sparse_updates::Int
    sparse_records::Int
    dependent_work::Int
end
Ledger(; limit::Int=1_000_000) = Ledger(limit,0,0,0,0,0,0,0,0)

current() = get(Base.task_local_storage(), _budget_key, nothing)::Union{Nothing,Ledger}
function with_budget(f, b::Ledger)
    # A rejection learned with less remaining budget cannot be reused after
    # replacing or restoring the ledger, when the available work can increase.
    JS._PresolveWork.clear_rejections!()
    try
        return Base.task_local_storage(f, _budget_key, b)
    finally
        JS._PresolveWork.clear_rejections!()
    end
end

sparse_available(b::Ledger) = b.sparse_updates < 200_000 && b.sparse_records < 50_000
sparse_can_charge(b::Ledger, work::Int) =
    b.sparse_records < 50_000 && b.sparse_updates + work <= 200_000
function charge_sparse!(b::Ledger, work::Int)
    b.sparse_updates += work
    b.sparse_records += 1
    nothing
end
dependent_can_charge(b::Ledger, work::Int) = b.dependent_work + work <= 200_000
function charge_dependent!(b::Ledger, work::Int)
    b.dependent_work += work
    nothing
end

function infer_shared(p, b::Ledger, stop_requested=() -> false)
    remaining = min(b.limit-b.term_visits, b.limit-b.proof_edges,
                    b.limit-b.expansion_edges, b.limit-b.singleton_term_visits)
    turns = max(0, 8-b.rounds)
    (remaining <= 0 || turns == 0) &&
        return JS._InequalityProofs.Certificate[], Dict{String,Int}()
    certificates, stats = JS._InequalityProofs.infer(p;
        work_limit=remaining, rounds=turns, expand_limit=5000, stop_requested)
    b.term_visits += get(stats,"term_visits",0)
    b.proof_edges += get(stats,"proof_edges",0)
    b.expansion_edges += get(stats,"expansion_edges",0)
    b.singleton_term_visits += get(stats,"singleton_term_visits",0)
    b.rounds += get(stats,"rounds",0)
    return certificates, stats
end

end
