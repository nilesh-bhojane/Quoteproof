import { useState, useEffect } from 'react';

/**
 * Timer Component — Person B
 * Placed on the quotation workflow to record assisted workflow seconds.
 * Posts timing to /api/v1/timings.
 */
export default function Timer({ quoteId = 'active-quote', onTimingRecorded }) {
  const [seconds, setSeconds] = useState(0);
  const [isRunning, setIsRunning] = useState(true);

  useEffect(() => {
    let interval = null;
    if (isRunning) {
      interval = setInterval(() => {
        setSeconds(prev => prev + 1);
      }, 1000);
    } else if (!isRunning && seconds !== 0) {
      clearInterval(interval);
    }
    return () => clearInterval(interval);
  }, [isRunning, seconds]);

  const formatTime = sec => {
    const m = Math.floor(sec / 60);
    const s = sec % 60;
    return `${m.toString().padStart(2, '0')}:${s.toString().padStart(2, '0')}`;
  };

  const handleStopAndRecord = () => {
    setIsRunning(false);
    fetch('/api/v1/timings', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        quote_id: quoteId,
        kind: 'assisted',
        seconds: Math.max(1, seconds),
      }),
    }).catch(() => {});

    if (onTimingRecorded) {
      onTimingRecorded(seconds);
    }
  };

  const handleReset = () => {
    setSeconds(0);
    setIsRunning(true);
  };

  return (
    <div
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: 12,
        padding: '6px 14px',
        background: '#f0f7f6',
        border: '1px solid #cce8e4',
        borderRadius: 999,
        fontSize: 12,
        fontWeight: 600,
        color: '#1d4a6e',
      }}
    >
      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 6 }}>
        <span
          style={{
            width: 8,
            height: 8,
            borderRadius: '50%',
            background: isRunning ? '#18754d' : '#8c5d09',
            animation: isRunning ? 'pulse 1.5s infinite' : 'none',
          }}
        />
        Assisted Cycle:
      </span>
      <strong style={{ fontFamily: 'monospace', fontSize: 14 }}>{formatTime(seconds)}</strong>
      {isRunning ? (
        <button
          onClick={handleStopAndRecord}
          style={{
            background: 'none',
            border: 'none',
            color: '#328a82',
            cursor: 'pointer',
            padding: 0,
            fontSize: 11,
            textDecoration: 'underline',
          }}
        >
          Pause & Record
        </button>
      ) : (
        <button
          onClick={handleReset}
          style={{
            background: 'none',
            border: 'none',
            color: '#328a82',
            cursor: 'pointer',
            padding: 0,
            fontSize: 11,
            textDecoration: 'underline',
          }}
        >
          Resume
        </button>
      )}
    </div>
  );
}
