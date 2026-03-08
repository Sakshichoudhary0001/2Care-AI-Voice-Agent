import { Mic, MicOff, Square } from 'lucide-react';
import clsx from 'clsx';

interface VoiceRecorderProps {
  isRecording: boolean;
  isProcessing: boolean;
  audioLevel: number;
  hasPermission: boolean | null;
  onToggle: () => void;
  disabled?: boolean;
}

export function VoiceRecorder({
  isRecording,
  isProcessing,
  audioLevel,
  hasPermission,
  onToggle,
  disabled = false,
}: VoiceRecorderProps) {
  const canRecord = hasPermission !== false && !disabled && !isProcessing;

  return (
    <div className="relative flex items-center justify-center">
      {/* Pulsing rings when recording */}
      {isRecording && (
        <>
          <div
            className="absolute w-20 h-20 rounded-full bg-red-500/20 animate-pulse-ring"
            style={{ animationDelay: '0ms' }}
          />
          <div
            className="absolute w-24 h-24 rounded-full bg-red-500/10 animate-pulse-ring"
            style={{ animationDelay: '200ms' }}
          />
        </>
      )}

      {/* Audio level indicator */}
      {isRecording && (
        <div
          className="absolute w-16 h-16 rounded-full bg-red-500/30 transition-transform duration-75"
          style={{ transform: `scale(${1 + audioLevel * 0.5})` }}
        />
      )}

      {/* Main button */}
      <button
        onClick={onToggle}
        disabled={!canRecord}
        className={clsx(
          'relative w-16 h-16 rounded-full flex items-center justify-center transition-all duration-200',
          'focus:outline-none focus:ring-4',
          isRecording
            ? 'bg-red-500 hover:bg-red-600 focus:ring-red-300 text-white'
            : 'bg-care-blue hover:bg-blue-700 focus:ring-blue-300 text-white',
          !canRecord && 'opacity-50 cursor-not-allowed',
          isProcessing && 'animate-pulse'
        )}
        aria-label={isRecording ? 'Stop recording' : 'Start recording'}
      >
        {isRecording ? (
          <Square className="w-6 h-6" fill="currentColor" />
        ) : hasPermission === false ? (
          <MicOff className="w-7 h-7" />
        ) : (
          <Mic className="w-7 h-7" />
        )}
      </button>

      {/* Status text */}
      <div className="absolute -bottom-8 text-center">
        <span
          className={clsx(
            'text-sm font-medium',
            isRecording ? 'text-red-500' : 'text-gray-500'
          )}
        >
          {isProcessing
            ? 'Processing...'
            : isRecording
            ? 'Listening...'
            : hasPermission === false
            ? 'Mic disabled'
            : 'Tap to speak'}
        </span>
      </div>
    </div>
  );
}

// Voice wave animation component for visual feedback
interface VoiceWaveProps {
  isActive: boolean;
  level: number;
}

export function VoiceWave({ isActive, level }: VoiceWaveProps) {
  const bars = 5;
  
  return (
    <div className="flex items-center justify-center gap-1 h-8">
      {Array.from({ length: bars }).map((_, i) => (
        <div
          key={i}
          className={clsx(
            'w-1 bg-care-blue rounded-full transition-all duration-100',
            isActive ? 'animate-voice-wave' : 'h-2'
          )}
          style={{
            height: isActive ? `${Math.max(8, level * 32 + Math.random() * 16)}px` : '8px',
            animationDelay: `${i * 100}ms`,
          }}
        />
      ))}
    </div>
  );
}
