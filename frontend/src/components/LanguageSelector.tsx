import { Language, LANGUAGES } from '@/types';
import { Globe } from 'lucide-react';
import clsx from 'clsx';

interface LanguageSelectorProps {
  language: Language;
  onChange: (language: Language) => void;
  disabled?: boolean;
}

export function LanguageSelector({
  language,
  onChange,
  disabled = false,
}: LanguageSelectorProps) {
  return (
    <div className="flex items-center gap-2">
      <Globe className="w-5 h-5 text-gray-400" />
      <div className="flex rounded-lg overflow-hidden border border-gray-200">
        {(Object.keys(LANGUAGES) as Language[]).map((lang) => (
          <button
            key={lang}
            onClick={() => onChange(lang)}
            disabled={disabled}
            className={clsx(
              'px-3 py-1.5 text-sm font-medium transition-colors',
              language === lang
                ? 'bg-care-blue text-white'
                : 'bg-white text-gray-600 hover:bg-gray-50',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
          >
            {LANGUAGES[lang].nativeName}
          </button>
        ))}
      </div>
    </div>
  );
}
