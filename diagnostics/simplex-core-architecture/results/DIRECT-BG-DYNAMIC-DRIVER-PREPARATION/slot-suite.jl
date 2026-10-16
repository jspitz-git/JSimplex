# Test-owned module: imported aliases only, no methods added to JSimplex.
module DynamicBGSlotTests
using JSimplex: BGSlotUpper, _bg_slots, _bg_lookup, _bg_link!, _bg_unlink!,
    _bg_set_at!, _bg_capacity, _bg_reserve!, _bg_reserve_with!, _bg_swap_rows!, _bg_rotate_rows!
import JSimplex
function run_slots()
    Base.include(@__MODULE__,normpath(joinpath(dirname(pathof(JSimplex)),"../test/slot-upper-tests.jl")))
end
end
