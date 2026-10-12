# Engineering App Suite

Welcome to the Engineering App Suite

This repository houses a collection of bespoke software tools designed for aerospace systems, FPGA firmware verification, and digital signal processing (DSP). Built to bridge the gap between high-level system architecture and physical RTL logic design, these applications simulate real-world engineering environments.

## Current applications

- **RTL Signal Studio:** An interactive DSP simulation and datapath verification environment that generates quantized `.coe`, `.mif`, and `.mem` memory files for hardware testbenches.

## RTL Signal Studio

A Streamlit-based DSP dashboard for exploring signal generation, noise injection, digital filtering, and FFT-based frequency analysis.

### Features

- Generate sine, square, sawtooth, linear chirp, and SAR chirp signals
- Apply rectangular, Taylor, or Kaiser pulse tapering to SAR chirps
- Configure the sampling frequency from 100 Hz to 1 GHz using Hz, kHz, MHz, or GHz input (for example, `250M` or `1G`); the dashboard converts the entry to Hz
- Configure the recording duration from 0 to 5 seconds and view the calculated sample count in the sidebar; generation is capped at one million samples, with a two-sample minimum for DSP analysis
- Combine up to three independently enabled signal components, each with adjustable type, frequency, amplitude, and phase
- Add Gaussian or uniform white noise at a target SNR, or bypass noise
- Apply lowpass, highpass, bandpass, or bandstop Butterworth filters, or bypass filtering
- Independently select rectangular, Hamming, Hann, Blackman, Taylor, or Kaiser FFT analysis windows
- Set the lower and upper FFT display frequencies in the sidebar to zoom in on a signal, with the range capped at the sampling Nyquist frequency
- Tune Taylor `nbar` and sidelobe level, or Kaiser `beta`, separately for SAR pulse tapering and FFT analysis
- Adjust parameters with synchronized sliders and numeric value fields
- Inspect the time-domain and frequency-domain response
- View the full recording in the time-domain plot; the trace is downsampled only when needed to keep rendering responsive
- Choose between the current stacked graph layout or a side-by-side time/frequency comparison from Visualization Settings
- Zoom, pan, and reset each interactive Plotly chart; use its camera toolbar button to save a high-resolution PNG screenshot
- Change the clean, noisy, and filtered trace colors from the sidebar
- Display sampling rate, target SNR, and calculated output SNR as live metrics above the charts
- Keep a compact sticky settings bar below the dashboard title with Signal highlighted first, followed by sweep, cutoff, noise, and filter; sampling rate remains in the metric row
- Switch between coordinated light and dark themes from Streamlit's app menu under Settings → Theme
- Download a CSV recording containing every generated sample and the clean, noisy, and filtered signal values
- Export up to 16,384 time/clean/noisy samples for testbenches and download a dynamic Markdown DSP analysis report
- Export a selected clean, noisy, or filtered signal as Xilinx `.coe`, Intel/Altera `.mif`, or generic Verilog `$readmemh` `.mem`
- Compare clean vs. filtered signal spectra
- Compare input and output SNR in a dedicated chart
- Show live interpretations for each graph in readable full-width sections below the time/frequency plots, including time-domain levels and dominant spectrum peaks (enabled by default)
- Group system/sampling and signal generation inside a collapsible "Signal and generation" sidebar section, with nested dropdowns for each component; keep channel/noise, digital filter, and spectral analysis in subsequent datapath-order sections
- Keep signal-path and analysis controls in the sidebar while the main area displays charts and optional live interpretations

### Requirements

This project uses Python 3.10+, Streamlit, NumPy, SciPy, Plotly, and Pandas.

### Setup

From the project root:

```bash
python -m venv venv
# Windows PowerShell
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Run the app

```bash
streamlit run signal_analysis_dashboard.py
```

### Notes

- The dashboard is designed for interactive experimentation in a browser.
- Both light and dark theme palettes are configured in `.streamlit/config.toml`; open the top-right app menu, choose **Settings**, then select a theme. Theme configuration changes may require restarting the Streamlit server.
- If you change filter cutoff values, keep them below the Nyquist frequency for your selected sampling rate.
- FPGA memory exports peak-normalize the selected record to `[-1, 1]`, then quantize to 16-bit signed two's complement. Microchip/Microsemi memory initialization extensions depend on the selected Libero IP flow; `.mem`, `.hex`, or `.mif` may be accepted, so confirm the target core's supported format.
- `memory_file_export.py` contains the reusable formatter functions. The `.mem` output is raw hexadecimal for Verilog `$readmemh`; the `.mif` format is commonly used by Intel/Altera tools. Microchip/Microsemi Libero IP may accept `.mem`, `.hex`, or `.mif` depending on the generated core and configuration.
