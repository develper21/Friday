import { TitleBar } from './components/TitleBar';
import { ParticleWave } from './components/ParticleWave';
import { Waveform } from './components/Waveform';
import { WeatherCard } from './components/WeatherCard';
import { MobileCard } from './components/MobileCard';
import { TimeDateCard } from './components/TimeDateCard';
import { useEffect, useState } from 'react';

function JeanDesktop() {
  const [audioLevel, setAudioLevel] = useState(0);
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [jeanMaxStatus, setJeanMaxStatus] = useState('stopped');

  // Set up IPC listeners for Jean Max
  useEffect(() => {
    if (window.electronAPI) {
      // Listen for Jean Max status updates
      window.electronAPI.onJeanMaxStatus((status) => {
        setJeanMaxStatus(status);
      });

      // Listen for audio level updates
      window.electronAPI.onAudioLevel((level) => {
        setAudioLevel(level);
      });

      // Listen for speaking state
      window.electronAPI.onJeanMaxSpeaking((speaking) => {
        setIsSpeaking(speaking);
      });

      // Auto-start Jean Max when app launches
      window.electronAPI.startJeanMax();
    }

    return () => {
      // Cleanup listeners if needed
    };
  }, []);

  const handleMinimize = () => {
    if (window.electronAPI) {
      window.electronAPI.minimize();
    }
  };

  const handleMaximize = () => {
    if (window.electronAPI) {
      window.electronAPI.maximize();
    }
  };

  const handleClose = () => {
    if (window.electronAPI) {
      window.electronAPI.close();
    }
  };

  const handleMenu = () => {
    console.log('Menu clicked');
  };

  const handleLiveLocation = () => {
    console.log('Live location clicked');
  };

  return (
    <main className="relative flex h-screen w-full flex-col overflow-hidden bg-background">
      {/* subtle depth glow, no boxes / no decorative lines */}
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0"
        style={{
          background:
            'radial-gradient(120% 80% at 50% 45%, rgba(29,55,110,0.35) 0%, rgba(11,15,26,0) 65%)',
        }}
      />

      <div className="relative z-10 flex h-full flex-col">
        <TitleBar
          onMinimize={handleMinimize}
          onMaximize={handleMaximize}
          onClose={handleClose}
          onMenu={handleMenu}
        />

        {/* center particle wave spans the full stage behind the cards */}
        <div className="relative min-h-0 flex-1">
          <div className="pointer-events-none absolute inset-y-[10%] left-[27%] right-[27%]">
            <ParticleWave audioLevel={audioLevel} isSpeaking={isSpeaking} />
          </div>

          <div className="relative flex h-full items-center justify-between px-8">
            <WeatherCard />
            <TimeDateCard />
            <MobileCard onLiveLocation={handleLiveLocation} />
          </div>
        </div>

        {/* bottom audio waveform */}
        <div className="mx-auto h-[120px] w-[54%] shrink-0 pb-6">
          <Waveform />
        </div>
      </div>
    </main>
  );
}

export default JeanDesktop;
