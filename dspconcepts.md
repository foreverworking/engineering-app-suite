# Digital Signal Processing (DSP) Concepts

## 1. The Butterworth Filter & Filter Orders
A Butterworth filter is a type of signal processing filter designed to have as flat a frequency response as possible in the passband. In radar and SAR, it acts as a digital front-door, stripping away high-frequency noise before complex processing begins.

**Filter Order (The "Steepness of the Cliff"):**
The order of a filter determines how aggressively it cuts off unwanted frequencies. 
* A **low order (e.g., 2)** creates a gentle slope; some noise outside the cutoff frequency will still leak through.
* A **high order (e.g., 8)** creates a sheer cliff face, sharply blocking any frequencies beyond the cutoff. 

## 2. Fast Fourier Transform (FFT) & Spectral Leakage
The FFT is an algorithm that computes the Discrete Fourier Transform of a sequence, converting a signal from its original time domain into a representation in the frequency domain. 

**Spectral Leakage** occurs when a signal being analyzed by an FFT does not have an integer number of periods within the observation window. The sharp, abrupt start and end points of the sample slice act like artificial square waves, causing the signal's energy to "leak" or smear into adjacent frequencies, hiding smaller legitimate signals.

## 3. Windowing Functions & Sidelobes
To combat spectral leakage, we apply **Windowing Functions**. A window tapers the beginning and end of the signal down to zero, smoothing out the abrupt edges before the FFT is applied.

However, windowing creates **Sidelobes**—echoes or ripples in the frequency spectrum that flank the main signal peak.
* **Ideal Sidelobe Levels:** In SAR, you want sidelobes to be mathematically as low as possible (e.g., $-40$ dB to $-50$ dB) so that a bright radar reflection (like a metal ship) doesn't create ghosts that hide a small target (like a wooden boat). 
* **Viewing them:** You must view sidelobes on a **Logarithmic (dB) Y-Axis**. On a linear scale, they are too small to see.

**Window Comparisons:**
* **Rectangular:** No tapering. Terrible spectral leakage, huge sidelobes. 
* **Hann / Blackman:** Smooth tapering, good for general purpose audio or bio-signals.
* **Hamming:** The historical standard for radar. It mathematically balances sharpening the main lobe while suppressing the highest sidelobes (down to about $-43$ dB).
* **Taylor & Kaiser:** Advanced, parameterized windows used heavily in modern SAR. They allow engineers to manually dictate the exact acceptable sidelobe level (e.g., forcing them below $-50$ dB).

## 4. Signal-to-Noise Ratio (SNR) in SAR
SNR is the ratio of meaningful signal power to background noise power. 
* **Digital SNR:** Calculated purely on the arrays (Signal Power / Noise Power). Filtering noise increases this slightly.
* **SAR Physical SNR:** Governed by the Radar Equation (factoring in transmitter power, range, antenna gain, and thermal noise). SAR echoes often return with an SNR below 0 dB (buried in noise).
* **Pulse Compression Gain:** The Matched filter in a SAR system compresses the wideband chirp into a single spike, boosting the output SNR by 20 to 30 dB.

## 5. Matched Filters & RRC Filters
While a Butterworth filter just cleans up general noise, a **Matched Filter** is a specialized radar tool designed to detect a specific known template (like your transmitted chirp) within a sea of noise. It is the engine of SAR pulse compression. Root-Raised-Cosine (RRC) filters are similar, often used in digital communications to prevent Inter-Symbol Interference (ISI).

## 6. Dashboard Parameters Explained
* **Sampling Frequency (Hz):** The rate at which the analog signal is digitized (Nyquist theorem dictates it must be $>2x$ the highest frequency).
* **Signal Type & Frequency:** The core shape (Sine, rectangular/square, triangle, sawtooth, or chirp) and its oscillation speed.
* **Duration & Phase:** How long the signal lasts and its starting angle.
* **Noise Profile & SNR:** Injects Gaussian white noise to simulate real-world atmospheric and thermal interference.

## 7. Real-World Applications & Parametric Signal Presets

The following table provides exact parameter presets to simulate standard industry signals in your Streamlit dashboard. These values are optimized for digital simulation environments.

