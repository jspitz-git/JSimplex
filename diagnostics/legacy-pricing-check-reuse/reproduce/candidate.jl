# Eligibility follows the actual fixed pricing. DSE recovery may publish Devex;
# a Dantzig fallback from DSE does not authorize reuse of a weighted-state check.
function pricing_supported(ws)
    selected = ws.options.pricing
    active = JS._weight_pricing(ws,:dual)
    return active == selected || (selected == :steepest_edge && active == :devex)
end
function install_candidate!()
    install_method("_can_reuse_dual_checks", (
        "ws.options.pricing == :devex" => "ws.options.pricing in (:devex,:dantzig,:steepest_edge)",
        "_weight_pricing(ws,:dual) == :devex" => "Main.pricing_supported(ws)",))
end
install_candidate!()
