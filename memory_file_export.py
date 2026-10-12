"""Format normalized signal samples for common FPGA memory initialization files."""

import numpy as np


def _quantized_words(normalized_samples):
    """Quantize float samples as clipped 16-bit two's-complement words."""
    samples = np.asarray(normalized_samples, dtype=np.float64)
    if samples.ndim != 1:
        raise ValueError("Signal samples must be a one-dimensional array.")
    if samples.size == 0:
        raise ValueError("At least one signal sample is required.")
    if not np.all(np.isfinite(samples)):
        raise ValueError("Signal samples must all be finite numbers.")

    quantized = np.rint(samples * 32767)
    quantized = np.clip(quantized, -32768, 32767).astype(np.int64)
    return [int(sample) & 0xFFFF for sample in quantized]


def format_xilinx_coe(normalized_samples):
    """Return a Xilinx .coe memory initialization vector using hexadecimal words."""
    words = _quantized_words(normalized_samples)
    vector = ",\n".join(f"{word:04X}" for word in words)
    return (
        "memory_initialization_radix=16;\n"
        "memory_initialization_vector=\n"
        f"{vector};\n"
    )


def format_mif(normalized_samples):
    """Return a hexadecimal .mif content block with 16-bit data words."""
    words = _quantized_words(normalized_samples)
    address_width = max(4, len(f"{len(words) - 1:X}"))
    contents = "\n".join(
        f"    {address:0{address_width}X} : {word:04X};"
        for address, word in enumerate(words)
    )
    return (
        f"DEPTH = {len(words)};\n"
        "WIDTH = 16;\n"
        "ADDRESS_RADIX = HEX;\n"
        "DATA_RADIX = HEX;\n"
        "CONTENT BEGIN\n"
        f"{contents}\n"
        "END;\n"
    )


def format_readmemh(normalized_samples):
    """Return newline-separated hexadecimal words for Verilog $readmemh."""
    words = _quantized_words(normalized_samples)
    return "".join(f"{word:04X}\n" for word in words)


def format_memory_files(normalized_samples):
    """Return COE, MIF, and generic MEM contents for the same normalized samples."""
    return {
        "coe": format_xilinx_coe(normalized_samples),
        "mif": format_mif(normalized_samples),
        "mem": format_readmemh(normalized_samples),
    }
