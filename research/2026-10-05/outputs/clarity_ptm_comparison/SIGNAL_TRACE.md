# Clarity PTM signal trace

Static SH-2A disassembly of supplied stock and ClarityMax images. Latest Pminus5 variant has identical executable bytes.

## Confirmed controller structure

FUN_2A030 uses GBR=FFF879E4. Its mapped target is signed16(*(uint32*)(GBR+108)+6), loaded into r8. FUN_29FB4 writes this field: it clamps the signed word at offset +8 of the object pointed to by FFF87AD8, interpolates the absolute value with X=13810+18*bank and Y=1388E+18*bank, and restores its sign. The output object pointer is stored at FFF87AEC. Raw command origin and physical units remain unresolved.

FUN_2A348 takes scheduling input r4, target r5, feedback-like signal r6, and history r7. The caller obtains feedback from signed16(FFF87A48) and scheduling input from offset +8 of the object pointed to by FFF87AD8. Error e=target-feedback. History is clipped to +/-65536; error-minus-history is clipped to +/-65536 before the D-like gain product.

P gains: Y=13BDC+18*bank; X=13B5E+18*bank. D-like gains: Y=13AE0+18*bank; X=13A62+18*bank. Bank byte is FFF87B7C. Both use the absolute scheduling input and interpolation helper 3ADD6. Products use division by 1024 with negative rounding toward zero. P clamp comes from 1390C (1774 stock,7373 PTM); D clamp from 1390E (333 stock,1774 PTM). Their sum saturates to +/-32767. Caller applies additional scheduled products /256 and final clamp from 13910 (1774 stock,9000 PTM).

PTM 1B81E adds arithmetic_shift_right(45*signed16(mapped_target),10) to the P+D result and saturates +/-32767 before the caller's remaining scaling/clamp stages. This is feedforward-like mapped-target injection, not direct physical torque.

## Correction to earlier interpretation of conditional P shaping

Patch 1B864 reads the same mapped target and uses r11=error and r2=interpolated P gain. However its r4 is NOT reliably the original scheduling input. Helper 3ADD6 does not preserve r4: on interior interpolation segments it leaves r4 holding the lower X breakpoint (3AE12), while endpoint paths leave the incoming input. Thus the patch's 100/500/1800/2800 thresholds operate on path-dependent register state. It cannot be described as a proven smooth schedule versus speed or raw command. The patch also reuses r2 internally; a complete instruction-level boundary test is required to characterize outputs exactly.

## Normalization

FUN_2AF96 reads signed32(FFF88548), multiplies by 3429 stock / 1650 PTM, divides by 256 with signed rounding, writes the unsaturated value through its r4 argument, and returns a +/-32767-saturated value. Producer and physical units of FFF88548 are unresolved.

No firmware edits, hardware execution, or physical calibration performed. P/D describe mathematical structure; engineering units and timing require further producer/history tracing.
