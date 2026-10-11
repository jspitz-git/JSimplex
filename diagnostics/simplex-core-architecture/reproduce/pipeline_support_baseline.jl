# Exact pre-S3-B output helper, renamed only for isolated cost comparison.
# Source file SHA256: 31a816bbd9c2dc5922ee5e6a66a61724af5dc931522b8454ce061c97ccde85b4
# Original helper SHA256: 60043e093a3850b4e899c67b5a193e4eb2ce96ae2ab5b6bcfc3bccef09710380
function _pipeline_original_output_support!(ws,cache,index,values)
    if index > 0
        return length(_pipeline_vector!(ws,values).indices)
    end
    all(isfinite,values) || throw(OverflowError("Pipeline solve overflowed"))
    return count(!iszero,values)
end
