/**
 * Project Synesthesia — weeks 2–3: Web Audio capture, p5 waveform, Flask /api/analyze.
 */

const RECORD_MS = 4000;

let audioContext = null;
let latestBuffer = null;
let waveformPeaks = null;

const $ = (id) => document.getElementById(id);

function getAudioContext() {
  if (!audioContext) {
    audioContext = new (window.AudioContext || window.webkitAudioContext)();
  }
  return audioContext;
}

function audioBufferToMono(audioBuffer) {
  const n = audioBuffer.numberOfChannels;
  const len = audioBuffer.length;
  const out = new Float32Array(len);
  for (let c = 0; c < n; c += 1) {
    const ch = audioBuffer.getChannelData(c);
    for (let i = 0; i < len; i += 1) out[i] += ch[i];
  }
  for (let i = 0; i < len; i += 1) out[i] /= n;
  return out;
}

function downsamplePeaks(data, targetPoints) {
  const n = data.length;
  if (n === 0) return [];
  const block = Math.max(1, Math.floor(n / targetPoints));
  const peaks = [];
  for (let i = 0; i < targetPoints; i += 1) {
    const start = i * block;
    let max = 0;
    const end = Math.min(start + block, n);
    for (let j = start; j < end; j += 1) {
      const v = Math.abs(data[j]);
      if (v > max) max = v;
    }
    peaks.push(max);
  }
  return peaks;
}

