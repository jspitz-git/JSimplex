# Test-owned module; top-level inclusion only. Production methods unchanged.
module BlockStorageTests
using Test, SparseArrays
import JSimplex
import JSimplex: BGBlockUpper, _bgu_allocate, _bgu_append_slab!, _bgu_back!, _bgu_buffer, _bgu_build, _bgu_build_with, _bgu_cid, _bgu_clear!, _bgu_coordinates, _bgu_copy, _bgu_copy_with, _bgu_decode, _bgu_degree, _bgu_delete!, _bgu_descriptor_capacity, _bgu_find, _bgu_free!, _bgu_free_block, _bgu_from_stage!, _bgu_gap!, _bgu_grown, _bgu_handle, _bgu_insert_at!, _bgu_limit, _bgu_link_block!, _bgu_merge_next!, _bgu_new, _bgu_predecessor, _bgu_reserve_block!, _bgu_reserve_descriptors!, _bgu_reserve_row!, _bgu_rotate_rows!, _bgu_row_capacity, _bgu_row_handle, _bgu_row_offset, _bgu_row_search, _bgu_set!, _bgu_set_with!, _bgu_stage!, _bgu_swap_rows!, _bgu_take!, _bgu_tuple, _bgu_unlink_block!, _bgu_write!, _bgu_zeros
include(joinpath(dirname(pathof(JSimplex)),"../test/block-oracles.jl"))
include(joinpath(dirname(pathof(JSimplex)),"../test/block-upper-tests.jl"))
end
