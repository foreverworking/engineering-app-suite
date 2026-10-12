"""
Signal Analysis Dashboard
-------------------------
A comprehensive web-based dashboard built with Streamlit to demonstrate
core Digital Signal Processing (DSP) concepts. 
Users can generate synthetic signals, add noise, apply digital filters,
and perform frequency-domain analysis (FFT) interactively.
"""

import io
import re

import streamlit as st
import numpy as np
import pandas as pd
import scipy.signal as signal
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from memory_file_export import format_memory_files

# Configure Streamlit page
st.set_page_config(
    page_title="RTL Signal Studio",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)


def hide_streamlit_footer():
    """Hide the Streamlit footer while leaving app settings accessible."""
    st.markdown(
        """
        <style>
        footer {visibility: hidden;}
        </style>
        """,
        unsafe_allow_html=True,
    )


hide_streamlit_footer()


# --- DSP Helper Functions ---
def parse_sampling_frequency(value):
    """Convert a frequency string with optional SI suffixes to integer Hz."""
    match = re.fullmatch(
        r"\s*(\d+(?:\.\d*)?|\.\d+)\s*([KMG]?)\s*(?:HZ)?\s*",
        value,
        flags=re.IGNORECASE,
    )
    if match is None:
        raise ValueError("Enter a frequency such as 1000, 250M, or 1G.")

    multiplier = {"": 1, "K": 1_000, "M": 1_000_000, "G": 1_000_000_000}
    frequency_hz = float(match.group(1)) * multiplier[match.group(2).upper()]
    if not np.isfinite(frequency_hz) or not frequency_hz.is_integer():
        raise ValueError("The converted sampling frequency must be a whole number of Hz.")
    return int(frequency_hz)


@st.cache_data
def generate_signal(
    sig_type,
    freq,
    amp,
    duration,
    fs,
    phase=0,
    chirp_window="Rectangular",
    taylor_nbar=4,
    taylor_sll=30,
    kaiser_beta=8.6,
):
    """Generates various synthetic base signals."""
    sample_count = max(1, int(round(duration * fs)))
    t = np.arange(sample_count) / fs
    omega = 2 * np.pi * freq
    
    if sig_type == 'Sine':
        return t, amp * np.sin(omega * t + phase)
    elif sig_type == 'Square':
        return t, amp * signal.square(omega * t + phase)
    elif sig_type == 'Sawtooth':
        return t, amp * signal.sawtooth(omega * t + phase)
    elif sig_type == 'Chirp':
        return t, amp * signal.chirp(
            t, f0=0, f1=freq, t1=duration, method='linear',
            phi=np.degrees(phase)
        )
    elif sig_type == 'SAR Chirp':
        chirp = signal.chirp(
            t, f0=0, f1=freq, t1=duration, method='linear',
            phi=np.degrees(phase)
        )
        if chirp_window == "Taylor":
            pulse_window = signal.windows.taylor(
                sample_count, nbar=taylor_nbar, sll=taylor_sll, norm=True
            )
        elif chirp_window == "Kaiser":
            pulse_window = signal.windows.kaiser(sample_count, beta=kaiser_beta)
        else:
            pulse_window = np.ones(sample_count)
        return t, amp * chirp * pulse_window
    else:
        return t, np.zeros_like(t)


@st.cache_data
def add_noise(sig, noise_type, snr_db):
    """Adds noise to a signal based on a target Signal-to-Noise Ratio (SNR)."""
    # Calculate signal power
    sig_power = np.mean(sig**2)
    
    if sig_power == 0:
         return sig # Can't add relative noise to a zero signal
         
    # Calculate target noise power based on SNR
    sig_power_db = 10 * np.log10(sig_power)
    noise_power_db = sig_power_db - snr_db
    noise_power = 10**(noise_power_db / 10)
    
    if noise_type == 'Gaussian White':
        noise = np.sqrt(noise_power) * np.random.randn(len(sig))
    elif noise_type == 'Uniform':
        amplitude = np.sqrt(3 * noise_power)
        noise = np.random.uniform(-amplitude, amplitude, len(sig))
    else:
        noise = np.zeros_like(sig)
        
    return sig + noise


def sync_number_input_from_slider(slider_key, number_key):
    st.session_state[number_key] = st.session_state[slider_key]
    st.session_state[f"{number_key}_invalid"] = False


def sync_slider_from_number_input(slider_key, number_key, min_value, max_value):
    value = st.session_state[number_key]
    is_valid = np.isfinite(value) and min_value <= value <= max_value
    st.session_state[f"{number_key}_invalid"] = not is_valid
    if is_valid:
        st.session_state[slider_key] = value


