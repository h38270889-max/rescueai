/**
 * ResQAI Emergency Chatbot Assistant Interface.
 * Real-time conversation handling, AI triage badges, speech-to-text (voice input),
 * and multilingual text-to-speech spoken guidance.
 */

document.addEventListener('DOMContentLoaded', () => {
  const chatForm = document.getElementById('chat-form');
  const chatInput = document.getElementById('chat-input');
  const chatMessages = document.getElementById('chat-messages');
  const clearChatBtn = document.getElementById('btn-clear-chat');
  const langSelect = document.getElementById('chat-lang-select');
  const sessionId = document.getElementById('chat-session-id')?.value;
  const micBtn = document.getElementById('btn-mic');
  const voiceIndicator = document.getElementById('voice-indicator');
  const voiceStatusText = document.getElementById('voice-status-text');
  const stopVoiceBtn = document.getElementById('btn-stop-voice');

  if (!chatForm || !chatInput || !chatMessages) return;

  // BCP-47 Speech Locales for Web Speech API
  const SPEECH_LOCALES = {
    'en': 'en-US',
    'hi': 'hi-IN',
    'mr': 'mr-IN',
    'ur': 'ur-PK',
    'bn': 'bn-IN',
    'ta': 'ta-IN',
    'te': 'te-IN',
    'gu': 'gu-IN',
    'kn': 'kn-IN',
    'ml': 'ml-IN',
    'pa': 'pa-IN',
    'es': 'es-ES',
    'ar': 'ar-SA',
    'fr': 'fr-FR'
  };

  // Simple Markdown parser for bold, bullet points, and emergency hotlines
  function formatMarkdown(text) {
    if (!text) return '';
    let escaped = text
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Bold
    escaped = escaped.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    // Bullet points
    escaped = escaped.replace(/^\s*[\*\-]\s+(.+)$/gm, '<li>$1</li>');
    escaped = escaped.replace(/(<li>.*<\/li>)/s, '<ul class="mb-2 ps-3">$1</ul>');
    // Line breaks
    escaped = escaped.replace(/\n/g, '<br>');
    return escaped;
  }

  // Clean markdown and HTML for spoken text-to-speech output
  function cleanTextForSpeech(text) {
    if (!text) return '';
    return text
      .replace(/\[(.*?)\]\(.*?\)/g, '$1')
      .replace(/[*_`#~]/g, '')
      .replace(/<[^>]+>/g, '')
      .replace(/^\s*[-•*]\s+/gm, ', ')
      .replace(/\s+/g, ' ')
      .trim();
  }

  // Speak aloud via Web Speech Synthesis
  function speakResponse(rawText) {
    if (!('speechSynthesis' in window)) {
      alert('Speech synthesis is not supported on this browser.');
      return;
    }

    window.speechSynthesis.cancel(); // Stop any previous speech
    const clean = cleanTextForSpeech(rawText);
    const utterance = new SpeechSynthesisUtterance(clean);
    
    const curLang = langSelect ? langSelect.value : 'en';
    utterance.lang = SPEECH_LOCALES[curLang] || 'en-US';
    utterance.rate = 1.0;
    utterance.pitch = 1.0;

    window.speechSynthesis.speak(utterance);
  }

  function appendMessage(sender, text, meta = {}) {
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${sender}`;

    const formattedText = formatMarkdown(text);
    let metaHtml = '';

    if (sender === 'assistant') {
      const urgencyClass = meta.urgency === 'Critical' ? 'bg-danger text-white' :
                           meta.urgency === 'High' ? 'bg-warning text-dark' : 'bg-info text-dark';
      
      const fallbackBadge = meta.is_fallback
        ? '<span class="badge bg-secondary ms-1"><i class="bi bi-shield-check"></i> Rule-Based Triage</span>'
        : '<span class="badge bg-primary ms-1"><i class="bi bi-robot"></i> AI Engine</span>';

      metaHtml = `
        <div class="message-meta d-flex align-items-center justify-content-between mt-2 pt-1 border-top border-light">
          <div class="d-flex align-items-center gap-1 flex-wrap">
            <span>${meta.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
            ${meta.urgency ? `<span class="badge ${urgencyClass}">${meta.urgency}</span>` : ''}
            ${meta.category ? `<span class="badge bg-light text-dark border">${meta.category.replace('_', ' ')}</span>` : ''}
            ${fallbackBadge}
          </div>
          <div>
            <button type="button" class="btn btn-sm btn-link text-muted p-0 btn-speak" title="Listen to spoken instructions">
              <i class="bi bi-volume-up-fill fs-6 text-primary"></i>
            </button>
          </div>
        </div>
      `;
    } else {
      metaHtml = `
        <div class="message-meta text-end mt-1">
          <span>${new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
        </div>
      `;
    }

    bubble.innerHTML = `<div>${formattedText}</div>${metaHtml}`;
    chatMessages.appendChild(bubble);
    chatMessages.scrollTop = chatMessages.scrollHeight;

    // Attach speak listener if assistant message
    if (sender === 'assistant') {
      const speakBtn = bubble.querySelector('.btn-speak');
      if (speakBtn) {
        speakBtn.addEventListener('click', () => speakResponse(text));
      }
    }
  }

  function showTypingIndicator() {
    const indicator = document.createElement('div');
    indicator.className = 'typing-indicator';
    indicator.id = 'typing-indicator';
    indicator.innerHTML = `
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
      <span class="typing-dot"></span>
    `;
    chatMessages.appendChild(indicator);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function removeTypingIndicator() {
    const el = document.getElementById('typing-indicator');
    if (el) el.remove();
  }

  async function sendMessage(messageText) {
    if (!messageText.trim()) return;

    appendMessage('user', messageText);
    chatInput.value = '';
    showTypingIndicator();

    const selectedLang = langSelect ? langSelect.value : 'en';

    try {
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          message: messageText,
          session_id: sessionId,
          language: selectedLang
        })
      });

      removeTypingIndicator();

      if (response.ok) {
        const data = await response.json();
        appendMessage('assistant', data.reply, {
          category: data.category,
          urgency: data.urgency,
          is_fallback: data.is_fallback,
          timestamp: data.timestamp
        });
      } else {
        appendMessage('assistant', '⚠️ Unable to process emergency advice. Please dial official helpline 112 directly.', {
          urgency: 'Critical',
          is_fallback: true
        });
      }
    } catch (err) {
      removeTypingIndicator();
      appendMessage('assistant', '⚠️ Network communication error. If you are in immediate danger, please dial 112 immediately.', {
        urgency: 'Critical',
        is_fallback: true
      });
    }
  }

  // Handle Form Submission
  chatForm.addEventListener('submit', (e) => {
    e.preventDefault();
    sendMessage(chatInput.value);
  });

  // Handle Suggested Query Pills
  document.querySelectorAll('.suggested-query-pill').forEach((btn) => {
    btn.addEventListener('click', () => {
      const query = btn.getAttribute('data-query');
      if (query) sendMessage(query);
    });
  });

  // Handle Speech Recognition (Web Speech API)
  const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
  let recognition = null;
  let isListening = false;

  if (SpeechRecognition && micBtn) {
    recognition = new SpeechRecognition();
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      isListening = true;
      micBtn.classList.add('btn-danger', 'text-white');
      micBtn.classList.remove('btn-outline-secondary');
      if (voiceIndicator) voiceIndicator.classList.remove('d-none');
      if (voiceStatusText) voiceStatusText.textContent = "Listening... Speak your emergency clearly.";
    };

    recognition.onresult = (event) => {
      let interimTranscript = '';
      let finalTranscript = '';

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        if (event.results[i].isFinal) {
          finalTranscript += event.results[i][0].transcript;
        } else {
          interimTranscript += event.results[i][0].transcript;
        }
      }

      if (finalTranscript) {
        chatInput.value = finalTranscript;
      } else if (interimTranscript) {
        chatInput.value = interimTranscript;
      }
    };

    recognition.onerror = (event) => {
      console.warn('Speech recognition error:', event.error);
      stopListening();
      if (voiceStatusText) voiceStatusText.textContent = `Mic error: ${event.error}`;
      setTimeout(() => {
        if (voiceIndicator) voiceIndicator.classList.add('d-none');
      }, 3000);
    };

    recognition.onend = () => {
      stopListening();
    };

    function startListening() {
      const curLang = langSelect ? langSelect.value : 'en';
      recognition.lang = SPEECH_LOCALES[curLang] || 'en-US';
      try {
        recognition.start();
      } catch (err) {
        console.warn('Recognition already started:', err);
      }
    }

    function stopListening() {
      isListening = false;
      micBtn.classList.remove('btn-danger', 'text-white');
      micBtn.classList.add('btn-outline-secondary');
      if (voiceIndicator) voiceIndicator.classList.add('d-none');
      try {
        recognition.stop();
      } catch (e) {}
    }

    micBtn.addEventListener('click', () => {
      if (!isListening) {
        startListening();
      } else {
        stopListening();
      }
    });

    if (stopVoiceBtn) {
      stopVoiceBtn.addEventListener('click', stopListening);
    }
  } else if (micBtn) {
    micBtn.title = "Speech recognition is not supported in this browser";
    micBtn.disabled = true;
  }

  // Handle Clear Conversation
  if (clearChatBtn) {
    clearChatBtn.addEventListener('click', async () => {
      if (!confirm('Are you sure you want to clear this emergency chat conversation?')) return;
      try {
        await fetch('/api/chat/clear', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ session_id: sessionId })
        });
        chatMessages.innerHTML = '';
        appendMessage('assistant', 'Conversation cleared. How can ResQAI Emergency Assistant help you right now?');
      } catch (err) {
        console.error('Error clearing conversation:', err);
      }
    });
  }

  // Load Past History
  async function loadChatHistory() {
    try {
      const res = await fetch(`/api/chat/history?session_id=${sessionId}`);
      if (res.ok) {
        const data = await res.json();
        if (data.messages && data.messages.length > 0) {
          chatMessages.innerHTML = '';
          data.messages.forEach((m) => {
            appendMessage(m.sender, m.message, {
              category: m.detected_category,
              urgency: m.detected_urgency,
              is_fallback: m.is_fallback,
              timestamp: m.created_at
            });
          });
        }
      }
    } catch (e) {
      console.warn('Could not load history:', e);
    }
  }

  loadChatHistory();
});
