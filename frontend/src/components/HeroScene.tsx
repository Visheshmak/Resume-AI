import { Canvas, useFrame } from "@react-three/fiber";
import { Float, Line, OrbitControls, PerspectiveCamera, Sparkles } from "@react-three/drei";
import { useRef } from "react";
import * as THREE from "three";

const nodes = [
  { position: [-1.5, 1.1, 0.35] as [number, number, number], color: "#d9ff72", label: "skills" },
  { position: [1.7, 0.9, -0.1] as [number, number, number], color: "#7ee7da", label: "evidence" },
  { position: [1.35, -1.25, 0.2] as [number, number, number], color: "#f5b971", label: "match" },
  { position: [-1.7, -1.15, -0.2] as [number, number, number], color: "#b9a6ff", label: "signal" },
];

function DocumentCard() {
  const group = useRef<THREE.Group>(null);

  useFrame((state) => {
    if (!group.current) return;
    group.current.rotation.y = Math.sin(state.clock.elapsedTime * 0.26) * 0.13;
    group.current.rotation.x = Math.sin(state.clock.elapsedTime * 0.2) * 0.04;
  });

  return (
    <group ref={group} rotation={[0.02, -0.2, -0.04]}>
      <mesh position={[0, 0, 0]}>
        <boxGeometry args={[2.35, 3.1, 0.08]} />
        <meshStandardMaterial color="#12283a" metalness={0.3} roughness={0.55} />
      </mesh>
      <mesh position={[0, 0, 0.06]}>
        <planeGeometry args={[2.08, 2.82]} />
        <meshBasicMaterial color="#e8eef5" />
      </mesh>
      {[-1.03, -0.68, -0.33, 0.02, 0.37, 0.72].map((y, index) => (
        <mesh key={y} position={[-0.28 + (index % 2) * 0.12, y, 0.08]}>
          <planeGeometry args={[1.22 - (index % 3) * 0.22, 0.055]} />
          <meshBasicMaterial color={index === 0 ? "#254158" : "#9ab0bd"} />
        </mesh>
      ))}
      <mesh position={[0.46, 0.72, 0.09]}>
        <planeGeometry args={[0.55, 0.27]} />
        <meshBasicMaterial color="#d9ff72" />
      </mesh>
    </group>
  );
}

function SignalNodes() {
  return (
    <>
      {nodes.map((node) => (
        <Float key={node.label} speed={1.1} rotationIntensity={0.12} floatIntensity={0.35}>
          <mesh position={node.position}>
            <sphereGeometry args={[0.105, 16, 16]} />
            <meshStandardMaterial color={node.color} emissive={node.color} emissiveIntensity={0.4} />
          </mesh>
        </Float>
      ))}
      <Line points={[nodes[0].position, [0, 0.2, 0.15], nodes[1].position]} color="#587786" transparent opacity={0.54} lineWidth={1} />
      <Line points={[nodes[1].position, [0.2, -0.3, 0.15], nodes[2].position]} color="#587786" transparent opacity={0.54} lineWidth={1} />
      <Line points={[nodes[2].position, [-0.2, -0.25, 0.15], nodes[3].position]} color="#587786" transparent opacity={0.54} lineWidth={1} />
      <Line points={[nodes[3].position, [-0.2, 0.25, 0.15], nodes[0].position]} color="#587786" transparent opacity={0.54} lineWidth={1} />
    </>
  );
}

export default function HeroScene() {
  return (
    <div className="hero-scene" aria-label="Interactive visualization of resume evidence flowing into analysis signals" role="img">
      <Canvas dpr={[1, 1.5]} gl={{ antialias: true, alpha: true }}>
        <PerspectiveCamera makeDefault position={[0, 0, 7.2]} fov={32} />
        <ambientLight intensity={1.1} />
        <pointLight position={[3, 3, 4]} intensity={18} color="#d9ff72" distance={8} />
        <pointLight position={[-4, -2, 2]} intensity={12} color="#7ee7da" distance={8} />
        <Sparkles count={34} scale={[5.5, 4.5, 2]} size={1.4} speed={0.22} color="#b9cdd3" />
        <Float speed={0.8} rotationIntensity={0.06} floatIntensity={0.35}>
          <DocumentCard />
        </Float>
        <SignalNodes />
        <OrbitControls enableZoom={false} enablePan={false} autoRotate autoRotateSpeed={0.25} maxPolarAngle={Math.PI / 1.8} minPolarAngle={Math.PI / 2.6} />
      </Canvas>
    </div>
  );
}