def sidebar_parameter(
    label,
    min_value,
    max_value,
    default,
    step,
    key,
    disabled=False,
    help_text=None,
    container=None,
):
    """Render a slider with a synchronized, validated numeric input."""
    parent = st.sidebar if container is None else container
    slider_key = f"{key}_slider"
    number_key = f"{key}_number"
    invalid_key = f"{number_key}_invalid"

    st.session_state.setdefault(slider_key, default)
    st.session_state.setdefault(number_key, default)
    st.session_state.setdefault(invalid_key, False)

    range_adjusted = False
    slider_value = st.session_state[slider_key]
    if not min_value <= slider_value <= max_value:
        slider_value = min(max(slider_value, min_value), max_value)
        st.session_state[slider_key] = slider_value
        if not st.session_state[invalid_key]:
            st.session_state[number_key] = slider_value
        range_adjusted = True

    slider_column, number_column = parent.columns([3, 1])
    slider_column.slider(
        label,
        min_value=min_value,
        max_value=max_value,
        step=step,
        key=slider_key,
        disabled=disabled,
        help=help_text,
        on_change=sync_number_input_from_slider,
        args=(slider_key, number_key),
    )
    decimals = max(0, int(np.ceil(-np.log10(step)))) if step < 1 else 0
    number_format = (
        "%d"
        if all(isinstance(value, int) for value in (min_value, max_value, default, step))
        else f"%.{decimals}f"
    )
    number_column.number_input(
        f"{label} value",
        step=step,
        format=number_format,
        key=number_key,
        disabled=disabled,
        help=help_text,
        on_change=sync_slider_from_number_input,
        args=(slider_key, number_key, min_value, max_value),
    )

    if st.session_state[invalid_key]:
        parent.warning(
            f"{label} must be between {min_value:g} and {max_value:g}. "
            "The last valid value is still being used."
        )
    elif range_adjusted:
        parent.warning(
            f"{label} was adjusted to {slider_value:g} because the allowed range changed."
        )

    return st.session_state[slider_key]


def calculate_snr_db(reference, error):
    """Calculates SNR in dB, or returns None when the reference is silent."""
    signal_power = np.mean(reference**2)
    error_power = np.mean(error**2)
    if signal_power <= 0:
        return None
    if error_power <= 0:
        return float('inf')
    return 10 * np.log10(signal_power / error_power)


def format_snr(value):
    if value is None:
        return "N/A"
    if np.isinf(value):
        return "∞ dB"
    return f"{value:.1f} dB"


def dominant_frequency(frequencies, magnitudes):
    """Returns the strongest non-DC frequency, or None if no tone is present."""
    if len(frequencies) < 2:
        return None
    non_dc_magnitudes = magnitudes[1:]
    if not len(non_dc_magnitudes) or np.max(non_dc_magnitudes) <= np.finfo(float).eps:
        return None
    peak_index = int(np.argmax(non_dc_magnitudes)) + 1
    return float(frequencies[peak_index])


def interactive_plot_config(filename):
    """Enable Plotly zoom controls and a high-resolution PNG screenshot action."""
    return {
        "displayModeBar": True,
        "displaylogo": False,
        "scrollZoom": True,
        "doubleClick": "reset",
        "toImageButtonOptions": {
            "format": "png",
            "filename": filename,
            "scale": 2,
        },
    }


@st.cache_data
def signal_recording_csv(time_s, clean_signal, noisy_signal, filtered_signal):
    """Serialize the full generated record (not just the plotted zoom) as CSV."""
    output = io.BytesIO()
    samples = np.column_stack(
        (time_s, clean_signal, noisy_signal, filtered_signal)
    )
    np.savetxt(
        output,
        samples,
        delimiter=",",
        header="time_s,clean_signal,noisy_signal,filtered_signal",
        comments="",
        fmt="%.10g",
    )
    return output.getvalue()


@st.cache_data
def testbench_csv(time_s, clean_signal, noisy_signal, sample_limit):
    """Build a cached CSV containing the requested prefix of the signal record."""
    export_frame = pd.DataFrame({
        "time_s": time_s[:sample_limit],
        "clean_signal": clean_signal[:sample_limit],
        "noisy_signal": noisy_signal[:sample_limit],
    })
    return export_frame.to_csv(index=False).encode("utf-8")


@st.cache_data
def cached_memory_files(normalized_signal):
    """Cache FPGA memory-file formatting until the selected signal changes."""
    return format_memory_files(normalized_signal)


@st.cache_data
def analysis_report_markdown(
    sampling_frequency,
    signal_types,
    filter_order,
    cutoff_description,
    input_snr,
    output_snr,
):
    """Generate the current DSP configuration and result summary as Markdown."""
    return f"""# DSP Analysis Test Report

## System and configuration

- **Sampling frequency:** {sampling_frequency:,} Hz
- **Signal type(s):** {signal_types}
- **Filter order:** {filter_order}
- **Cutoff frequency:** {cutoff_description}

## Analysis results

- **Input SNR:** {format_snr(input_snr)}
- **Output SNR:** {format_snr(output_snr)}
"""


