; Function Signature: probe(Base.Val{:new})
; Function Attrs: noinline
define swiftcc i8 @julia_probe_4215(ptr nonnull swiftself "gcstack" %pgcstack_arg) local_unnamed_addr #0 !dbg !4 {
top:
  %ptls_field = getelementptr inbounds nuw i8, ptr %pgcstack_arg, i64 16
  %ptls_load = load ptr, ptr %ptls_field, align 8, !tbaa !14
  %0 = getelementptr inbounds nuw i8, ptr %ptls_load, i64 16
  %safepoint = load atomic ptr, ptr %0 monotonic, align 8, !tbaa !18, !invariant.load !10
  fence syncscope("singlethread") seq_cst
  %1 = load volatile i64, ptr %safepoint, align 8
  fence syncscope("singlethread") seq_cst
  %2 = call swiftcc i8 @j__dense_ma_rounding_matches_4217(ptr nonnull swiftself "gcstack" %pgcstack_arg), !dbg !20
  ret i8 %2, !dbg !20
}