function encodeWavMono(float32, sampleRate) {
  const numSamples = float32.length;
  const buffer = new ArrayBuffer(44 + numSamples * 2);
  const view = new DataView(buffer);

  const writeStr = (off, s) => {
    for (let i = 0; i < s.length; i += 1) {
      view.setUint8(off + i, s.charCodeAt(i));
    }
  };

  writeStr(0, "RIFF");
  view.setUint32(4, 36 + numSamples * 2, true);
  writeStr(8, "WAVE");
  writeStr(12, "fmt ");
  view.setUint32(16, 16, true);
  view.setUint16(20, 1, true);
  view.setUint16(22, 1, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, sampleRate * 2, true);
  view.setUint16(32, 2, true);
  view.setUint16(34, 16, true);
  writeStr(36, "data");
  view.setUint32(40, numSamples * 2, true);

  let offset = 44;
  for (let i = 0; i < numSamples; i += 1, offset += 2) {
    let s = Math.max(-1, Math.min(1, float32[i]));
    view.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

function setStatus(msg, kind) {
  const el = $("status");
  el.textContent = msg;
  el.classList.remove("ok", "err");
  if (kind) el.classList.add(kind);
}

function onBufferReady(audioBuffer) {
  latestBuffer = audioBuffer;
  const mono = audioBufferToMono(audioBuffer);
  waveformPeaks = downsamplePeaks(mono, 1800);
  if (window.__synRedrawWave) window.__synRedrawWave();

  $("analyzeBtn").disabled = false;
  setStatus(
    `Loaded ~${audioBuffer.duration.toFixed(2)}s at ${audioBuffer.sampleRate} Hz — run analysis.`,
    "ok"
  );
}

async function postAnalyzeWav(wavArrayBuffer) {
  const blob = new Blob([wavArrayBuffer], { type: "audio/wav" });
  const fd = new FormData();
  fd.append("audio", blob, "syn_clip.wav");

  const res = await fetch("/api/analyze", { method: "POST", body: fd });
  const data = await res.json();
  if (!res.ok || !data.success) {
    throw new Error(data.message || `HTTP ${res.status}`);
  }
  return data;
}

function renderAnalysis(data) {
  const feat = data.features || {};
  const labels = data.labels || {};

  $("featureList").innerHTML = `
    <li><span>Duration</span>${feat.duration_sec ?? "—"} s</li>
    <li><span>Tempo (est.)</span>${feat.tempo_bpm ?? "—"} bpm</li>
    <li><span>RMS (mean)</span>${feat.rms_mean ?? "—"}</li>
    <li><span>Spectral centroid</span>${feat.spectral_centroid_hz ?? "—"} Hz</li>
    <li><span>ZCR (mean)</span>${feat.zero_crossing_rate_mean ?? "—"}</li>
    <li><span>Onset mean / std</span>${feat.onset_strength_mean ?? "—"} / ${feat.onset_strength_std ?? "—"}</li>
  `;

  const chips = Object.entries(labels)
    .map(([k, v]) => `<span class="chip">${k}: ${v}</span>`)
    .join("");
  $("labelChips").innerHTML = chips || '<span class="chip">No labels</span>';

  $("promptPreview").textContent = data.prompt_preview || "";
}

// --- p5 waveform (global mode) ---
function setup() {
  const host = $("waveform-host");
  const w = Math.max(320, host.clientWidth || 600);
  const h = 140;
  const cnv = createCanvas(w, h);
  cnv.parent("waveform-host");
  noLoop();
  window.__synRedrawWave = () => redraw();
}

function draw() {
  background(18, 16, 28);
  if (!waveformPeaks || waveformPeaks.length === 0) {
    noStroke();
    fill(80, 74, 110);
    textAlign(CENTER, CENTER);
    textSize(14);
    text("Record or upload audio to see a waveform", width / 2, height / 2);
    return;
  }

  noFill();
  stroke(124, 92, 255);
  strokeWeight(1.2);
  const mid = height / 2;
  const step = width / waveformPeaks.length;
  beginShape();
  for (let i = 0; i < waveformPeaks.length; i += 1) {
    const x = i * step;
    const h = waveformPeaks[i] * (height * 0.42);
    vertex(x, mid - h);
  }
  for (let i = waveformPeaks.length - 1; i >= 0; i -= 1) {
    const x = i * step;
    const h = waveformPeaks[i] * (height * 0.42);
    vertex(x, mid + h);
  }
  endShape(CLOSE);

  stroke(255, 107, 157, 90);
  strokeWeight(1);
  line(0, mid, width, mid);
}

function windowResized() {
  const host = $("waveform-host");
  if (!host) return;
  resizeCanvas(Math.max(320, host.clientWidth), 140);
  redraw();
}

// --- UI wiring ---
async function testBackend() {
  try {
    const res = await fetch("/api/health");
    const data = await res.json();
    console.log("Backend:", data);
  } catch (e) {
    console.warn("Backend health check failed", e);
  }
}

async function startRecording() {
  setStatus("Requesting microphone…");
  $("recordBtn").disabled = true;
  try {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mime = MediaRecorder.isTypeSupported("audio/webm;codecs=opus")
      ? "audio/webm;codecs=opus"
      : undefined;
    const recorder = new MediaRecorder(stream, mime ? { mimeType: mime } : undefined);
    const chunks = [];

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunks.push(e.data);
    };

    recorder.onstop = async () => {
      stream.getTracks().forEach((t) => t.stop());
      try {
        setStatus("Decoding recording…");
        const blob = new Blob(chunks, { type: chunks[0]?.type || "audio/webm" });
        const ctx = getAudioContext();
        const buf = await blob.arrayBuffer();
        const audioBuffer = await ctx.decodeAudioData(buf.slice(0));
        onBufferReady(audioBuffer);
      } catch (err) {
        console.error(err);
        setStatus(`Could not decode recording: ${err.message}`, "err");
      } finally {
        $("recordBtn").disabled = false;
      }
    };

    recorder.start();
    setStatus(`Recording… (${RECORD_MS / 1000}s)`);
    setTimeout(() => {
      if (recorder.state === "recording") recorder.stop();
    }, RECORD_MS);
  } catch (err) {
    console.error(err);
    setStatus("Microphone access denied or unavailable.", "err");
    $("recordBtn").disabled = false;
  }
}

async function onFilePick(event) {
  const file = event.target.files?.[0];
  if (!file) return;
  setStatus(`Reading ${file.name}…`);
  try {
    const ctx = getAudioContext();
    const buf = await file.arrayBuffer();
    const audioBuffer = await ctx.decodeAudioData(buf.slice(0));
    onBufferReady(audioBuffer);
  } catch (err) {
    console.error(err);
    setStatus(`Could not decode file: ${err.message}`, "err");
  }
  event.target.value = "";
}

async function runAnalyze() {
  if (!latestBuffer) {
    setStatus("No audio loaded.", "err");
    return;
  }
  $("analyzeBtn").disabled = true;
  setStatus("Analyzing on server…");
  try {
    const mono = audioBufferToMono(latestBuffer);
    const wav = encodeWavMono(mono, latestBuffer.sampleRate);
    const data = await postAnalyzeWav(wav);
    renderAnalysis(data);
    setStatus("Analysis complete.", "ok");
  } catch (err) {
    console.error(err);
    setStatus(err.message || "Analysis failed", "err");
  } finally {
    $("analyzeBtn").disabled = false;
  }
}

window.addEventListener("load", () => {
  $("recordBtn").textContent = `Record ${RECORD_MS / 1000}s`;
  testBackend();
  $("recordBtn").addEventListener("click", startRecording);
  $("fileInput").addEventListener("change", onFilePick);
  $("analyzeBtn").addEventListener("click", runAnalyze);
});