def validate_filter_cutoffs(fs, filter_type, cutoff_freqs):
    """Validates filter cutoff values before design."""
    if filter_type == 'None':
        return None, None

    if fs <= 0:
        return None, "Sampling frequency must be greater than zero."

    nyq = 0.5 * fs
    values = [float(v) for v in cutoff_freqs]

    if filter_type in ['Lowpass', 'Highpass']:
        if len(values) != 1:
            return None, f"{filter_type} requires exactly one cutoff frequency."
        if not 0 < values[0] < nyq:
            return None, f"Cutoff frequency must be between 0 and {nyq:.1f} Hz."
        return values, None

    if filter_type in ['Bandpass', 'Bandstop']:
        if len(values) != 2:
            return None, f"{filter_type} requires two cutoff frequencies."
        low, high = values
        if not 0 < low < high < nyq:
            return None, f"Band edges must satisfy 0 < low < high < {nyq:.1f} Hz."
        return [low, high], None

    return None, f"Unsupported filter type: {filter_type}"


@st.cache_data
def design_and_apply_filter(sig, fs, filter_type, order, cutoff_freqs):
    """Designs a Butterworth IIR filter and applies it to the signal."""
    if filter_type == 'None':
        return sig

    validated_cutoffs, error = validate_filter_cutoffs(fs, filter_type, cutoff_freqs)
    if error is not None:
        st.warning(f"Invalid filter settings: {error}")
        return sig

    nyq = 0.5 * fs

    try:
        if filter_type == 'Lowpass':
            normal_cutoff = validated_cutoffs[0] / nyq
            b, a = signal.butter(order, normal_cutoff, btype='low', analog=False)
        elif filter_type == 'Highpass':
            normal_cutoff = validated_cutoffs[0] / nyq
            b, a = signal.butter(order, normal_cutoff, btype='high', analog=False)
        elif filter_type == 'Bandpass':
            normal_cutoff = [f / nyq for f in validated_cutoffs]
            b, a = signal.butter(order, normal_cutoff, btype='band', analog=False)
        elif filter_type == 'Bandstop':
            normal_cutoff = [f / nyq for f in validated_cutoffs]
            b, a = signal.butter(order, normal_cutoff, btype='bandstop', analog=False)

        # Apply filter using filtfilt for zero-phase distortion
        filtered_sig = signal.filtfilt(b, a, sig)
        return filtered_sig
    except ValueError as e:
        st.error(f"Filter Design Error: {e}. Check your cutoff frequencies.")
        return sig

@st.cache_data
def compute_fft(
    sig, fs, window_type, taylor_nbar=4, taylor_sll=30, kaiser_beta=8.6
):
    """Computes the Fast Fourier Transform of the signal."""
    N = len(sig)
    
    # Apply window function to reduce spectral leakage
    if window_type == 'Hann':
        win = signal.windows.hann(N)
    elif window_type == 'Hamming':
        win = signal.windows.hamming(N)
    elif window_type == 'Blackman':
        win = signal.windows.blackman(N)
    elif window_type == 'Taylor':
        win = signal.windows.taylor(N, nbar=taylor_nbar, sll=taylor_sll, norm=True)
    elif window_type == 'Kaiser':
        win = signal.windows.kaiser(N, beta=kaiser_beta)
    else:
        win = np.ones(N)
        
    windowed_sig = sig * win
    yf = np.fft.rfft(windowed_sig)
    xf_pos = np.fft.rfftfreq(N, 1/fs)
    mag = np.abs(yf) * (2 / np.sum(win))
    mag[0] /= 2
    if N % 2 == 0:
        mag[-1] /= 2
    mag_db = 20 * np.log10(np.clip(mag, 1e-10, None))
    return xf_pos, mag, mag_db

# --- Sidebar Controls ---
st.sidebar.title("Signal controls", icon=":material/tune:")
st.sidebar.caption("Follow the signal path from sampling to spectral analysis.")
st.sidebar.caption("Change light/dark mode from the app menu: Settings → Theme.")

