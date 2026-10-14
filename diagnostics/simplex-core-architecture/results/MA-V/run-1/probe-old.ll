; Function Signature: probe(Base.Val{:old})
; Function Attrs: noinline
define swiftcc range(i8 0, 2) i8 @julia_probe_4204(ptr nonnull swiftself "gcstack" %pgcstack_arg) local_unnamed_addr #0 !dbg !4 {
top:
  %gcframe1 = alloca [3 x ptr], align 16
  call void @llvm.memset.p0.i64(ptr align 16 %gcframe1, i8 0, i64 24, i1 true)
  store i64 4, ptr %gcframe1, align 8, !tbaa !14
  %task.gcstack = load ptr, ptr %pgcstack_arg, align 8
  %frame.prev = getelementptr inbounds nuw i8, ptr %gcframe1, i64 8
  store ptr %task.gcstack, ptr %frame.prev, align 8, !tbaa !14
  store ptr %gcframe1, ptr %pgcstack_arg, align 8
  %ptls_field = getelementptr inbounds nuw i8, ptr %pgcstack_arg, i64 16
  %ptls_load = load ptr, ptr %ptls_field, align 8, !tbaa !14
  %0 = getelementptr inbounds nuw i8, ptr %ptls_load, i64 16
  %safepoint = load atomic ptr, ptr %0 monotonic, align 8, !tbaa !18, !invariant.load !10
  fence syncscope("singlethread") seq_cst
  %1 = load volatile i64, ptr %safepoint, align 8
  fence syncscope("singlethread") seq_cst
  %scope = getelementptr inbounds i8, ptr %pgcstack_arg, i64 -112, !dbg !20
  %2 = load ptr, ptr %scope, align 8, !dbg !20, !tbaa !14, !alias.scope !34, !noalias !37
  %.tag_addr = getelementptr inbounds i8, ptr %2, i64 -8, !dbg !20
  %.tag = load atomic volatile i64, ptr %.tag_addr unordered, align 8, !dbg !20, !tbaa !42, !range !45
  %3 = and i64 %.tag, -16, !dbg !20
  %exactly_isa = icmp eq i64 %3, 208, !dbg !20
  %exactly_isa3 = icmp eq i64 %3, ptrtoint (ptr @"+Main.Base.ScopedValues.Scope#4206.jit" to i64), !dbg !20
  %or.cond = select i1 %exactly_isa, i1 true, i1 %exactly_isa3, !dbg !20
  br i1 %or.cond, label %pass, label %fail, !dbg !20

L13:                                              ; preds = %guard_exit
  store ptr %7, ptr %gc_slot_addr_036, align 8
  %getfield = call ptr @ijl_get_nth_field_checked(ptr nonnull %7, i64 0), !dbg !46
  %getfield.tag_addr = getelementptr inbounds i8, ptr %getfield, i64 -8, !dbg !52
  %getfield.tag = load atomic volatile i64, ptr %getfield.tag_addr unordered, align 8, !dbg !52, !tbaa !42, !range !45
  %4 = and i64 %getfield.tag, -16, !dbg !52
  %exactly_isa16 = icmp eq i64 %4, ptrtoint (ptr @"+Main.Base.MPFR.MPFRRoundingMode#4211.jit" to i64), !dbg !52
  br i1 %exactly_isa16, label %L18, label %fail17, !dbg !52

L18:                                              ; preds = %L13
  %getfield.unbox = load i32, ptr %getfield, align 4, !tbaa !53, !alias.scope !55, !noalias !56
  %.x.pre = load i32, ptr @"jl_global#4208.jit", align 4, !dbg !57, !tbaa !63, !alias.scope !55, !noalias !56
  br label %L29, !dbg !65

L27:                                              ; preds = %guard_exit, %pass
  %.x9 = load i32, ptr @"jl_global#4208.jit", align 4, !dbg !66, !tbaa !63, !alias.scope !55, !noalias !56
  br label %L29, !dbg !68

L29:                                              ; preds = %L27, %L18
  %.x = phi i32 [ %.x9, %L27 ], [ %.x.pre, %L18 ], !dbg !57
  %value_phi7 = phi i32 [ %.x9, %L27 ], [ %getfield.unbox, %L18 ]
  %5 = icmp eq i32 %value_phi7, %.x, !dbg !69
  %6 = zext i1 %5 to i8, !dbg !69
  %frame.prev44 = load ptr, ptr %frame.prev, align 8, !tbaa !14
  store ptr %frame.prev44, ptr %pgcstack_arg, align 8, !tbaa !14
  ret i8 %6, !dbg !69

fail:                                             ; preds = %top
  call void @ijl_type_error(ptr nonnull @"_j_str_typeassert#1", ptr nonnull @"jl_global#4207.jit", ptr %2), !dbg !20
  unreachable, !dbg !20

pass:                                             ; preds = %top
  %jl_nothing = load ptr, ptr @jl_nothing, align 8, !dbg !71, !tbaa !18, !invariant.load !10, !alias.scope !72, !noalias !73, !nonnull !10
  %.not = icmp eq ptr %2, %jl_nothing, !dbg !71
  br i1 %.not, label %L27, label %guard_exit, !dbg !71

guard_exit:                                       ; preds = %pass
  %gc_slot_addr_036 = getelementptr inbounds nuw i8, ptr %gcframe1, i64 16
  store ptr %2, ptr %gc_slot_addr_036, align 8
  %7 = call swiftcc nonnull ptr @j_get_4209(ptr nonnull swiftself "gcstack" %pgcstack_arg, ptr nocapture readonly %2, ptr nonnull @"jl_global#4210.jit"), !dbg !74
  %.not31 = icmp eq ptr %7, %jl_nothing, !dbg !75
  br i1 %.not31, label %L27, label %L13, !dbg !75

fail17:                                           ; preds = %L13
  store ptr null, ptr %gc_slot_addr_036, align 8
  call void @ijl_type_error(ptr nonnull @"_j_str_typeassert#1", ptr nonnull @"+Main.Base.MPFR.MPFRRoundingMode#4211.jit", ptr nonnull %getfield), !dbg !52
  unreachable, !dbg !52
}
