const express = require('express');
const axios = require('axios');

const router = express.Router();

const systemInstruction = `You are HealthTrack+ AI, a helpful and professional medical assistant. 
Your goal is to help users understand their health data, provide general wellness advice, 
and assist with navigating the HealthTrack+ platform.
Always include a disclaimer that you are an AI and not a substitute for professional medical advice.`;

router.post('/api', async (req, res) => {
  try {
    const { message } = req.body;
    if (!message) return res.status(400).json({ error: 'No message provided' });

    const groqKey = process.env.GROQ_API_KEY;
    if (groqKey && groqKey !== 'your_groq_api_key_here') {
      try {
        const response = await axios.post(
          'https://api.groq.com/openai/v1/chat/completions',
          {
            model: 'llama-3.3-70b-versatile',
            messages: [
              { role: 'system', content: systemInstruction },
              { role: 'user', content: message }
            ]
          },
          {
            headers: { Authorization: `Bearer ${groqKey}`, 'Content-Type': 'application/json' },
            timeout: 30000
          }
        );
        if (response.data && response.data.choices && response.data.choices[0]) {
          return res.json({ response: response.data.choices[0].message.content });
        }
      } catch (err) {
        console.warn('Groq API error, falling back to OpenRouter:', err.message);
      }
    }

    let apiKey = process.env.OPENAI_API_KEY;
    if (!apiKey) {
      const legacyKey = process.env.GOOGLE_API_KEY;
      if (legacyKey && legacyKey.startsWith('sk-or-v1')) apiKey = legacyKey;
    }
    if (!apiKey) {
      return res.status(503).json({ error: 'Server configuration error: API key missing' });
    }

    const response = await axios.post(
      'https://openrouter.ai/api/v1/chat/completions',
      {
        model: 'google/gemini-2.0-flash-001',
        messages: [
          { role: 'system', content: systemInstruction },
          { role: 'user', content: message }
        ]
      },
      {
        headers: { Authorization: `Bearer ${apiKey}`, 'Content-Type': 'application/json' },
        timeout: 30000
      }
    );

    if (response.status !== 200) {
      throw new Error(`OpenRouter API error: ${JSON.stringify(response.data)}`);
    }

    const completionText = response.data.choices[0].message.content;
    res.json({ response: completionText });
  } catch (e) {
    console.error('Chatbot API error:', e.message);
    res.status(500).json({ error: 'Chat service error. Please try again later.' });
  }
});

router.post('/api/tts', async (req, res) => {
  try {
    const { text } = req.body;
    if (!text || !text.trim()) return res.status(400).json({ error: 'No text provided' });

    const apiKey = process.env.SARVAM_API_KEY;
    if (!apiKey || apiKey === 'your_sarvam_api_key_here') {
      return res.status(503).json({ error: 'TTS configuration error: API key missing' });
    }

    let ttsText = text.trim();
    if (ttsText.length > 450) ttsText = ttsText.slice(0, 450) + '...';

    const response = await axios.post(
      'https://api.sarvam.ai/text-to-speech',
      {
        inputs: [ttsText],
        target_language_code: 'hi-IN',
        speaker: 'priya',
        pitch: 0,
        pace: 1.0,
        loudness: 1.5,
        speech_sample_rate: 22050,
        enable_preprocessing: true
      },
      {
        headers: {
          'Content-Type': 'application/json',
          'api-subscription-key': apiKey
        },
        timeout: 30000
      }
    );

    if (response.status === 200 && response.data.audios && response.data.audios.length > 0) {
      return res.json({ audio: response.data.audios[0] });
    }
    res.status(500).json({ error: 'Invalid response from TTS service' });
  } catch (e) {
    console.error('TTS API error:', e.message);
    res.status(500).json({ error: 'TTS service encountered an error.' });
  }
});

module.exports = router;