with st.sidebar.expander("1. Signal and generation", expanded=True) as signal_panel:
    with signal_panel.expander("System and sampling", expanded=True) as system_panel:
        sampling_frequency_text = system_panel.text_input(
            "Sampling frequency",
            value="1 kHz",
            key="sampling_frequency_input",
            help=(
                "Enter Hz directly or use k/K for kHz, M for MHz, or G for GHz. "
                "Supported range: 100 Hz to 1 GHz."
            ),
            placeholder="e.g. 1000, 250M, 1G",
        )
        last_valid_fs = int(
            st.session_state.get("sampling_frequency_last_valid_hz", 1000)
        )
        try:
            fs = parse_sampling_frequency(sampling_frequency_text)
            if not 100 <= fs <= 1_000_000_000:
                raise ValueError(
                    "Sampling frequency must be between 100 Hz and 1 GHz."
                )
            st.session_state["sampling_frequency_last_valid_hz"] = fs
        except ValueError as error:
            fs = last_valid_fs
            system_panel.error(
                f"{error} Using the last valid value: {fs:,} Hz."
            )
        system_panel.caption(f"Converted value: {fs:,} Hz")
        duration_requested = sidebar_parameter(
            "Record duration (seconds)", 0.1, 5.0, 1.0, 0.1, "signal_duration",
            help_text="Total signal duration used for waveform generation and frequency analysis.",
            container=system_panel,
        )
        max_signal_samples = 1_000_000
        sample_count = max(2, int(round(fs * duration_requested)))
        if sample_count > max_signal_samples:
            sample_count = max_signal_samples
            system_panel.warning(
                f"Duration limited to {sample_count / fs:.3g} seconds to keep analysis "
                f"within {max_signal_samples:,} samples."
            )
        system_panel.number_input(
            "Number of samples", min_value=2, max_value=max_signal_samples,
            value=sample_count, step=1, disabled=True,
            help="Calculated from sampling frequency × effective duration.",
        )
        system_panel.caption(f"Nyquist frequency: {fs / 2:g} Hz")

    duration = sample_count / fs
    t = np.arange(sample_count) / fs
    combined_signal = np.zeros(sample_count)
    active_components = []
    active_frequencies = []

    with signal_panel.expander("Signal generation", expanded=True) as generation_panel:
        generation_panel.caption("Choose the signal components to combine.")
        num_signals = int(generation_panel.number_input(
            "Number of signal components", min_value=1, max_value=3, value=2,
            help="Choose how many independently configured components to combine.",
        ))

        for i in range(num_signals):
            component_panel = generation_panel.expander(
                f"Component {i + 1}", expanded=(i == 0)
            )
            with component_panel:
                enabled = component_panel.checkbox(
                    "Include in combined signal", value=True, key=f"component_enabled_{i}"
                )
                sig_type = component_panel.selectbox(
                    "Type",
                    ["Sine", "Square", "Sawtooth", "Chirp", "SAR Chirp"],
                    key=f"type_{i}",
                    help="Chirp sweeps linearly from 0 Hz to the selected frequency.",
                )
                frequency_label = (
                    "Sweep end frequency (Hz)"
                    if sig_type in ["Chirp", "SAR Chirp"] else "Frequency (Hz)"
                )
                freq = sidebar_parameter(
                    frequency_label, 1.0, fs / 2 - 1, (i + 1) * 5.0, 1.0,
                    f"freq_{i}", disabled=not enabled,
                    help_text="Tone frequency for periodic signals, or final sweep frequency for a chirp.",
                    container=component_panel,
                )
                amp = sidebar_parameter(
                    "Amplitude", 0.1, 10.0, 1.0, 0.1, f"amp_{i}",
                    disabled=not enabled, help_text="Peak amplitude of this component.",
                    container=component_panel,
                )
                phase = sidebar_parameter(
                    "Phase (rad)", 0.0, 2 * np.pi, 0.0, 0.1,
                    f"phase_{i}", disabled=not enabled,
                    help_text="Initial phase offset in radians.",
                    container=component_panel,
                )

                chirp_window = "Rectangular"
                chirp_taylor_nbar = 4
                chirp_taylor_sll = 30
                chirp_kaiser_beta = 8.6
                if sig_type == "SAR Chirp":
                    chirp_window = component_panel.selectbox(
                        "SAR chirp pulse window",
                        ["Rectangular", "Taylor", "Kaiser"],
                        key=f"sar_chirp_window_{i}",
                        disabled=not enabled,
                        help="Optional time-domain taper applied to this SAR chirp pulse.",
                    )
                    if chirp_window == "Taylor":
                        chirp_taylor_nbar = int(sidebar_parameter(
                            "Taylor nbar", 2, 10, 4, 1,
                            f"sar_taylor_nbar_{i}",
                            disabled=not enabled, container=component_panel,
                        ))
                        chirp_taylor_sll = int(sidebar_parameter(
                            "Taylor sidelobe level (dB)", 20, 100, 30, 1,
                            f"sar_taylor_sll_{i}", disabled=not enabled,
                            container=component_panel,
                        ))
                    elif chirp_window == "Kaiser":
                        chirp_kaiser_beta = sidebar_parameter(
                            "Kaiser beta", 0.0, 20.0, 8.6, 0.1,
                            f"sar_kaiser_beta_{i}", disabled=not enabled,
                            container=component_panel,
                        )

                if enabled:
                    _, signal_component = generate_signal(
                        sig_type, freq, amp, duration, fs, phase, chirp_window,
                        chirp_taylor_nbar, chirp_taylor_sll, chirp_kaiser_beta,
                    )
                    combined_signal += signal_component
                    active_components.append(sig_type)
                    active_frequencies.append(freq)

