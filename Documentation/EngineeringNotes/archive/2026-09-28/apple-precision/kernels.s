	.build_version macos, 27, 0	sdk_version 27, 0
	.section	__TEXT,__text,regular,pure_instructions
	.globl	_main                           ; -- Begin function main
	.p2align	2
_main:                                  ; @main
; %bb.0:
	mov	w0, #0                          ; =0x0
	ret
                                        ; -- End function
	.globl	_$s22PrecisionHardwareProbe9scalarFMAyS2d_S2dtF ; -- Begin function $s22PrecisionHardwareProbe9scalarFMAyS2d_S2dtF
	.p2align	2
_$s22PrecisionHardwareProbe9scalarFMAyS2d_S2dtF: ; @"$s22PrecisionHardwareProbe9scalarFMAyS2d_S2dtF"
; %bb.0:
	fmadd	d0, d1, d2, d0
	ret
                                        ; -- End function
	.globl	_$s22PrecisionHardwareProbe9vectorFMAys5SIMD2VySdGAE_A2EtF ; -- Begin function $s22PrecisionHardwareProbe9vectorFMAys5SIMD2VySdGAE_A2EtF
	.p2align	2
_$s22PrecisionHardwareProbe9vectorFMAys5SIMD2VySdGAE_A2EtF: ; @"$s22PrecisionHardwareProbe9vectorFMAys5SIMD2VySdGAE_A2EtF"
; %bb.0:
	fmla.2d	v0, v2, v1
	ret
                                        ; -- End function
	.globl	_$s22PrecisionHardwareProbe15separateProductyS2d_S2dtF ; -- Begin function $s22PrecisionHardwareProbe15separateProductyS2d_S2dtF
	.p2align	2
_$s22PrecisionHardwareProbe15separateProductyS2d_S2dtF: ; @"$s22PrecisionHardwareProbe15separateProductyS2d_S2dtF"
; %bb.0:
	fmul	d1, d1, d2
	fadd	d0, d0, d1
	ret
                                        ; -- End function
	.section	__TEXT,__swift5_entry,regular,no_dead_strip
	.p2align	2, 0x0                          ; @"\01l_entry_point"
l_entry_point:
	.long	_main-l_entry_point
	.long	0                               ; 0x0

	.private_extern	___swift_reflection_version ; @__swift_reflection_version
	.section	__TEXT,__const
	.globl	___swift_reflection_version
	.weak_definition	___swift_reflection_version
	.p2align	1, 0x0
___swift_reflection_version:
	.short	3                               ; 0x3

	.no_dead_strip	l_entry_point
	.no_dead_strip	_$s22PrecisionHardwareProbe15separateProductyS2d_S2dtF
	.no_dead_strip	_$s22PrecisionHardwareProbe9scalarFMAyS2d_S2dtF
	.no_dead_strip	_$s22PrecisionHardwareProbe9vectorFMAys5SIMD2VySdGAE_A2EtF
	.no_dead_strip	___swift_reflection_version
	.no_dead_strip	_main
	.linker_option "-lswift_Concurrency"
	.linker_option "-lswiftCore"
	.linker_option "-lswift_StringProcessing"
	.linker_option "-lobjc"
	.section	__DATA,__objc_imageinfo,regular,no_dead_strip
L_OBJC_IMAGE_INFO:
	.long	0
	.long	100927296

.subsections_via_symbols
