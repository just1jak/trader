import React from 'react';
import {Composition, registerRoot} from 'remotion';

const TestVideoContent = () => {
  return (
    <div style={{color: 'white', fontSize: 100, display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100%'}}>
      Hello World
    </div>
  );
};

const TestVideo = () => {
  return (
    <Composition
      id="TestVideo"
      width={1080}
      height={1080}
      fps={30}
      durationInFrames={90}
      component={TestVideoContent}
    />
  );
};

registerRoot(TestVideo);
export default TestVideo;