with st.sidebar.expander("3. Channel and noise", expanded=False) as channel_panel:
    noise_type = channel_panel.selectbox(
        "Noise profile",
        ["None", "Gaussian White", "Uniform"],
        help="Add Gaussian or uniform white noise to the combined signal.",
    )
noise_enabled = noise_type != "None"
with channel_panel:
    snr_db = sidebar_parameter(
        "Target SNR (dB)", -20, 50, 10, 1, "noise_snr",
        disabled=not noise_enabled,
        help_text="Target ratio of signal power to noise power in decibels.",
        container=channel_panel,
    )
noisy_signal = add_noise(combined_signal, noise_type, snr_db)

with st.sidebar.expander("4. Digital filter", expanded=False) as filter_panel:
    filter_type = filter_panel.selectbox(
        "Filter response",
        ["None", "Lowpass", "Highpass", "Bandpass", "Bandstop"],
        help="Butterworth IIR filter applied to the noisy signal.",
    )
filter_enabled = filter_type != "None"
cutoff_max = fs / 2 - 1
with filter_panel:
    if filter_type in ["Bandpass", "Bandstop"]:
        cutoff = [
            sidebar_parameter(
                "Low cutoff (Hz)", 1.0, cutoff_max, 10.0, 1.0,
                "filter_low_cutoff", disabled=not filter_enabled,
                help_text="Lower edge of the passband or stopband.",
                container=filter_panel,
            ),
            sidebar_parameter(
                "High cutoff (Hz)", 1.0, cutoff_max, 50.0, 1.0,
                "filter_high_cutoff", disabled=not filter_enabled,
                help_text="Upper edge of the passband or stopband; keep it above the low cutoff and below Nyquist.",
                container=filter_panel,
            ),
        ]
    else:
        cutoff = [sidebar_parameter(
            "Cutoff frequency (Hz)", 1.0, cutoff_max, 20.0, 1.0,
            "filter_cutoff", disabled=not filter_enabled,
            help_text="Cutoff must remain below the Nyquist frequency.",
            container=filter_panel,
        )]
    order = int(sidebar_parameter(
        "Filter order", 1, 10, 4, 1, "filter_order",
        disabled=not filter_enabled,
        help_text="Higher orders have steeper transitions but can increase ringing.",
        container=filter_panel,
    ))

filtered_signal = design_and_apply_filter(noisy_signal, fs, filter_type, order, cutoff)
input_snr = calculate_snr_db(combined_signal, noisy_signal - combined_signal)
output_snr = calculate_snr_db(combined_signal, filtered_signal - combined_signal)
if not noise_enabled:
    input_snr = float('inf')

with st.sidebar.expander("Recording and screenshots", expanded=False):
    st.caption("To save a chart as PNG, hover over it and select the camera icon.")

with st.sidebar.expander("5. Spectral analysis", expanded=False) as spectral_panel:
    window_type = spectral_panel.selectbox(
        "FFT window",
        ["Rectangular", "Hamming", "Hann", "Blackman", "Taylor", "Kaiser"],
        help="Window applied before the FFT to control spectral leakage.",
    )
    taylor_nbar = 4
    taylor_sll = 30
    kaiser_beta = 8.6
    if window_type == "Taylor":
        taylor_nbar = int(sidebar_parameter(
            "Taylor nbar", 2, 10, 4, 1, "fft_taylor_nbar",
            container=spectral_panel,
        ))
        taylor_sll = int(sidebar_parameter(
            "Taylor sidelobe level (dB)", 20, 100, 30, 1, "fft_taylor_sll",
            container=spectral_panel,
        ))
    elif window_type == "Kaiser":
        kaiser_beta = sidebar_parameter(
            "Kaiser beta", 0.0, 20.0, 8.6, 0.1, "fft_kaiser_beta",
            container=spectral_panel,
        )
    plot_type = spectral_panel.radio(
        "Spectrum scale", ["Linear Magnitude", "Logarithmic (dB)"],
        help="Choose linear FFT magnitude or logarithmic decibel scale.",
    )

with st.sidebar.expander("Visualization Settings", expanded=False):
    show_interpretations = st.checkbox(
        "Show live graph interpretations", value=True, key="show_interpretations"
    )
    clean_color = st.color_picker(
        "Clean Signal Color", value="#00FF00", key="visual_clean_signal_color"
    )
    noisy_color = st.color_picker(
        "Noisy Signal Color", value="#FF0000", key="visual_noisy_signal_color"
    )
    filtered_color = st.color_picker(
        "Filtered Signal Color", value="#00BFFF", key="visual_filtered_signal_color"
    )

st.title("RTL Signal Studio")
sampling_metric, target_snr_metric, calculated_snr_metric = st.columns(3)
sampling_metric.metric("Sampling Rate", f"{fs:,} Hz")
target_snr_metric.metric(
    "Target SNR",
    f"{snr_db:g} dB" if noise_enabled else "Disabled",
)
calculated_snr_metric.metric("Calculated SNR", format_snr(output_snr))

