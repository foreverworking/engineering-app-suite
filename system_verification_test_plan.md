# RTL Signal Studio – System Verification & Test Plan

## 1. Verification Criteria: Defining "Flawless" Operation
Before deploying the dashboard, the system must pass the following baseline checks for every waveform:
*   **Mathematical Accuracy:** The Frequency Domain (FFT) must display peaks precisely at the configured frequencies. Filter cutoffs must attenuate the signal exactly at the defined thresholds.
*   **Rendering Stability:** The Time Domain plot must cleanly render the waveform without browser lag, freezing, or Moiré rendering artifacts (solid blocks of color).
*   **State Management:** Switching between signals, filter types, and axis scales (Linear/Logarithmic) must instantly clear the previous state and render the new parameters without carrying over ghost data.
*   **Noise & SNR Math:** Injecting Gaussian White Noise must visibly degrade the time-domain signal and scatter the FFT floor. Applying the correct filter must recover the wave shape and yield a Calculated SNR significantly higher than the Target SNR.

## 2. Signal Testing Matrix

| Test ID | Signal Type | Gen. Parameters | Sampling & Time | Noise & Filter | FFT Settings | Expected Verification Results | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | **SAR Chirp** | Sweep: 0 to 4,000 Hz | $F_s$: 1,000,000 Hz<br>Duration: 0.02s | Noise: 10 dB Target<br>Filter: Lowpass (Order 4)<br>Cutoff: 4,500 Hz | Scale: Logarithmic (dB)<br>Window: Hamming<br>X-Max: 5,500 Hz | **Time:** Clear frequency compression (low to high). Amplitude tapered by window.<br>**FFT:** Flat spectral "box" from 0-4kHz, sharp drop-off at 4.5kHz.<br>**Metrics:** Calculated SNR improves to ~17-25 dB. | **PASS** |
| **TC-02** | **Sine Wave** | Frequency: 1,000 Hz | $F_s$: 1,000,000 Hz<br>Duration: 0.005s | Noise: 10 dB Target<br>Filter: Lowpass (Order 4)<br>Cutoff: 2,000 Hz | Scale: Linear<br>Window: None (Rectangular)<br>X-Max: 5,000 Hz | **Time:** Exactly 5 smooth, distinct wave cycles visible.<br>**FFT:** Razor-sharp, single vertical spike exactly at the 1,000 Hz bin.<br>**Metrics:** Filtered trace smoothly tracks the original clean trace. | *Pending* |
| **TC-03** | **Square Wave** | Frequency: 500 Hz | $F_s$: 1,000,000 Hz<br>Duration: 0.01s | Noise: None<br>Filter: Lowpass (Order 4)<br>Cutoff: 1,000 Hz | Scale: Linear or Log<br>Window: None<br>X-Max: 10,000 Hz | **Time:** Sharp rising/falling edges. Filtered trace should show ringing (Gibbs phenomenon).<br>**FFT:** Strong fundamental peak at 500 Hz, with distinct odd harmonics (1.5k, 2.5k, 3.5k). | *Pending* |
| **TC-04** | **Triangle Wave** | Frequency: 500 Hz | $F_s$: 1,000,000 Hz<br>Duration: 0.01s | Noise: None<br>Filter: Disabled | Scale: Logarithmic (dB)<br>Window: None<br>X-Max: 10,000 Hz | **Time:** Clean linear ramps.<br>**FFT:** Odd harmonics present, but rolling off much faster (steeper slope) than the Square Wave harmonics. | *Pending* |