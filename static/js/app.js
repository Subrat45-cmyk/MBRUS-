/**
 * MBRUS AI Dragon System - Frontend Controller
 * Google Gemini Integration, Pinpoint GPS Geolocation, Multilingual Speech (Hindi, Bengali, Bhojpuri, Haryanvi, Marwadi, English),
 * Priority Sites Launcher, Dual Waveform Visualizer & Live Telemetry.
 */

document.addEventListener('DOMContentLoaded', () => {
    const arcReactor = document.getElementById('arcReactor');
    const coreStatusText = document.getElementById('coreStatusText');
    const micBtn = document.getElementById('micBtn');
    const handsFreeBtn = document.getElementById('handsFreeBtn');
    const muteBtn = document.getElementById('muteBtn');
    const settingsBtn = document.getElementById('settingsBtn');
    const locateMeBtn = document.getElementById('locateMeBtn');
    const gpsBadge = document.getElementById('gpsBadge');
    const gpsDot = document.getElementById('gpsDot');
    const gpsStatusText = document.getElementById('gpsStatusText');
    const langSelect = document.getElementById('langSelect');
    const chatInput = document.getElementById('chatInput');
    const sendBtn = document.getElementById('sendBtn');
    const chatStream = document.getElementById('chatStream');
    const sportsFeed = document.getElementById('sportsFeed');
    const sportsCountBadge = document.getElementById('sportsCountBadge');

    // Weather Box Elements
    const weatherCityName = document.getElementById('weatherCityName');
    const weatherCondText = document.getElementById('weatherCondText');
    const weatherTempVal = document.getElementById('weatherTempVal');
    const weatherFeels = document.getElementById('weatherFeels');
    const weatherHum = document.getElementById('weatherHum');
    const weatherWind = document.getElementById('weatherWind');
    const weatherCoords = document.getElementById('weatherCoords');
    const clockDisplay = document.getElementById('clockDisplay');

    // Gemini Modal Elements
    const geminiBadge = document.getElementById('geminiBadge');
    const geminiDot = document.getElementById('geminiDot');
    const geminiStatusText = document.getElementById('geminiStatusText');
    const geminiModal = document.getElementById('geminiModal');
    const closeGeminiModalBtn = document.getElementById('closeGeminiModalBtn');
    const saveGeminiBtn = document.getElementById('saveGeminiBtn');
    const geminiApiKeyInput = document.getElementById('geminiApiKeyInput');
    const geminiModelSelect = document.getElementById('geminiModelSelect');
    const geminiConnectionStatus = document.getElementById('geminiConnectionStatus');
    const newChatBtn = document.getElementById('newChatBtn');

    // Priority Sites Elements
    const priorityChipsContainer = document.getElementById('priorityChipsContainer');
    const addSiteBtn = document.getElementById('addSiteBtn');
    const addSiteModal = document.getElementById('addSiteModal');
    const closeAddSiteBtn = document.getElementById('closeAddSiteBtn');
    const saveNewSiteBtn = document.getElementById('saveNewSiteBtn');
    const newSiteKey = document.getElementById('newSiteKey');
    const newSiteName = document.getElementById('newSiteName');
    const newSiteUrl = document.getElementById('newSiteUrl');
    const newSiteIcon = document.getElementById('newSiteIcon');

    // System Metrics Elements
    const cpuVal = document.getElementById('cpuVal');
    const cpuFill = document.getElementById('cpuFill');
    const ramVal = document.getElementById('ramVal');
    const ramFill = document.getElementById('ramFill');
    const batteryVal = document.getElementById('batteryVal');
    const batteryFill = document.getElementById('batteryFill');
    const diskVal = document.getElementById('diskVal');

    // Settings Modal
    const settingsModal = document.getElementById('settingsModal');
    const closeSettingsBtn = document.getElementById('closeSettingsBtn');
    const saveSettingsBtn = document.getElementById('saveSettingsBtn');
    const cityInput = document.getElementById('cityInput');
    const voiceSelect = document.getElementById('voiceSelect');

    let isListening = false;
    let isHandsFree = false;
    let isMuted = false;
    let isSpeaking = false;
    let currentLanguage = "auto";
    let selectedVoice = "en-US-ChristopherNeural";
    let currentAudio = null;
    let recognition = null;
    let visualizerAnimId = null;
    let userCoords = null;

    // Dual Waveform Visualizer
    const canvas = document.getElementById('waveCanvas');
    const ctx = canvas.getContext('2d');
    let wavePhase = 0;

    function renderWaveform() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        const amplitude = isListening ? 14 : (isSpeaking ? 16 : 3);
        const frequency = isListening ? 0.05 : (isSpeaking ? 0.04 : 0.02);

        // Wave 1: Crimson Red
        ctx.lineWidth = 2.5;
        ctx.strokeStyle = isListening ? '#00f0ff' : '#ff0033';
        ctx.shadowBlur = isSpeaking ? 12 : 6;
        ctx.shadowColor = '#ff0033';

        ctx.beginPath();
        for (let x = 0; x < canvas.width; x++) {
            const y = (canvas.height / 2) + Math.sin(x * frequency + wavePhase) * amplitude * Math.sin(x / canvas.width * Math.PI);
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();

        // Wave 2: Electric Cyan
        ctx.lineWidth = 1.5;
        ctx.strokeStyle = isListening ? '#ffaa00' : '#00f0ff';
        ctx.shadowColor = '#00f0ff';

        ctx.beginPath();
        for (let x = 0; x < canvas.width; x++) {
            const y = (canvas.height / 2) - Math.sin(x * frequency + wavePhase * 1.3) * (amplitude * 0.75) * Math.sin(x / canvas.width * Math.PI);
            if (x === 0) ctx.moveTo(x, y);
            else ctx.lineTo(x, y);
        }
        ctx.stroke();
        ctx.shadowBlur = 0;

        wavePhase += isListening ? 0.12 : (isSpeaking ? 0.15 : 0.03);
        visualizerAnimId = requestAnimationFrame(renderWaveform);
    }
    renderWaveform();

    function setAssistantState(state) {
        arcReactor.classList.remove('listening', 'thinking', 'speaking');
        switch (state) {
            case 'listening':
                arcReactor.classList.add('listening');
                coreStatusText.textContent = 'LISTENING FOR SPEECH...';
                coreStatusText.style.color = 'var(--neon-cyan)';
                micBtn.classList.add('recording');
                break;
            case 'thinking':
                arcReactor.classList.add('thinking');
                coreStatusText.textContent = 'EXECUTING COMMAND...';
                coreStatusText.style.color = 'var(--neon-red-bright)';
                micBtn.classList.remove('recording');
                break;
            case 'speaking':
                arcReactor.classList.add('speaking');
                coreStatusText.textContent = 'TRANSMITTING VOICE AUDIO...';
                coreStatusText.style.color = '#fff';
                micBtn.classList.remove('recording');
                break;
            case 'idle':
            default:
                coreStatusText.textContent = isHandsFree ? 'HANDS-FREE ACTIVE • SPEAK NOW' : 'ONLINE // READY FOR COMMANDS';
                coreStatusText.style.color = 'var(--neon-red-bright)';
                micBtn.classList.remove('recording');
                break;
        }
    }

    // GPS Geolocation Engine
    function requestGPSLocation(speakAnnouncement = false) {
        if (!('geolocation' in navigator)) {
            gpsStatusText.textContent = '📍 GPS: UNSUPPORTED';
            gpsDot.style.background = '#ff3366';
            loadLiveWeather();
            return;
        }

        gpsStatusText.textContent = '📍 GPS: ACQUIRING...';
        gpsDot.style.background = '#ffaa00';

        navigator.geolocation.getCurrentPosition(
            async (position) => {
                const lat = position.coords.latitude;
                const lon = position.coords.longitude;
                userCoords = { lat, lon };

                gpsStatusText.textContent = `📍 GPS: LOCKED (${lat.toFixed(2)}°, ${lon.toFixed(2)}°)`;
                gpsDot.style.background = '#00ff88';

                try {
                    const resp = await fetch('/api/location/gps', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ latitude: lat, longitude: lon, language: currentLanguage })
                    });
                    const data = await resp.json();
                    if (data.success) {
                        updateWeatherWidget(data.location.full_name, data.weather);
                        if (speakAnnouncement) {
                            appendMessage('assistant', `📍 **GPS Coordinates Locked:** ${data.location.full_name}\n- **Temperature:** ${data.weather.temperature} (Feels like ${data.weather.feels_like})\n- **Condition:** ${data.weather.condition}\n- **Wind:** ${data.weather.wind_speed}`);
                            playVoiceResponse(data.voice_text, currentLanguage, data.recommended_voice);
                        }
                    }
                } catch (e) {
                    console.warn("GPS registration backend error:", e);
                }
            },
            (error) => {
                console.warn("GPS error:", error.message);
                gpsStatusText.textContent = '📍 GPS: DENIED / MANUAL';
                gpsDot.style.background = '#ff3366';
                loadLiveWeather();
            },
            { enableHighAccuracy: true, timeout: 10000, maximumAge: 60000 }
        );
    }

    gpsBadge.addEventListener('click', () => requestGPSLocation(true));
    locateMeBtn.addEventListener('click', () => requestGPSLocation(true));

    function updateWeatherWidget(locationTitle, w) {
        weatherCityName.textContent = `📍 ${locationTitle}`;
        weatherCondText.textContent = w.condition;
        weatherTempVal.textContent = w.temperature;
        weatherFeels.textContent = `🌡️ Feels like: ${w.feels_like || w.temperature}`;
        weatherHum.textContent = `💧 Humidity: ${w.humidity}`;
        weatherWind.textContent = `💨 Wind: ${w.wind_speed}`;
        weatherCoords.textContent = `🛰️ Coords: ${w.latitude.toFixed(2)}°, ${w.longitude.toFixed(2)}°`;
    }

    // Gemini Engine Controller & New Chat
    async function loadGeminiStatus() {
        try {
            const res = await fetch('/api/gemini/status');
            const data = await res.json();
            if (data.configured) {
                geminiStatusText.textContent = `✨ ${data.active_model.toUpperCase().replace('-FLASH-LITE', ' FLASH LITE').replace('-FLASH', ' FLASH').replace('-PRO', ' PRO')}`;
                geminiDot.style.background = '#00ff88';
                geminiDot.style.boxShadow = '0 0 10px #00ff88';
                if (data.available_models && data.available_models.length > 0) {
                    geminiModelSelect.innerHTML = data.available_models.map(m => 
                        `<option value="${m.id}">${m.name}</option>`
                    ).join('');
                }
                geminiModelSelect.value = data.active_model;
                geminiConnectionStatus.innerHTML = `<span style="color:#00ff88;">● Connected: Key active (${data.masked_key})</span>`;
            } else {
                geminiStatusText.textContent = '✨ CONNECT GEMINI';
                geminiDot.style.background = '#ffaa00';
                geminiDot.style.boxShadow = '0 0 10px #ffaa00';
                geminiConnectionStatus.innerHTML = `<span style="color:#ffaa00;">● Free Autonomous Engine Active. Paste Gemini Key for Deep Reasoning.</span>`;
            }
        } catch (e) {
            console.warn("Gemini status error:", e);
        }
    }

    geminiBadge.addEventListener('click', () => {
        geminiModal.style.display = 'flex';
        loadGeminiStatus();
    });

    closeGeminiModalBtn.addEventListener('click', () => {
        geminiModal.style.display = 'none';
    });

    saveGeminiBtn.addEventListener('click', async () => {
        const key = geminiApiKeyInput.value.trim();
        const model = geminiModelSelect.value;
        if (!key) {
            alert('Please paste a valid Gemini API Key from Google AI Studio.');
            return;
        }

        saveGeminiBtn.textContent = 'Verifying...';
        try {
            const res = await fetch('/api/gemini/key', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ api_key: key, model: model })
            });
            const data = await res.json();
            saveGeminiBtn.textContent = 'Connect Gemini';

            if (data.success) {
                geminiModal.style.display = 'none';
                geminiApiKeyInput.value = '';
                appendMessage('assistant', `✨ **Google Gemini Intelligence Connected!** Model set to **${model}**. Ready for multi-turn conversational reasoning, coding, and tools.`);
                playVoiceResponse(`Google Gemini intelligence connected successfully, Sir. Systems operating on ${model}.`, currentLanguage);
                loadGeminiStatus();
            } else {
                alert('Could not verify Gemini key. Please check the key and try again.');
            }
        } catch (e) {
            saveGeminiBtn.textContent = 'Connect Gemini';
            alert('Error connecting Gemini: ' + e.message);
        }
    });

    newChatBtn.addEventListener('click', async () => {
        window.soundFX.playStartup();
        await fetch('/api/gemini/clear-chat', { method: 'POST' });
        chatStream.innerHTML = `
            <div class="chat-bubble assistant">
                <div class="avatar-icon assistant">
                    <img src="/static/images/mbrus_logo.png" alt="MBRUS">
                </div>
                <div class="bubble-content">
                    <strong style="color:var(--neon-red-bright)">✨ New Chat Session Initialized.</strong><br/>
                    Conversation context has been cleared. What would you like to explore or execute next, Boss?
                    <div class="bubble-meta">
                        <span>CONTEXT CLEARED • TALK • THINK • ACT</span>
                    </div>
                </div>
            </div>
        `;
    });

    // Multilingual Speech Recognition
    function getSpeechRecLang(lang) {
        if (lang === 'bn') return 'bn-IN';
        if (['hi', 'bho', 'bgc', 'mwr'].includes(lang)) return 'hi-IN';
        return 'en-US';
    }

    function initSpeechRecognition() {
        const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
        if (!SpeechRec) {
            console.warn("Web Speech API not supported.");
            return;
        }

        recognition = new SpeechRec();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = getSpeechRecLang(currentLanguage);

        recognition.onstart = () => {
            isListening = true;
            setAssistantState('listening');
            window.soundFX.playListeningPing();
        };

        recognition.onresult = (event) => {
            let interim = '';
            let final = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) final += event.results[i][0].transcript;
                else interim += event.results[i][0].transcript;
            }
            if (interim) chatInput.value = interim;
            if (final) {
                chatInput.value = final;
                processUserQuery(final.trim());
            }
        };

        recognition.onerror = () => {
            isListening = false;
            setAssistantState('idle');
            if (isHandsFree) setTimeout(() => { if (isHandsFree && !isSpeaking) startListening(); }, 1500);
        };

        recognition.onend = () => {
            isListening = false;
            if (!isSpeaking) setAssistantState('idle');
            if (isHandsFree && !isSpeaking) setTimeout(() => { if (isHandsFree && !isSpeaking) startListening(); }, 800);
        };
    }

    langSelect.addEventListener('change', () => {
        currentLanguage = langSelect.value;
        if (recognition) recognition.lang = getSpeechRecLang(currentLanguage);
        const langNames = {
            'auto': 'Auto-Detect', 'en': 'English', 'hi': 'Hindi (हिंदी)',
            'bn': 'Bengali (বাংলা)', 'bho': 'Bhojpuri (भोजपुरी)',
            'bgc': 'Haryanvi (हरियाणवी)', 'mwr': 'Marwadi (मारवाड़ी)'
        };
        appendMessage('assistant', `🌐 Language preference set to **${langNames[currentLanguage]}**.`);
    });

    function startListening() {
        if (!recognition) initSpeechRecognition();
        if (recognition && !isListening && !isSpeaking) {
            try {
                recognition.lang = getSpeechRecLang(currentLanguage);
                recognition.start();
            } catch (e) {
                console.warn("Recognition start busy:", e);
            }
        }
    }

    function stopListening() {
        if (recognition && isListening) {
            recognition.stop();
            isListening = false;
            setAssistantState('idle');
        }
    }

    micBtn.addEventListener('click', () => {
        if (isListening) stopListening();
        else startListening();
    });

    handsFreeBtn.addEventListener('click', () => {
        isHandsFree = !isHandsFree;
        handsFreeBtn.classList.toggle('active', isHandsFree);
        if (isHandsFree) {
            window.soundFX.playStartup();
            appendMessage('assistant', 'Hands-free continuous listening activated. Speak commands naturally at any time.');
            startListening();
        } else {
            stopListening();
            appendMessage('assistant', 'Hands-free mode deactivated.');
        }
    });

    arcReactor.addEventListener('click', () => {
        if (isSpeaking && currentAudio) {
            currentAudio.pause();
            isSpeaking = false;
            setAssistantState('idle');
        } else if (!isListening) {
            startListening();
        }
    });

    // TTS Audio Player
    async function playVoiceResponse(text, targetLang = 'auto', recommendedVoice = '') {
        if (isMuted || !text) return;
        if (currentAudio) {
            currentAudio.pause();
            currentAudio = null;
        }

        isSpeaking = true;
        setAssistantState('speaking');

        try {
            const voiceToUse = recommendedVoice || selectedVoice;
            const ttsUrl = `/api/tts?text=${encodeURIComponent(text)}&voice=${encodeURIComponent(voiceToUse)}&lang=${encodeURIComponent(targetLang)}`;
            currentAudio = new Audio(ttsUrl);

            currentAudio.onended = () => {
                isSpeaking = false;
                setAssistantState('idle');
                if (isHandsFree) setTimeout(() => { if (isHandsFree && !isListening) startListening(); }, 500);
            };

            currentAudio.onerror = () => fallbackBrowserTTS(text, targetLang);
            await currentAudio.play();
        } catch (err) {
            fallbackBrowserTTS(text, targetLang);
        }
    }

    function fallbackBrowserTTS(text, lang) {
        if (!('speechSynthesis' in window)) {
            isSpeaking = false;
            setAssistantState('idle');
            return;
        }

        window.speechSynthesis.cancel();
        const utterance = new SpeechSynthesisUtterance(text);
        utterance.rate = 1.05;
        if (lang === 'bn') utterance.lang = 'bn-IN';
        else if (['hi', 'bho', 'bgc', 'mwr'].includes(lang)) utterance.lang = 'hi-IN';
        else utterance.lang = 'en-US';

        utterance.onend = () => {
            isSpeaking = false;
            setAssistantState('idle');
            if (isHandsFree) setTimeout(() => { if (isHandsFree && !isListening) startListening(); }, 500);
        };
        utterance.onerror = () => {
            isSpeaking = false;
            setAssistantState('idle');
        };
        window.speechSynthesis.speak(utterance);
    }

    muteBtn.addEventListener('click', () => {
        isMuted = !isMuted;
        window.soundFX.muted = isMuted;
        muteBtn.classList.toggle('active', isMuted);
        muteBtn.innerHTML = isMuted ? '🔇' : '🔊';
        if (isMuted && currentAudio) {
            currentAudio.pause();
            isSpeaking = false;
            setAssistantState('idle');
        }
    });

    // Priority Websites Manager
    async function loadPrioritySites() {
        try {
            const res = await fetch('/api/priority-sites');
            const data = await res.json();
            if (data.success && data.sites) {
                renderPriorityChips(data.sites);
            }
        } catch (e) {
            console.warn("Failed to load priority sites:", e);
        }
    }

    function renderPriorityChips(sites) {
        priorityChipsContainer.innerHTML = '';
        Object.keys(sites).forEach(key => {
            const site = sites[key];
            const chip = document.createElement('div');
            chip.className = 'site-chip';
            chip.innerHTML = `<span>${site.icon || '🌐'}</span> <span>${site.name}</span>`;
            chip.title = `Launch ${site.name} (${site.url})`;
            chip.addEventListener('click', () => launchPrioritySite(key, site.name));
            priorityChipsContainer.appendChild(chip);
        });
    }

    async function launchPrioritySite(key, name) {
        window.soundFX.playResponseTone();
        appendMessage('user', `Open ${name}`);
        setAssistantState('thinking');

        try {
            const res = await fetch('/api/priority-sites/launch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ key: key })
            });
            const data = await res.json();
            const voiceText = data.voice_text || `Opening ${name} for you, Sir.`;
            appendMessage('assistant', `🚀 **Opened in Browser:** [${name}](${data.site ? data.site.url : '#'})`);
            await playVoiceResponse(voiceText, currentLanguage);
        } catch (e) {
            appendMessage('assistant', `Failed to launch ${name}.`);
            setAssistantState('idle');
        }
    }

    addSiteBtn.addEventListener('click', () => { addSiteModal.style.display = 'flex'; });
    closeAddSiteBtn.addEventListener('click', () => { addSiteModal.style.display = 'none'; });

    saveNewSiteBtn.addEventListener('click', async () => {
        const key = newSiteKey.value.trim().toLowerCase();
        const name = newSiteName.value.trim();
        const url = newSiteUrl.value.trim();
        const icon = newSiteIcon.value.trim() || '🌐';

        if (!key || !url) {
            alert('Please provide a keyword and valid URL.');
            return;
        }

        const res = await fetch('/api/priority-sites', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ key, name: name || key, url, icon, category: 'Custom' })
        });
        const data = await res.json();
        if (data.success) {
            addSiteModal.style.display = 'none';
            newSiteKey.value = '';
            newSiteName.value = '';
            newSiteUrl.value = '';
            appendMessage('assistant', `Added **${name || key}** to your Priority Sites list.`);
            loadPrioritySites();
        }
    });

    // Query Processing
    async function processUserQuery(query) {
        if (!query || !query.trim()) return;

        chatInput.value = '';
        appendMessage('user', query);
        setAssistantState('thinking');

        try {
            const resp = await fetch('/api/chat', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ 
                    message: query, 
                    voice: selectedVoice,
                    language: currentLanguage
                })
            });

            const data = await resp.json();
            window.soundFX.playResponseTone();

            if (data.intent === 'state_city_weather' && data.card && data.card.location) {
                updateWeatherWidget(data.card.location, data.card);
            }

            appendMessage('assistant', data.display_text || data.voice_text, data.card, data.voice_text, data.language);
            await playVoiceResponse(data.voice_text, data.language || currentLanguage, data.recommended_voice);

        } catch (err) {
            console.error("Chat API error:", err);
            appendMessage('assistant', 'Sir, my network connection encountered a momentary disruption. Please try again.');
            setAssistantState('idle');
        }
    }

    function appendMessage(sender, text, card = null, voiceText = '', lang = '') {
        const bubble = document.createElement('div');
        bubble.className = `chat-bubble ${sender}`;

        const avatar = document.createElement('div');
        avatar.className = `avatar-icon ${sender}`;
        if (sender === 'user') avatar.innerHTML = '👤';
        else avatar.innerHTML = '<img src="/static/images/mbrus_logo.png" alt="MBRUS">';

        const content = document.createElement('div');
        content.className = 'bubble-content';
        content.innerHTML = formatMarkdown(text);

        if (card && card.items && card.items.length > 0) {
            const cardBox = document.createElement('div');
            cardBox.className = 'sports-card';
            cardBox.style.marginTop = '8px';
            cardBox.innerHTML = `
                <div class="sports-card-header">
                    <span>${card.title || 'Live Match Details'}</span>
                    <span class="sports-card-badge">LIVE</span>
                </div>
                ${card.items.map(it => `<div class="sports-card-status">• ${it}</div>`).join('')}
            `;
            content.appendChild(cardBox);
        }

        const meta = document.createElement('div');
        meta.className = 'bubble-meta';
        const now = new Date();
        const timeStr = now.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
        const langBadge = lang && lang !== 'en' ? `<span style="color:var(--neon-cyan);margin-left:6px;">[${lang.toUpperCase()}]</span>` : '';
        meta.innerHTML = `<span>${timeStr} ${langBadge}</span>`;

        if (sender === 'assistant' && voiceText) {
            const speakBtn = document.createElement('button');
            speakBtn.className = 'speak-again-btn';
            speakBtn.textContent = '🔊 Listen again';
            speakBtn.addEventListener('click', () => playVoiceResponse(voiceText, lang || currentLanguage));
            meta.appendChild(speakBtn);
        }

        content.appendChild(meta);
        bubble.appendChild(avatar);
        bubble.appendChild(content);

        chatStream.appendChild(bubble);
        chatStream.scrollTop = chatStream.scrollHeight;
    }

    function formatMarkdown(text) {
        if (!text) return '';
        let formatted = text.replace(/```([a-zA-Z0-9_-]*)\n([\s\S]*?)```/g, (match, lang, code) => {
            const langLabel = lang ? lang.toUpperCase() : 'CODE';
            const escapedCode = code.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
            return `
                <pre>
                    <div class="code-header-bar">
                        <span>${langLabel}</span>
                        <button class="copy-code-btn" onclick="window.copyCodeSnippet(this)">📋 Copy</button>
                    </div><code>${escapedCode}</code>
                </pre>
            `;
        });

        formatted = formatted.replace(/`([^`]+)`/g, '<code style="background:rgba(255,0,51,0.15);color:var(--neon-cyan);padding:2px 5px;border-radius:4px;font-family:var(--font-mono);font-size:12px;">$1</code>');
        formatted = formatted.replace(/### (.*?)\n/g, '<h4 style="color:var(--neon-red-bright);margin:8px 0 4px 0;">$1</h4>');
        formatted = formatted.replace(/## (.*?)\n/g, '<h3 style="color:#fff;margin:10px 0 6px 0;">$1</h3>');
        formatted = formatted.replace(/# (.*?)\n/g, '<h2 style="color:#fff;margin:12px 0 8px 0;">$1</h2>');
        formatted = formatted.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
        formatted = formatted.replace(/\*(.*?)\*/g, '<em>$1</em>');
        formatted = formatted.replace(/\[(.*?)\]\((.*?)\)/g, '<a href="$2" target="_blank" style="color:var(--neon-cyan);text-decoration:none;border-bottom:1px dashed var(--neon-cyan);">$1 ↗</a>');
        formatted = formatted.replace(/\n/g, '<br/>');
        return formatted;
    }

    window.copyCodeSnippet = (btn) => {
        const pre = btn.closest('pre');
        const code = pre ? pre.querySelector('code').innerText : '';
        if (code) {
            navigator.clipboard.writeText(code).then(() => {
                const prev = btn.textContent;
                btn.textContent = '✅ Copied!';
                setTimeout(() => { btn.textContent = prev; }, 2000);
            });
        }
    };

    sendBtn.addEventListener('click', () => processUserQuery(chatInput.value.trim()));
    chatInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') processUserQuery(chatInput.value.trim());
    });

    document.querySelectorAll('.chip-btn:not(#newChatBtn)').forEach(btn => {
        btn.addEventListener('click', () => {
            const prompt = btn.getAttribute('data-prompt');
            processUserQuery(prompt);
        });
    });

    // Sports Feed
    async function loadLiveSports() {
        try {
            const res = await fetch('/api/live/sports');
            const data = await res.json();
            if (data.success && data.matches) {
                sportsCountBadge.textContent = `${data.count} LIVE`;
                renderSportsCards(data.matches);
            }
        } catch (e) {
            console.warn("Sports feed error:", e);
        }
    }

    function renderSportsCards(matches) {
        if (!matches || matches.length === 0) {
            sportsFeed.innerHTML = '<div style="color:var(--text-dim);font-size:12px;">No live games currently active.</div>';
            return;
        }

        sportsFeed.innerHTML = matches.map(m => `
            <div class="sports-card" onclick="window.appTalkSports('${m.title.replace(/'/g, "\\'")}')">
                <div class="sports-card-header">
                    <span>${m.title}</span>
                    <span class="sports-card-badge">LIVE</span>
                </div>
                <div class="sports-card-status">${m.status || m.details}</div>
            </div>
        `).join('');
    }

    window.appTalkSports = (matchTitle) => {
        processUserQuery(`What is running status of ${matchTitle}`);
    };

    // Live Weather (Fallback)
    async function loadLiveWeather() {
        if (userCoords) return;
        try {
            const res = await fetch('/api/live/weather');
            const data = await res.json();
            if (data.success && data.weather) {
                updateWeatherWidget(data.weather.location, data.weather);
            }
        } catch (e) {
            console.warn("Weather error:", e);
        }
    }

    // Telemetry
    async function loadSystemStats() {
        try {
            const res = await fetch('/api/live/system');
            const data = await res.json();
            if (data.success && data.stats) {
                const s = data.stats;
                clockDisplay.textContent = `${s.time} • ${s.date}`;

                cpuVal.textContent = `${s.cpu_percent}%`;
                cpuFill.style.width = `${Math.min(s.cpu_percent, 100)}%`;
                cpuFill.classList.toggle('warn', s.cpu_percent > 80);

                ramVal.textContent = `${s.ram_percent}% (${s.ram_used_gb}G/${s.ram_total_gb}G)`;
                ramFill.style.width = `${Math.min(s.ram_percent, 100)}%`;
                ramFill.classList.toggle('warn', s.ram_percent > 85);

                batteryVal.textContent = `${s.battery_percent}% (${s.battery_charging ? '⚡ Charging' : 'Discharging'})`;
                batteryFill.style.width = `${Math.min(s.battery_percent, 100)}%`;
                diskVal.textContent = `${s.disk_percent}%`;
            }
        } catch (e) {
            console.warn("System stats error:", e);
        }
    }

    // Settings
    settingsBtn.addEventListener('click', async () => {
        try {
            const res = await fetch('/api/settings');
            const data = await res.json();
            cityInput.value = data.default_city || '';
            voiceSelect.value = data.tts_voice || selectedVoice;
            settingsModal.style.display = 'flex';
        } catch (e) {
            settingsModal.style.display = 'flex';
        }
    });

    closeSettingsBtn.addEventListener('click', () => { settingsModal.style.display = 'none'; });

    saveSettingsBtn.addEventListener('click', async () => {
        const city = cityInput.value.trim();
        selectedVoice = voiceSelect.value;
        await fetch('/api/settings', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ default_city: city, tts_voice: selectedVoice })
        });
        settingsModal.style.display = 'none';
        appendMessage('assistant', `Settings updated successfully. Voice set to ${selectedVoice}.`);
        loadLiveWeather();
    });

    // Startup Initializations
    initSpeechRecognition();
    loadPrioritySites();
    loadGeminiStatus();
    requestGPSLocation(false);
    loadLiveSports();
    loadSystemStats();

    setInterval(loadSystemStats, 4000);
    setInterval(loadLiveSports, 30000);

    setTimeout(() => {
        window.soundFX.playStartup();
    }, 500);
});
