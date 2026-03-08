import { useRef, useEffect } from 'react';
import { Message } from '@/types';
import { User, Bot, Volume2 } from 'lucide-react';
import clsx from 'clsx';
import { format } from 'date-fns';

interface MessageListProps {
  messages: Message[];
  isProcessing?: boolean;
  onPlayAudio?: (audioUrl: string) => void;
}

export function MessageList({
  messages,
  isProcessing = false,
  onPlayAudio,
}: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isProcessing]);

  return (
    <div className="flex-1 overflow-y-auto p-4 space-y-4">
      {messages.length === 0 && !isProcessing && (
        <div className="flex flex-col items-center justify-center h-full text-gray-400">
          <Bot className="w-16 h-16 mb-4 opacity-50" />
          <p className="text-lg">Start a conversation</p>
          <p className="text-sm">Tap the microphone to speak or type a message</p>
        </div>
      )}

      {messages.map((message) => (
        <MessageBubble
          key={message.id}
          message={message}
          onPlayAudio={onPlayAudio}
        />
      ))}

      {isProcessing && (
        <div className="flex items-start gap-3">
          <div className="w-8 h-8 rounded-full bg-care-blue flex items-center justify-center flex-shrink-0">
            <Bot className="w-5 h-5 text-white" />
          </div>
          <div className="bg-gray-100 rounded-2xl rounded-tl-none px-4 py-3">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
              <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

interface MessageBubbleProps {
  message: Message;
  onPlayAudio?: (audioUrl: string) => void;
}

function MessageBubble({ message, onPlayAudio }: MessageBubbleProps) {
  const isUser = message.type === 'user';
  const isSystem = message.type === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <span className="text-xs text-gray-400 bg-gray-100 px-3 py-1 rounded-full">
          {message.content}
        </span>
      </div>
    );
  }

  return (
    <div
      className={clsx(
        'flex items-start gap-3',
        isUser && 'flex-row-reverse'
      )}
    >
      <div
        className={clsx(
          'w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0',
          isUser ? 'bg-care-green' : 'bg-care-blue'
        )}
      >
        {isUser ? (
          <User className="w-5 h-5 text-white" />
        ) : (
          <Bot className="w-5 h-5 text-white" />
        )}
      </div>

      <div
        className={clsx(
          'max-w-[75%] rounded-2xl px-4 py-3',
          isUser
            ? 'bg-care-blue text-white rounded-tr-none'
            : 'bg-gray-100 text-gray-800 rounded-tl-none'
        )}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
        
        <div className={clsx(
          'flex items-center gap-2 mt-1',
          isUser ? 'justify-start' : 'justify-end'
        )}>
          {message.audioUrl && onPlayAudio && (
            <button
              onClick={() => onPlayAudio(message.audioUrl!)}
              className={clsx(
                'p-1 rounded-full transition-colors',
                isUser
                  ? 'hover:bg-white/20 text-white/80'
                  : 'hover:bg-gray-200 text-gray-500'
              )}
              title="Play audio"
            >
              <Volume2 className="w-4 h-4" />
            </button>
          )}
          <span
            className={clsx(
              'text-xs',
              isUser ? 'text-white/70' : 'text-gray-400'
            )}
          >
            {format(message.timestamp, 'HH:mm')}
          </span>
        </div>
      </div>
    </div>
  );
}