# --- Plotting ---

# Plot 1: Time Domain
fig_time = make_subplots(rows=1, cols=1)

# Show up to five periods of the highest active component so fast waveforms
# remain visually distinguishable instead of being compressed into the full record.
if active_frequencies:
    highest_signal_frequency = max(active_frequencies)
    plot_view_duration = min(duration, 5 / highest_signal_frequency)
else:
    plot_view_duration = duration

plot_view_count = max(2, min(sample_count, int(np.ceil(plot_view_duration * fs))))
max_plot_points = 5000
plot_step = max(1, int(np.ceil(plot_view_count / max_plot_points)))
plot_indices = np.arange(0, plot_view_count, plot_step)

fig_time.add_trace(go.Scatter(x=t[plot_indices], y=combined_signal[plot_indices],
                              mode='lines', name='Original Clean Signal',
                              line=dict(color=clean_color, width=1, dash='dash')))

if noise_type != 'None':
    fig_time.add_trace(go.Scatter(x=t[plot_indices], y=noisy_signal[plot_indices],
                                  mode='lines', name='Noisy Signal',
                                  line=dict(color=noisy_color, width=1)))

fig_time.add_trace(go.Scatter(x=t[plot_indices], y=filtered_signal[plot_indices],
                              mode='lines', name='Final (Filtered) Signal',
                              line=dict(color=filtered_color, width=2)))

fig_time.update_layout(
    title="Time Domain Representation",
    xaxis_title="Time (seconds)",
    yaxis_title="Amplitude",
    xaxis=dict(range=[0, t[plot_indices[-1]]]),
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=40, b=40),
    height=400,
    hovermode="x unified"
)
st.plotly_chart(
    fig_time,
    width="stretch",
    config=interactive_plot_config("time-domain-signal"),
    key="time_domain_plot",
    alt="Clean, noisy, and filtered signal waveforms over time",
)

if show_interpretations:
    with st.expander("Interpret the time-domain plot", expanded=True):
        peak_to_peak = float(np.ptp(combined_signal))
        rms_amplitude = float(np.sqrt(np.mean(combined_signal**2)))
        st.write(
            f"The plot shows {len(active_components)} active signal component(s) "
            f"({', '.join(active_components) if active_components else 'none'}), "
            f"sampled at {fs:g} Hz for {duration:g} seconds "
            f"({len(t):,} samples)."
        )
        st.write(
            f"The time plot is zoomed to the first {plot_view_duration:.4g} seconds "
            f"({len(plot_indices):,} plotted points) to make waveform shape visible."
        )
        st.write(
            f"The clean signal has a peak-to-peak amplitude of {peak_to_peak:.3g} "
            f"and an RMS amplitude of {rms_amplitude:.3g}."
        )
        if noise_enabled:
            st.write(
                f"{noise_type} noise is enabled with a target SNR of {snr_db:g} dB; "
                "compare the noisy trace with the clean trace to see its time-domain variation."
            )
        else:
            st.write("Noise is disabled, so the noisy input matches the clean signal.")
        if filter_enabled:
            st.write(
                f"A {filter_type.lower()} Butterworth filter (order {order}) is applied "
                "to the input before the final trace is plotted."
            )
        else:
            st.write("Filtering is disabled, so the final trace is the input signal.")

# Plot 2: Frequency Domain (FFT)

xf, mag_clean, db_clean = compute_fft(
    combined_signal, fs, window_type, taylor_nbar, taylor_sll, kaiser_beta
)
_, mag_filt, db_filt = compute_fft(
    filtered_signal, fs, window_type, taylor_nbar, taylor_sll, kaiser_beta
)

fig_freq = go.Figure()

if plot_type == 'Linear Magnitude':
    y_clean, y_filt, y_title = mag_clean, mag_filt, "Magnitude"
else:
    y_clean, y_filt, y_title = db_clean, db_filt, "Magnitude (dB)"

fig_freq.add_trace(go.Scatter(x=xf, y=y_clean, mode='lines', 
                              name='Original Clean Spectrum',
                              line=dict(color=clean_color, width=1)))
                              
fig_freq.add_trace(go.Scatter(x=xf, y=y_filt, mode='lines', 
                              name='Final (Filtered) Spectrum',
                              line=dict(color=filtered_color, width=2)))

# Add shading to indicate filter bands
if filter_type != 'None':
    shapes = []
    nyq = fs / 2
    if filter_type == 'Lowpass':
        shapes.append(dict(type="rect", x0=0, x1=cutoff[0], y0=0, y1=1, yref="paper",
                           fillcolor="rgba(0, 188, 212, 0.1)", layer="below", line_width=0))
    elif filter_type == 'Highpass':
        shapes.append(dict(type="rect", x0=cutoff[0], x1=nyq, y0=0, y1=1, yref="paper",
                           fillcolor="rgba(0, 188, 212, 0.1)", layer="below", line_width=0))
    elif filter_type == 'Bandpass':
        shapes.append(dict(type="rect", x0=cutoff[0], x1=cutoff[1], y0=0, y1=1, yref="paper",
                           fillcolor="rgba(0, 188, 212, 0.1)", layer="below", line_width=0))
    fig_freq.update_layout(shapes=shapes)

