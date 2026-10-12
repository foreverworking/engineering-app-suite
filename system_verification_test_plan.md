# RTL Signal Studio - System Verification & Test Plan

## 1. Verification Criteria

Run the waveform cases with one enabled component at a time, noise disabled, and filtering disabled unless a case explicitly enables them. Confirm the selected settings are reflected in the summary bar and that switching waveforms does not leave stale traces or settings.

* **Waveform accuracy:** Confirm the time-domain shape, configured frequency, amplitude, and phase. For periodic signals, use a record containing an integer number of cycles to make FFT-bin expectations deterministic.
* **FFT behavior:** Confirm peaks and harmonic patterns at the expected frequencies. The FFT window affects spectral leakage and magnitude; it does not taper the generated time-domain signal.
* **Filter behavior:** A Butterworth design's single-pass cutoff is the -3 dB point, not a brick-wall boundary. This app applies zero-phase forward/backward filtering, so the effective magnitude at that cutoff is approximately -6 dB. Verify passband/stopband behavior with suitable tones and inspect the plotted frequency response.
* **Noise and SNR:** Check that enabling noise visibly changes the input and that the measured input SNR is near the selected target within a practical tolerance. Output SNR improvement depends on how much noise lies outside the filter passband; do not require one fixed output-SNR range for every signal.
* **Rendering and state:** Confirm both plots render, their axes and labels are visible, controls remain usable, and switching signal types updates the plots without stale data.
* **Sample limit:** Keep each case at or below 1,000,000 generated samples.

## 2. Waveform Test Matrix

For the following cases, use the listed values explicitly in the sidebar rather than relying on a previous run's control state. FFT X-axis minimum is 0 Hz for every case.

| Test ID | Signal type | Generation parameters | Sampling and record | Noise and filter | FFT settings | Expected results | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **TC-01** | Sine | Frequency: 1,000 Hz; amplitude: 1; phase: 0 rad | $F_s$: 20,000 Hz; duration: 0.01 s; 200 samples; 10 cycles | Noise: None; filter: None | Rectangular window; Linear Magnitude; X-max: 5,000 Hz | Time plot is a 1,000 Hz sinusoid between -1 and +1. FFT has a dominant peak at the 1,000 Hz bin (100 Hz bin spacing), with no harmonics for the ideal clean sine. | **Verified** |
| **TC-02** | Rectangle (Square) | Frequency: 500 Hz; amplitude: 1; phase: 0 rad | $F_s$: 20,000 Hz; duration: 0.02 s; 400 samples; 10 cycles | Noise: None; filter: None | Rectangular window; Linear Magnitude; X-max: 5,000 Hz | Time plot has a 50% duty-cycle, two-level waveform at approximately -1 and +1. It starts at +1 at phase zero. FFT has a fundamental at 500 Hz and odd harmonics (1.5 kHz, 2.5 kHz, ...); even harmonics are strongly suppressed, allowing small discrete-sampling residuals. | **Verified** |
| **TC-03** | Triangle | Frequency: 500 Hz; amplitude: 1; phase: 0 rad | $F_s$: 20,000 Hz; duration: 0.02 s; 400 samples; 10 cycles | Noise: None; filter: None | Rectangular window; Linear Magnitude; X-max: 5,000 Hz | Time plot has symmetric linear rising and falling ramps between approximately -1 and +1; at phase zero it starts at -1. FFT has odd harmonics whose amplitudes decrease approximately as 1/n^2. | **Verified** |
| **TC-04** | Sawtooth | Frequency: 500 Hz; amplitude: 1; phase: 0 rad | $F_s$: 20,000 Hz; duration: 0.02 s; 400 samples; 10 cycles | Noise: None; filter: None | Rectangular window; Linear Magnitude; X-max: 5,000 Hz | Time plot has a linear ramp and abrupt reset each period, between approximately -1 and +1; it starts at -1 at phase zero. FFT has the fundamental and both odd and even harmonics, with harmonic amplitudes decreasing approximately as 1/n. | **Verified** |
| **TC-05** | Chirp | Linear sweep: 0 to 4,000 Hz; amplitude: 1; phase: 0 rad | $F_s$: 20,000 Hz; duration: 0.02 s; 400 samples | Noise: None; filter: None | Hamming window; Logarithmic (dB); X-max: 5,000 Hz | Time plot shows an increasing instantaneous frequency over the full record. Chirp bandwidth is 4,000 Hz. FFT energy is distributed over the swept band rather than appearing as one tone peak; Hamming reduces leakage and broadens spectral peaks. | **Verified** |
| **TC-06** | SAR Chirp | Linear sweep: 0 to 4,000 Hz; amplitude: 1; phase: 0 rad; SAR pulse window: Taylor; nbar: 4; sidelobe level: 30 dB | $F_s$: 1,000,000 Hz; duration: 0.02 s; 20,000 samples | Noise: None; filter: None | Hamming window; Logarithmic (dB); X-max: 5,000 Hz | Time plot shows the chirp across the full record with the selected Taylor pulse taper applied. FFT energy spans the 4,000 Hz sweep; the selected pulse taper and the separate Hamming FFT window affect spectral sidelobes/leakage. Verify labels identify the SAR chirp and configured sweep. | **Verified** |

