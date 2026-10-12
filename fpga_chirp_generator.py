import numpy as np
import scipy.signal as signal
import os

def generate_fpga_chirp(num_samples=1024, fs_mhz=100.0, f_start_mhz=0.0, f_end_mhz=20.0):
    """
    Generates a SAR chirp signal optimized for FPGA BRAM sizing.
    
    Parameters:
    - num_samples: Total memory depth (e.g., 1024, 2048, 4096 words for BRAM).
    - fs_mhz: Hardware sampling frequency in MHz (Clock speed of the ADC/FPGA).
    - f_start_mhz: Starting frequency of the chirp in MHz.
    - f_end_mhz: Ending frequency of the chirp in MHz.
    
    Returns:
    - numpy array of floating-point signal values between -1.0 and 1.0.
    """
    fs = fs_mhz * 1e6
    f_start = f_start_mhz * 1e6
    f_end = f_end_mhz * 1e6
    
    # Calculate duration based on the number of samples needed for the BRAM
    duration = num_samples / fs
    
    # Create the time vector
    t = np.arange(0, duration, 1/fs)
    
    # Generate the linear sweep chirp
    # Note: We slice to exact num_samples in case of floating point rounding errors in arange
    t = t[:num_samples] 
    chirp_signal = signal.chirp(t, f0=f_start, f1=f_end, t1=duration, method='linear')
    
    return chirp_signal

def quantize_for_hardware(sig_float, bit_width=16):
    """
    Converts a normalized floating-point signal (-1.0 to 1.0) into 
    signed integer values representing fixed-point 2's complement hardware format.
    """
    # For a signed N-bit integer, the max positive value is (2^(N-1)) - 1
    # Example: 16-bit max is 32767, min is -32768
    max_val = (1 << (bit_width - 1)) - 1
    
    # Scale the float signal
    scaled_sig = sig_float * max_val
    
    # Round to the nearest integer
    quantized_sig = np.round(scaled_sig).astype(int)
    
    # Clip to ensure no overflow just in case
    min_val = -(1 << (bit_width - 1))
    quantized_sig = np.clip(quantized_sig, min_val, max_val)
    
    return quantized_sig

def to_hex_2s_complement(value, bit_width):
    """
    Safely formats a signed integer as a 2's complement hexadecimal string.
    """
    # Create a mask of 1s for the given bit width (e.g., 16 bits = 0xFFFF)
    mask = (1 << bit_width) - 1
    # Apply mask and format to padded hex
    hex_chars = bit_width // 4
    return f"{(value & mask):0{hex_chars}X}"

def write_coe_file(filename, quantized_sig, bit_width):
    """
    Writes a .coe (Coefficient) file for Xilinx Vivado Block Memory Generator.
    """
    with open(filename, 'w') as f:
        f.write("; FPGA SAR Chirp Signal Initialization File\n")
        f.write(f"; Bit Width: {bit_width}, Depth: {len(quantized_sig)}\n")
        f.write("memory_initialization_radix=16;\n")
        f.write("memory_initialization_vector=\n")
        
        for i, val in enumerate(quantized_sig):
            hex_val = to_hex_2s_complement(val, bit_width)
            if i == len(quantized_sig) - 1:
                f.write(f"{hex_val};\n") # Last element ends with semicolon
            else:
                f.write(f"{hex_val},\n") # Comma separated
    print(f"[Success] Xilinx Vivado .coe file saved: {filename}")

def write_mif_file(filename, quantized_sig, bit_width):
    """
    Writes a .mif (Memory Initialization File) for Intel/Altera Quartus Prime.
    """
    depth = len(quantized_sig)
    with open(filename, 'w') as f:
        f.write(f"-- FPGA SAR Chirp Signal Initialization File\n")
        f.write(f"DEPTH = {depth};\n")
        f.write(f"WIDTH = {bit_width};\n")
        f.write("ADDRESS_RADIX = UNS;\n")
        f.write("DATA_RADIX = HEX;\n")
        f.write("CONTENT BEGIN\n")
        
        for address, val in enumerate(quantized_sig):
            hex_val = to_hex_2s_complement(val, bit_width)
            # Format: <address> : <data>;
            f.write(f"    {address:<4} : {hex_val};\n")
            
        f.write("END;\n")
    print(f"[Success] Intel Quartus .mif file saved: {filename}")

if __name__ == "__main__":
    print("--- FPGA BRAM SAR Chirp Generator ---")
    
    # 1. Define Hardware Constants
    BRAM_DEPTH = 1024      # Number of samples (standard FPGA block RAM size)
    BIT_WIDTH = 16         # 16-bit signed integer (ADC/DAC resolution)
    FS_MHZ = 100.0         # 100 MHz sampling clock
    START_FREQ_MHZ = 0.0   # Chirp start
    END_FREQ_MHZ = 20.0    # Chirp end (20 MHz)
    
    # 2. Generate perfect mathematical signal
    print(f"Generating {BRAM_DEPTH} samples for {FS_MHZ} MHz clock...")
    float_chirp = generate_fpga_chirp(
        num_samples=BRAM_DEPTH, 
        fs_mhz=FS_MHZ, 
        f_start_mhz=START_FREQ_MHZ, 
        f_end_mhz=END_FREQ_MHZ
    )
    
    # 3. Quantize for hardware
    print(f"Quantizing signal to {BIT_WIDTH}-bit signed fixed-point...")
    quantized_chirp = quantize_for_hardware(float_chirp, bit_width=BIT_WIDTH)
    
    # 4. Export BRAM files
    write_coe_file("sar_chirp_1024.coe", quantized_chirp, bit_width=BIT_WIDTH)
    write_mif_file("sar_chirp_1024.mif", quantized_chirp, bit_width=BIT_WIDTH)
    
    print("Done! You can now import these files into your FPGA project's ROM/BRAM IP.")