fig_freq.update_layout(
    title="Frequency Domain (Spectrum)",
    xaxis_title="Frequency (Hz)",
    yaxis_title=y_title,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=40, b=40),
    height=400,
    hovermode="x unified"
)
st.plotly_chart(
    fig_freq,
    width="stretch",
    config=interactive_plot_config("frequency-spectrum"),
    key="frequency_spectrum_plot",
    alt="Clean and filtered signal magnitude across frequency",
)

if show_interpretations:
    clean_peak = dominant_frequency(xf, mag_clean)
    filtered_peak = dominant_frequency(xf, mag_filt)
    frequency_resolution = fs / len(combined_signal)
    with st.expander("Interpret the frequency-domain plot", expanded=True):
        if clean_peak is None:
            st.write("The clean spectrum has no measurable non-DC frequency peak.")
        else:
            st.write(
                f"The strongest non-DC peak in the clean spectrum is at about "
                f"{clean_peak:.2f} Hz; the FFT bin spacing is {frequency_resolution:.2f} Hz."
            )
        if filtered_peak is None:
            st.write("The processed spectrum has no measurable non-DC frequency peak.")
        else:
            st.write(
                f"The strongest non-DC peak after noise/filter processing is at about "
                f"{filtered_peak:.2f} Hz."
            )
        st.write(
            f"The displayed spectrum uses the {window_type} analysis window and "
            f"{plot_type.lower()} scaling. Peaks are FFT-bin estimates, so their "
            "accuracy is limited by the bin spacing."
        )
        if filter_enabled:
            st.write(
                f"The shaded region marks the {filter_type.lower()} filter's pass or "
                "stop band; compare the clean and processed traces to see which spectral "
                "components were attenuated."
            )
        else:
            st.write("Filtering is disabled; any difference between traces is due to noise.")

# Plot 3: SNR comparison
snr_labels = ["Input SNR", "Output SNR"]
snr_values = [input_snr, output_snr]
finite_snr = [value for value in snr_values if value is not None and np.isfinite(value)]
if finite_snr:
    y_min = min(0, min(finite_snr))
    y_max = max(0, max(finite_snr))
    y_padding = max(1, (y_max - y_min) * 0.1)
else:
    y_min, y_max, y_padding = -1, 1, 1

fig_snr = go.Figure()
fig_snr.add_trace(go.Bar(
    x=snr_labels,
    y=[value if value is not None and np.isfinite(value) else None for value in snr_values],
    text=[format_snr(value) if value is not None and np.isfinite(value) else None
          for value in snr_values],
    textposition="outside",
    name="SNR",
    marker_color=[noisy_color, filtered_color],
))
for label, value in zip(snr_labels, snr_values):
    if value is None or not np.isfinite(value):
        fig_snr.add_annotation(
            x=label,
            y=y_max + y_padding * 0.5,
            text=format_snr(value),
            showarrow=False,
        )

fig_snr.update_layout(
    title="Input vs. Output SNR",
    xaxis_title="Signal stage",
    yaxis_title="SNR (dB)",
    yaxis=dict(range=[y_min - y_padding, y_max + y_padding]),
    margin=dict(l=40, r=40, t=60, b=40),
    height=400,
    showlegend=False,
)
st.plotly_chart(
    fig_snr,
    width="stretch",
    config=interactive_plot_config("snr-comparison"),
    key="snr_comparison_plot",
    alt="Input and output signal-to-noise ratio comparison",
)

if show_interpretations:
    with st.expander("Interpret the SNR plot", expanded=True):
        if input_snr is None or output_snr is None:
            st.write(
                "SNR is undefined because the clean reference signal has zero power. "
                "Enable at least one non-zero signal component to compare SNR."
            )
        else:
            st.write(
                f"Input SNR is {format_snr(input_snr)} and output SNR is "
                f"{format_snr(output_snr)}. Output SNR is measured against the original "
                "clean signal, so it includes both residual noise and any filter-induced "
                "signal changes."
            )
            if np.isfinite(input_snr) and np.isfinite(output_snr):
                improvement = output_snr - input_snr
                if improvement > 0.1:
                    st.write(f"The processing improves SNR by {improvement:.2f} dB.")
                elif improvement < -0.1:
                    st.write(f"The processing reduces SNR by {abs(improvement):.2f} dB.")
                else:
                    st.write("The processing changes SNR by less than 0.1 dB.")
            elif np.isinf(input_snr) and np.isinf(output_snr):
                st.write(
                    "Both values are infinite because there is no noise or processing "
                    "error relative to the clean signal."
                )
            elif np.isinf(output_snr):
                st.write("Output matches the clean signal exactly, giving infinite SNR.")
            elif np.isinf(input_snr):
                st.write(
                    "Input matches the clean signal exactly; any output error is introduced "
                    "during filtering."
                )

