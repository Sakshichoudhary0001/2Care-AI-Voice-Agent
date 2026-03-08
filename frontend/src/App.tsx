import { useState, useEffect } from 'react';
import { VoiceChat } from '@/components';
import { Heart, Shield, Clock } from 'lucide-react';

function App() {
  const [sessionId, setSessionId] = useState<string>('');

  useEffect(() => {
    // Generate a unique session ID
    const id = `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    setSessionId(id);
  }, []);

  if (!sessionId) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="animate-spin w-8 h-8 border-4 border-care-blue border-t-transparent rounded-full" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 flex flex-col">
      {/* Top banner */}
      <div className="bg-gradient-to-r from-care-blue to-care-green text-white py-2 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm">
          <div className="flex items-center gap-6">
            <span className="flex items-center gap-1">
              <Shield className="w-4 h-4" />
              HIPAA Compliant
            </span>
            <span className="flex items-center gap-1">
              <Clock className="w-4 h-4" />
              24/7 Available
            </span>
          </div>
          <span className="flex items-center gap-1">
            <Heart className="w-4 h-4" />
            Caring for you
          </span>
        </div>
      </div>

      {/* Main chat interface */}
      <main className="flex-1 max-w-5xl w-full mx-auto flex flex-col shadow-lg my-4 rounded-lg overflow-hidden bg-white" style={{ height: 'calc(100vh - 80px)' }}>
        <VoiceChat sessionId={sessionId} />
      </main>

      {/* Footer */}
      <footer className="bg-white border-t border-gray-200 py-3 px-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between text-sm text-gray-500">
          <p>© 2026 2Care.ai - AI-Powered Healthcare Assistance</p>
          <div className="flex items-center gap-4">
            <a href="#" className="hover:text-care-blue">Privacy Policy</a>
            <a href="#" className="hover:text-care-blue">Terms of Service</a>
            <a href="#" className="hover:text-care-blue">Contact Us</a>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;
