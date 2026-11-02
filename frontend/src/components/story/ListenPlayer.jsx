import React, { useState, useEffect, useRef } from 'react';
import { Volume2, VolumeX, Play, Pause, Headphones } from 'lucide-react';

/**
 * Audio experience for listening to story briefs.
 * Uses the Web Speech API with an explicit disclaimer identifying it as a browser preview.
 */
export default function ListenPlayer({
  textToRead,
  headline,
  accentColor = '#00E5FF',
}) {
  const [isPlaying, setIsPlaying] = useState(false);
  const [progress, setProgress] = useState(0);
  const [isSupported, setIsSupported] = useState(true);
  const utteranceRef = useRef(null);
  const timerRef = useRef(null);

  useEffect(() => {
    if (!('speechSynthesis' in window)) {
      setIsSupported(false);
    }
    return () => {
      if ('speechSynthesis' in window) {
        window.speechSynthesis.cancel();
      }
      if (timerRef.current) clearInterval(timerRef.current);
    };
  }, []);

  const handleTogglePlay = () => {
    if (!isSupported) {
      alert('Text-to-speech audio preview is not supported by this browser.');
      return;
    }

    if (isPlaying) {
      window.speechSynthesis.cancel();
      setIsPlaying(false);
      if (timerRef.current) clearInterval(timerRef.current);
    } else {
      window.speechSynthesis.cancel();

      const text = `${headline}. ${textToRead}`;
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;

      // Select natural English voice if available
      const voices = window.speechSynthesis.getVoices();
      const engVoice = voices.find(
        (v) => v.lang.startsWith('en') && (v.name.includes('Natural') || v.name.includes('Google') || v.name.includes('Neural'))
      ) || voices.find((v) => v.lang.startsWith('en'));

      if (engVoice) utterance.voice = engVoice;

      utterance.onend = () => {
        setIsPlaying(false);
        setProgress(100);
        if (timerRef.current) clearInterval(timerRef.current);
      };

      utterance.onerror = (e) => {
        console.warn('Speech synthesis notice:', e);
        setIsPlaying(false);
        if (timerRef.current) clearInterval(timerRef.current);
      };

      utteranceRef.current = utterance;
      window.speechSynthesis.speak(utterance);
      setIsPlaying(true);
      setProgress(5);

      const estimatedDurationSeconds = Math.max(10, Math.round(text.split(' ').length / 2.5));
      let elapsed = 0;
      timerRef.current = setInterval(() => {
        elapsed += 1;
        const currentProgress = Math.min(95, Math.round((elapsed / estimatedDurationSeconds) * 100));
        setProgress(currentProgress);
      }, 1000);
    }
  };

  return (
    <div
      className="listen-player-bar"
      style={{
        borderLeft: `3px solid ${accentColor}`,
      }}
    >
      <button
        className="play-pause-btn"
        onClick={handleTogglePlay}
        title={isPlaying ? 'Pause voiceover' : 'Listen to story brief'}
        style={{
          background: accentColor,
          color: '#07080B',
        }}
        aria-label={isPlaying ? 'Pause Audio Brief' : 'Play Audio Brief'}
      >
        {isPlaying ? <Pause size={18} fill="#07080B" /> : <Play size={18} fill="#07080B" />}
      </button>

      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 8, marginBottom: 6 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 6 }}>
            <Headphones size={14} style={{ color: accentColor }} />
            <span style={{ fontSize: 13, fontWeight: 700, color: '#ffffff' }}>
              Listen to Brief
            </span>
          </div>
          <span
            style={{
              fontSize: 10.5,
              fontWeight: 600,
              padding: '2px 8px',
              borderRadius: 4,
              background: 'rgba(255, 255, 255, 0.08)',
              color: '#94a3b8',
            }}
          >
            Browser Speech Preview — ESTD Voice Synthesis
          </span>
        </div>

        {/* Progress track */}
        <div
          style={{
            width: '100%',
            height: 4,
            background: 'rgba(255, 255, 255, 0.1)',
            borderRadius: 2,
            overflow: 'hidden',
          }}
        >
          <div
            style={{
              width: `${isPlaying ? progress : 0}%`,
              height: '100%',
              background: accentColor,
              transition: 'width 0.4s ease',
            }}
          />
        </div>
      </div>
    </div>
  );
}