with st.container(border=True):
    st.header("Data & Report Export", icon=":material/file_download:")
    st.caption(
        "Choose an export length, then download signal data, an analysis report, "
        "or FPGA memory initialization files."
    )
    export_sample_count = st.number_input(
        "Number of Samples to Export",
        min_value=1,
        max_value=16384,
        value=1024,
        step=1,
        help="Export the first N time, clean-signal, and noisy-signal samples.",
        key="testbench_export_sample_count",
    )

    if export_sample_count > sample_count:
        st.caption(
            f"The current record contains {sample_count:,} samples; the CSV will include "
            "the available samples only."
        )

    csv_export = testbench_csv(
        t, combined_signal, noisy_signal, int(export_sample_count)
    )
    recording_csv = signal_recording_csv(
        t, combined_signal, noisy_signal, filtered_signal
    )
    memory_signal_name = st.selectbox(
        "Signal for FPGA memory export",
        ["Clean signal", "Noisy signal", "Filtered signal"],
        help="Select the waveform to quantize into 16-bit signed BRAM words.",
    )
    memory_signal = {
        "Clean signal": combined_signal,
        "Noisy signal": noisy_signal,
        "Filtered signal": filtered_signal,
    }[memory_signal_name][:int(export_sample_count)]
    memory_peak = float(np.max(np.abs(memory_signal))) if memory_signal.size else 0.0
    normalized_memory_signal = (
        memory_signal / memory_peak if memory_peak > 0 else memory_signal
    )
    memory_files = cached_memory_files(normalized_memory_signal)
    st.caption(
        f"{memory_signal_name} is peak-normalized to [-1, 1] before 16-bit quantization. "
        "Xilinx uses .coe; Intel/Altera commonly use .mif. Microchip/Microsemi "
        "extensions depend on the Libero IP flow; check the target core's supported format."
    )
    cutoff_description = (
        "Not applied"
        if filter_type == "None"
        else (
            f"{cutoff[0]:g}–{cutoff[1]:g} Hz"
            if len(cutoff) == 2
            else f"{cutoff[0]:g} Hz"
        )
    )
    report_export = analysis_report_markdown(
        fs,
        ", ".join(active_components) if active_components else "None",
        order,
        cutoff_description,
        input_snr,
        output_snr,
    )

    st.subheader("Signal data and report")
    csv_column, recording_column, report_column = st.columns(3)
    with csv_column:
        st.caption("`.csv` · selected sample range")
        st.download_button(
            "Download testbench CSV",
            data=csv_export,
            file_name="generated_signals.csv",
            mime="text/csv",
            on_click="ignore",
            icon=":material/download:",
            help="Download the selected time, clean signal, and noisy signal samples.",
        )
    with recording_column:
        st.caption("`.csv` · full recording")
        st.download_button(
            "Download full recording",
            data=recording_csv,
            file_name="signal_recording.csv",
            mime="text/csv",
            on_click="ignore",
            icon=":material/download:",
            help="Download every generated sample, including clean, noisy, and filtered signals.",
        )
    with report_column:
        st.caption("`.md` · analysis summary")
        st.download_button(
            "Download analysis report",
            data=report_export,
            file_name="dsp_analysis_report.md",
            mime="text/markdown",
            on_click="ignore",
            icon=":material/description:",
            help="Download the current system configuration and SNR results as Markdown.",
        )

    st.subheader("FPGA memory files")
    coe_column, mif_column, mem_column = st.columns(3)
    with coe_column:
        st.caption("`.coe` · Xilinx")
        st.download_button(
            "Download COE",
            data=memory_files["coe"],
            file_name="generated_signals.coe",
            mime="text/plain",
            on_click="ignore",
            icon=":material/download:",
            help="16-bit signed two's-complement words in Xilinx COE format.",
        )
    with mif_column:
        st.caption("`.mif` · Intel/Altera")
        st.download_button(
            "Download MIF",
            data=memory_files["mif"],
            file_name="generated_signals.mif",
            mime="text/plain",
            on_click="ignore",
            icon=":material/download:",
            help="16-bit signed two's-complement words with hexadecimal addresses and data.",
        )
    with mem_column:
        st.caption("`.mem` · Verilog `$readmemh`")
        st.download_button(
            "Download MEM",
            data=memory_files["mem"],
            file_name="generated_signals.mem",
            mime="text/plain",
            on_click="ignore",
            icon=":material/download:",
            help="Raw 16-bit words for Verilog $readmemh.",
        )