| Domain | Application | Signal Type | Frequency | Amplitude | Noise / SNR | Filter (Cutoff) | Window |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **Radar** | Synthetic Aperture Radar (SAR) | Chirp | 4 kHz (Sweep) | 1.0 | Gaussian / 10 dB | Lowpass (4.5 kHz) | Hamming |
| **Hardware** | FPGA XADC Datapath Verification | Sine | 1 kHz | 0.8 | Gaussian / 20 dB | Lowpass (1.5 kHz) | Hann |
| **Space** | Satellite Payload Telemetry | Square | 5 kHz | 1.0 | Gaussian / 5 dB | Bandpass | Taylor |
| **Audio** | Subwoofer / Acoustics Testing | Sine | 60 Hz | 1.0 | None | None | Rectangular |
| **Medical** | Medical Bio-Signal (ECG Sim) | Sawtooth | 1.5 Hz | 0.5 | Gaussian / 15 dB | Lowpass (5 Hz) | Blackman |
| **Medical** | Diagnostic Ultrasound (Deep) | Chirp | 3 MHz | 2.0 | Gaussian / 12 dB | Bandpass (3 MHz) | Kaiser |
| **Medical** | Pulse Oximeter (Heart Rate) | Sine | 1.2 Hz | 1.0 | Gaussian / 10 dB | Lowpass (3 Hz) | Hann |
| **Medical** | Hearing Aid (Vocal Range) | Sine | 1 kHz | 0.5 | Gaussian / 5 dB | Bandpass (300-3k) | Hamming |
| **Medical** | Fetal Heart Monitor (Doppler) | Sine | 2.5 Hz | 0.8 | Gaussian / 8 dB | Lowpass (5 Hz) | Blackman |
| **Medical** | Continuous Glucose Monitor (CGM) | Square (Step)| 0.001 Hz | 1.0 | Gaussian / 20 dB | Lowpass (0.01Hz) | Rectangular |
| **Medical** | MRI Scanner (RF Coil Data) | Chirp | 64 MHz | 1.0 | Gaussian / 15 dB | Lowpass (65 MHz) | Kaiser |
| **Consumer** | Active Noise Canceling (ANC) | Sine | 120 Hz | 1.0 | Gaussian / 0 dB | Lowpass (500 Hz) | Hann |
| **Consumer** | Voice Assistant (VAD) | Sine | 300 Hz | 0.7 | Gaussian / 10 dB | Highpass (80 Hz) | Hamming |
| **Consumer** | MP3 / AAC Audio Compression | Sine | 15 kHz | 1.0 | Gaussian / 30 dB | Lowpass (16 kHz) | Hann |
| **Consumer** | Touchscreen Display (Capacitive)| Square | 10 Hz | 1.0 | Gaussian / 15 dB | Lowpass (50 Hz) | Hann |
| **Infra** | Apple AirTags (UWB Ranging) | Chirp (Impulse)| 6.5 GHz | 0.3 | Gaussian / 2 dB | Bandpass (Wide) | Taylor |
| **Infra** | Keyless Car Entry (Anti-Relay) | Chirp (Impulse)| 433 MHz | 0.5 | Gaussian / 5 dB | Bandpass | Taylor |
| **Infra** | Smart Electricity Meters | Sine | 50/60 Hz | 1.0 | Gaussian / 25 dB | Lowpass (100 Hz) | Rectangular |
| **Infra** | Anti-Lock Braking Systems (ABS)| Square | 50 Hz | 1.0 | Gaussian / 15 dB | Lowpass (100 Hz) | Hann |
| **Infra** | Seismic Oil Exploration | Chirp | 10 - 100 Hz | 5.0 | Gaussian / 5 dB | Lowpass (150 Hz) | Hamming |
| **Sea/Space**| Submarine Active Sonar | Chirp | 3 kHz | 2.0 | Gaussian / 0 dB | Bandpass | Hamming |
| **Sea/Space**| Acoustic Doppler Current Profiler| Chirp | 300 kHz | 1.0 | Gaussian / 5 dB | Bandpass | Kaiser |
| **Sea/Space**| GPS Receiver (Satellite Nav) | Sine (BPSK) | 1.575 GHz | 0.1 | Gaussian / -20 dB| Bandpass | Taylor |
| **Sea/Space**| Deep Space Telemetry (X-band) | Square | 8 GHz | 1.0 | Gaussian / -5 dB | Bandpass | Taylor |
| **Sea/Space**| Radio Astronomy (CMB) | Noise | 1.4 GHz | 0.1 | Gaussian / -30 dB| Lowpass (1.5 GHz)| Kaiser |