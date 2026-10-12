# RTL Signal Studio 📡

**A Python-based DSP Simulation & Datapath Verification Environment for FPGA Firmware Engineering**

RTL Signal Studio is an interactive Digital Signal Processing (DSP) dashboard designed specifically to bridge the gap between high-level algorithmic simulation and low-level RTL logic design. It allows engineers to dynamically generate wideband signals, apply digital filters, analyze spectral leakage, and export quantized memory files directly into hardware testbenches for FPGA simulation.

## 🎯 Primary Use Cases
* **FPGA Datapath Verification:** Generate stimulus data to verify RTL signal processing modules, such as moving average filters, FIR filters, and XADC interfaces.
* **SAR Pulse Compression Testing:** Simulate synthetic aperture radar (SAR) chirps, apply Hamming/Taylor windowing, and evaluate expected Signal-to-Noise Ratio (SNR) improvements before writing the matched filter logic.
* **BRAM Initialization:** Automatically quantize floating-point signal arrays into 16-bit signed integers and export formatted `.coe` (Xilinx Vivado) and `.mif` (Intel Quartus) files to initialize Block RAM IP cores.

## ✨ Key Features
* **Interactive Signal Generator:** Configure standard waveforms (Sine, Square, Sawtooth) or wideband Chirps with configurable sweep ranges, phase, and amplitude.
* **Dynamic Digital Front-End:** Apply customizable Butterworth filters (Lowpass, Highpass, Bandpass) with adjustable orders to simulate digital signal conditioning.
* **Advanced Spectral Analysis:** Visualize Time-Domain and Frequency-Domain (FFT) data with logarithmic (dB) scaling. Compare windowing functions (Rectangular, Hann, Hamming, Blackman, Taylor, Kaiser) to observe sidelobe suppression and spectral leakage mitigation.
* **Hardware-Ready Export:** 
  * Download raw signal and noise arrays as `.csv` files capped at hardware-friendly depths (e.g., 1024 or 4096 samples).
  * Export automated Markdown (`.md`) test reports documenting the exact filter cutoffs, SNR metrics, and system parameters of a given simulation run.
* **Industry Presets:** Includes 25 built-in parameter presets to instantly simulate real-world data links, ranging from 4 kHz SAR sweeps and 1 kHz FPGA XADC tones to UWB impulse ranging and diagnostic ultrasound.

## 🛠️ Technology Stack
* **Language:** Python 3
* **Framework:** Streamlit (UI & State Management)
* **DSP & Math:** NumPy, SciPy (Signal Processing)
* **Data Visualization:** Plotly (Interactive Charts), Matplotlib
* **Data Handling:** Pandas

## 🚀 Getting Started

### Prerequisites
Ensure you have Python 3.8+ installed along with `pip` and `git`.

### Installation
1. Clone the repository:
   ```bash
   git clone [https://github.com/yourusername/rtl-signal-studio.git](https://github.com/yourusername/rtl-signal-studio.git)
   cd rtl-signal-studio