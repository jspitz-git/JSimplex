module SplitStorageTests
using Test,SparseArrays
import JSimplex
import JSimplex: BGSplitUpper, _sbu_allocate, _sbu_append_slab!, _sbu_back!, _sbu_buffer, _sbu_build, _sbu_build_with, _sbu_cid, _sbu_clear!, _sbu_coordinates, _sbu_copy, _sbu_copy_with, _sbu_decode, _sbu_degree, _sbu_delete!, _sbu_descriptor_capacity, _sbu_find, _sbu_free!, _sbu_free_block, _sbu_from_stage!, _sbu_gap!, _sbu_grown, _sbu_handle, _sbu_insert_at!, _sbu_limit, _sbu_link_block!, _sbu_merge_next!, _sbu_new, _sbu_predecessor, _sbu_reserve_block!, _sbu_reserve_descriptors!, _sbu_reserve_row!, _sbu_rotate_rows!, _sbu_row_capacity, _sbu_row_handle, _sbu_row_offset, _sbu_row_search, _sbu_set!, _sbu_set_with!, _sbu_stage!, _sbu_swap_rows!, _sbu_take!, _sbu_target, _sbu_tuple, _sbu_unlink_block!, _sbu_write!, _sbu_zeros
include(joinpath(dirname(pathof(JSimplex)),"../test/split-oracles.jl"))
include(joinpath(dirname(pathof(JSimplex)),"../test/split-upper-tests.jl"))
end
