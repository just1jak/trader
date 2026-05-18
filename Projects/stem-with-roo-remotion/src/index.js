import React from 'react';
import {Composition, registerRoot, useCurrentFrame, interpolate, Easing} from 'remotion';

const MyVideoContent = () => {
  const frame = useCurrentFrame();
  const fps = 30;
  const segmentDuration = 3 * fps; // 90 frames per 3-second segment

  // Wire height: grows in segment 1 (index 1) from 0 to 100px
  const wireHeight = interpolate(
    frame,
    [1 * segmentDuration, 2 * segmentDuration], // segment 1: frames 90-180
    [0, 100],
    Easing.easeInOutQuad,
  );

  // Bulb opacity: turns on in segment 2 (index 2) from 0 to 1
  const bulbOpacity = interpolate(
    frame,
    [2 * segmentDuration, 3 * segmentDuration], // segment 2: frames 180-270
    [0, 1],
    Easing.easeInOutQuad,
  );

  // Switch rotation: flips in segment 3 (index 3) from 0 to -45 degrees
  const switchRotation = interpolate(
    frame,
    [3 * segmentDuration, 4 * segmentDuration], // segment 3: frames 270-360
    [0, -45],
    Easing.easeInOutQuad,
  );

  // Text for each segment
  const getTextForSegment = (segmentIndex) => {
    switch (segmentIndex) {
      case 0: return "Hi! I'm Roo!";
      case 1: return "This is a battery. It gives energy.";
      case 2: return "When the wire connects, the light turns on!";
      case 3: return "Add a switch to turn it off and on.";
      case 4: return "Try making your own circuit!\\nNext: Build a flashlight!";
      default: return "";
    }
  };

  const currentSegmentIndex = Math.min(Math.floor(frame / segmentDuration), 4);
  const text = getTextForSegment(currentSegmentIndex);

  // Roo's vertical bounce (just a little movement to show waving)
  const rooBounce = interpolate(
    frame % fps, // bounce every second
    [0, fps/2, fps],
    [0, 10, 0],
    Easing.easeInOutQuad,
  );

  return (
    <>
      {/* Background */}
      <div style={{backgroundColor: '#87CEEB', width: '100%', height: '100%'}} />

      {/* Roo Character */}
      <div 
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          transform: `translate(-50%, calc(-50% + ${rooBounce}px))`,
          width: '200px',
          height: '200px',
          backgroundColor: '#FF6B6B',
          borderRadius: '50%',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'white',
          fontSize: '24px',
          fontWeight: 'bold',
        }}
      >
        Roo
      </div>

      {/* Battery */}
      <div 
        style={{
          position: 'absolute',
          top: '30%',
          left: '30%',
          width: '60px',
          height: '100px',
          backgroundColor: '#FFA500',
          border: '2px solid #333',
        }}
      >
        <div style={{position: 'absolute', top: '0', left: '25%', width: '50%', height: '20px', backgroundColor: '#FFA500'}} />
      </div>

      {/* Wire */}
      <div 
        style={{
          position: 'absolute',
          top: '50%',
          left: '40%',
          width: '2px',
          height: `${wireHeight}px`,
          backgroundColor: '#000',
          transformOrigin: 'top',
        }}
      />

      {/* Light Bulb */}
      <div 
        style={{
          position: 'absolute',
          top: '40%',
          left: '60%',
          width: '50px',
          height: '70px',
          backgroundColor: '#FFFF00',
          borderRadius: '50% 50% 40% 40%',
          border: '2px solid #333',
          opacity: bulbOpacity,
        }}
      >
        <div style={{position: 'absolute', top: '-10px', left: '25%', width: '50%', height: '10px', backgroundColor: '#FFFF00'}} />
      </div>

      {/* Switch */}
      <div 
        style={{
          position: 'absolute',
          top: '50%',
          left: '50%',
          width: '40px',
          height: '20px',
          backgroundColor: '#808080',
          borderRadius: '10px',
          transform: `translate(-50%, -50%) rotate(${switchRotation}deg)`,
          transformOrigin: 'center',
        }}
      >
        <div style={{position: 'absolute', top: '-5px', left: '50%', width: '10px', height: '10px', backgroundColor: '#333', borderRadius: '50%', transform: 'translate(-50%, -50%)'}} />
      </div>

      {/* Text */}
      <div 
        style={{
          position: 'absolute',
          top: '10%',
          left: '50%',
          transform: 'translateX(-50%)',
          fontSize: '36px',
          color: '#333',
          textAlign: 'center',
          width: '80%',
          lineHeight: '1.2',
        }}
      >
        {text.split('\\n').map((line, index) => (
          <React.Fragment key={index}>
            {line}
            <br />
          </React.Fragment>
        ))}
      </div>
    </>
  );
};

const MyVideo = () => {
  return (
    <Composition
      id="MyVideo"
      width={1080}
      height={1080}
      fps={30}
      durationInFrames={450}
      component={MyVideoContent}
    />
  );
};

registerRoot(MyVideo);
export default MyVideo;