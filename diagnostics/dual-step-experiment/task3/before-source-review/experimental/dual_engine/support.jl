function set_present!(s::SparseSet,i::Int,present::Bool)
    checkbounds(s.position,i)
    old=s.position[i]
    if present && old==0
        s.used+=1;s.ids[s.used]=i;s.position[i]=s.used
    elseif !present && old!=0
        last=s.ids[s.used];s.ids[old]=last;s.position[last]=old
        s.used-=1;s.position[i]=0
    end
    nothing
end
function set_scratch!(q::StampedScratch,i::Int,x::Float64)
    checkbounds(q.values,i);isfinite(x)||throw(ArgumentError("nonfinite scratch write"))
    if !iszero(x) && q.stamps[i]!=q.epoch
        q.used+=1;q.ids[q.used]=i;q.stamps[i]=q.epoch
    end
    q.values[i]=x;q.evidence_generation=UInt64(0)
    nothing
end
function add_scratch!(q::StampedScratch,i::Int,x::Float64)
    checkbounds(q.values,i);isfinite(x)||throw(ArgumentError("nonfinite scratch addition"))
    value=q.values[i]+x
    isfinite(value)||throw(ArgumentError("scratch addition overflow"))
    set_scratch!(q,i,value)
end
function compact_scratch!(q::StampedScratch)
    kept=0
    for k in 1:q.used
        i=q.ids[k]
        if !iszero(q.values[i]);kept+=1;q.ids[kept]=i
        else;q.stamps[i]=UInt32(0)
        end
    end
    q.used=kept
    nothing
end
function clear_scratch!(q::StampedScratch)
    for k in 1:q.used;q.values[q.ids[k]]=0.;end
    q.used=0;q.evidence_generation=UInt64(0)
    if q.epoch==typemax(UInt32)
        fill!(q.stamps,UInt32(0));q.epoch=UInt32(1)
    else
        q.epoch+=UInt32(1)
    end
    nothing
end