## 3. Filter and Noise Checks

| Test ID | Setup | Expected verification results | Status |
| :--- | :--- | :--- | :--- |
| **TC-07** | Sine, 1,000 Hz, amplitude 1; $F_s$: 20,000 Hz; duration: 0.02 s; Gaussian White noise; target SNR: 10 dB; Lowpass Butterworth order 4; cutoff: 2,000 Hz; Rectangular FFT window. Also check a clean 2,000 Hz sine with the same filter to measure cutoff gain. | Input SNR is close to the 10 dB target within measurement tolerance. The 1,000 Hz tone remains in the passband. The zero-phase forward/backward filter has effective gain near 0.5 (approximately -6 dB) at the 2,000 Hz cutoff; the single-pass Butterworth design is -3 dB there. Frequencies above cutoff are attenuated; the response is not an abrupt brick-wall cutoff. | **Verified** |
| **TC-08** | Rectangle (Square), 500 Hz, amplitude 1; $F_s$: 20,000 Hz; duration: 0.02 s; no noise; Lowpass Butterworth order 4; cutoff: 1,000 Hz; Rectangular FFT window | Fundamental remains in the passband while higher odd harmonics are increasingly attenuated. The filtered time waveform has rounded edges; inspect for ringing without requiring an exact overshoot amount. | **Verified** |
| **TC-09** | In one component control, switch sequentially through Sine, Rectangle (Square), Triangle, Sawtooth, Chirp, and SAR Chirp; then disable and re-enable the component | The plot traces, spectrum, and summary update to the current selection. No prior waveform remains in the combined signal when it is replaced or disabled; re-enabling restores the selected waveform. | **Verified** |

## 4. Review Notes

* Previous TC-01 was marked PASS without reproducible verification evidence. The revised sine case was executed and its measurements are recorded in Section 5. Its Hamming window is explicitly the FFT analysis window. SAR pulse taper is tested separately using a supported SAR window.
* Previous TC-02 used a 1 MHz sampling rate for a 1 kHz sine, which made the sample count unnecessarily large and its claimed exact 1 kHz FFT-bin match incorrect for the listed duration. The revised settings use 20 kHz sampling and an integer-cycle record.
* Previous square-wave coverage maps to the current **Rectangle (Square)** option.
* Previous triangle expectations described amplitude tapering caused by an FFT window. The FFT window does not change the time-domain signal; the revised Triangle case checks the generated ramps and the approximate 1/n^2 harmonic envelope.
* Sawtooth was listed as a supported waveform but had no dedicated case; TC-04 adds coverage for its reset edge and both odd and even harmonics.
* All listed cases were exercised on 2026-10-12 using Streamlit AppTest; measured outcomes are in Section 5.

## 5. Verification Results

### TC-01 - Sine - 2026-10-12

**Execution:** Streamlit AppTest against the dashboard with one enabled Sine component.

