_primal_direction_magnitude(value) = abs(value)
_primal_direction_magnitude(value::BigFloat) = signbit(value) ? -value : value
