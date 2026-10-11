# Fixed counters for owned diagnostic metadata. Public diagnostics retain bodies.
function install_long_metadata!(JS,source_root)
    isdefined(JS,:_lc_metadata_installed) && throw(ArgumentError("Metadata already installed"))
    isdefined(JS,:_lc_owned_observer_type) || error("Install owned event sink first")
    index(name)=something(findfirst(==(name),LONG_COUNTER_LABELS))
    scanned=index("pricing_scanned_entries");scored=index("pricing_scored_entries")
    full=index("pricing_full_scan");block=index("pricing_block_scan");hit=index("pricing_pool_hit")
    pool_expression=long_function(source_root,"simplex_pricing.jl","function _record_pricing_work!(")
    full_expression=long_function(source_root,"simplex_pricing.jl","function _record_full_pricing!(")
    discard=long_function(source_root,"simplex_pivot.jl","function _discard_candidate!(")
    Core.eval(JS,quote
        const _lc_metadata_installed=true
        @inline _lc_owned(d)=false
        @inline _lc_owned(d::SimplexDiagnostics{F}) where {F<:_lc_owned_observer_type}=true
        @inline _lc_owned(d::SimplexDiagnostics{F}) where {F<:_StageObserver}=
            _lc_owned(d.observer.live.progress.diagnostics)
    end)
    old=pool_expression.args[2]
    pool_expression.args[2]=quote
        if _lc_owned(diagnostics)
            local scanned=pool.scanned_entries-previous[1]
            _lc_counts[$scanned]+=scanned
            _lc_counts[$scored]+=pool.scored_entries-previous[2]
            _lc_counts[$full]+=pool.full_scans-previous[3]
            _lc_counts[$block]+=pool.block_scans-previous[4]
            _lc_counts[$hit]+=Int(scanned==0 && result!=0)
            return nothing
        end
        $old
    end
    old=full_expression.args[2]
    full_expression.args[2]=quote
        if _lc_owned(diagnostics)
            _lc_counts[$scanned]+=count
            _lc_counts[$scored]+=scored
            _lc_counts[$full]+=1
            return nothing
        end
        $old
    end
    Core.eval(JS,pool_expression);Core.eval(JS,full_expression)
    committed=Expr(:block)
    for reason in (:restore_checkpoint,:repair,:checkpoint,:pricing_reset)
        i=index("committed_"*string(reason))
        push!(committed.args,:(reason==$(QuoteNode(reason)) && (_lc_counts[$i]+=1)))
    end
    Core.eval(JS,quote
        function _record_recovery!(d::SimplexDiagnostics{F},reason) where {F<:_lc_owned_observer_type}
            record_event!(d,reason) # preserve validation; no callback on commit
            $committed
            nothing
        end
    end)
    matches=Ref(0);discard_index=index("discarded_metadata_events")
    function rewrite(node)
        node isa Expr || return node
        if node.head==:call && node.args[1]==:record_event!
            matches[]+=1
            return quote
                _lc_owned(ws.progress.diagnostics) && (_lc_counts[$discard_index]+=1)
                $node
            end
        end
        Expr(node.head,map(rewrite,node.args)...)
    end
    discard=rewrite(discard)
    matches[]==1 || error("Expected one discarded metadata call")
    Core.eval(JS,discard)
    nothing
end