| Measurement | Observed result | Check |
| :--- | :--- | :--- |
| Sampling rate / duration / samples | 20,000 Hz / 0.01 s / 200 samples | Pass |
| Last sample time | 0.00995 s | Pass |
| Frequency resolution | 100 Hz | Pass |
| Time-domain minimum / maximum | -1.0 / +1.0 | Pass |
| Dominant non-DC FFT bin / magnitude | 1,000 Hz / 1.0 | Pass |
| Noise / filter | None / None | Pass |
| FFT window / scale / X-axis maximum | Rectangular / Linear Magnitude / 5,000 Hz | Pass |
| Streamlit exceptions | None | Pass |

**Result:** Verified. All measured values matched the TC-01 setup and expected outcomes.

### TC-02 through TC-09 - 2026-10-12

**Execution:** Streamlit AppTest with the parameters listed in Section 2 and Section 3. Time and FFT Plotly trace data were decoded and checked; each run completed with no Streamlit exceptions.

| Test ID | Observed results | Result |
| :--- | :--- | :--- |
| TC-02 | 400 samples; time range -1 to +1; 500 Hz FFT bin; 50 Hz resolution. Magnitudes at 500/1,000/1,500/2,000/2,500 Hz: 1.27125 / 0.04000 / 0.41845 / 0.04000 / 0.24471. Odd harmonics dominate; sampled even-harmonic residuals are about 3.1% of the fundamental. | Verified |
| TC-03 | 400 samples; time starts at -1 and ranges -1 to +1; 500 Hz FFT bin; 50 Hz resolution. Magnitudes at 500/1,000/1,500/2,000/2,500 Hz: 0.81224 / ~0 / 0.09175 / ~0 / 0.03414. Odd-harmonic ratios agree with 1/n^2 decay. | Verified |
| TC-04 | 400 samples; time starts at -1 and ranges -1 to +1; 500 Hz FFT bin; 50 Hz resolution. Magnitudes at 500/1,000/1,500/2,000/2,500 Hz: 0.63657 / 0.31821 / 0.21207 / 0.15900 / 0.12717, matching the expected 1/n envelope and including even harmonics. | Verified |
| TC-05 | 400 samples through 0.01995 s; 50 Hz FFT resolution; time amplitude -1 to +1; Hamming/log-dB selected; displayed range 0–5,000 Hz. About 99.988% of measured spectral power fell at or below the 4,000 Hz sweep end. | Verified |
| TC-06 | 20,000 generated samples (5,000 rendered points) through 0.019996 s; 50 Hz FFT resolution; Taylor SAR pulse window selected; Hamming/log-dB selected; displayed range 0–5,000 Hz. First rendered sample magnitude was 0.2431 versus a peak magnitude of 1.0000; about 99.999% of measured spectral power fell at or below 4,000 Hz. | Verified |
| TC-07 | Measured input SNR: 9.984 dB for 10 dB target. Clean tone peak remained at 1,000 Hz. Input noise error power: 0.05018; post-filter error power: 0.01040. | Verified |
| TC-08 | Filtered spectrum retained its dominant 500 Hz bin. Filtered magnitudes at 500/1,500/2,500 Hz: 1.26684 / 0.03390 / 0.01262. Maximum adjacent-sample step decreased from 2.0000 to 0.2114, confirming rounded edges and harmonic attenuation. | Verified |
| TC-09 | Sequentially selected Sine, Rectangle (Square), Triangle, Sawtooth, Chirp, and SAR Chirp in the same component; every selection appeared in the summary and generated 400 nonzero samples with peak magnitude 1. Disabling the component produced an all-zero trace (maximum absolute value 0); re-enabling restored the selected waveform (peak magnitude 1). No Streamlit exceptions. | Verified |

**Result:** TC-02 through TC-09 passed their configured checks. TC-07's measured input SNR was within 0.02 dB of its target. A clean 2,000 Hz test tone at the 2,000 Hz cutoff had measured effective gain 0.49998 (-6.021 dB), consistent with the app's forward/backward zero-phase filtering.
