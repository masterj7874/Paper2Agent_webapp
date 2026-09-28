// WebGL background: a slowly drifting particle nebula + a wireframe "cell" torus knot that reacts to the pointer.
import { useEffect, useRef } from 'react'
import * as THREE from 'three'

export default function Starfield({ accent = '#22d3ee', intensity = 1 }) {
  const ref = useRef(null)
  const accentRef = useRef(accent)
  useEffect(() => { accentRef.current = accent }, [accent])

  useEffect(() => {
    const el = ref.current
    const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, powerPreference: 'high-performance' })
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    renderer.setSize(el.clientWidth, el.clientHeight)
    el.appendChild(renderer.domElement)
    const scene = new THREE.Scene()
    scene.fog = new THREE.FogExp2(0x05070f, 0.035)
    const camera = new THREE.PerspectiveCamera(60, el.clientWidth / el.clientHeight, 0.1, 200)
    camera.position.set(0, 0, 18)

    // particles
    const N = 2600
    const pos = new Float32Array(N * 3), col = new Float32Array(N * 3), seed = new Float32Array(N)
    const c1 = new THREE.Color('#22d3ee'), c2 = new THREE.Color('#a78bfa'), c3 = new THREE.Color('#34d399')
    for (let i = 0; i < N; i++) {
      const r = 6 + Math.random() * 34, th = Math.random() * Math.PI * 2, ph = Math.acos(2 * Math.random() - 1)
      pos[i * 3] = r * Math.sin(ph) * Math.cos(th); pos[i * 3 + 1] = (r * Math.sin(ph) * Math.sin(th)) * 0.55; pos[i * 3 + 2] = r * Math.cos(ph) - 10
      const c = [c1, c2, c3][i % 3].clone().lerp(new THREE.Color('#ffffff'), Math.random() * 0.5)
      col[i * 3] = c.r; col[i * 3 + 1] = c.g; col[i * 3 + 2] = c.b; seed[i] = Math.random() * Math.PI * 2
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    geo.setAttribute('color', new THREE.BufferAttribute(col, 3))
    geo.setAttribute('seed', new THREE.BufferAttribute(seed, 1))
    const mat = new THREE.ShaderMaterial({
      transparent: true, depthWrite: false, blending: THREE.AdditiveBlending, vertexColors: true,
      uniforms: { uTime: { value: 0 }, uPixelRatio: { value: renderer.getPixelRatio() } },
      vertexShader: `attribute float seed; varying vec3 vColor; uniform float uTime; uniform float uPixelRatio;
        void main(){ vColor = color; vec3 p = position; p.y += sin(uTime*0.4 + seed)*0.6; p.x += cos(uTime*0.25 + seed*1.7)*0.4;
        vec4 mv = modelViewMatrix * vec4(p,1.0); gl_Position = projectionMatrix * mv;
        gl_PointSize = (2.2 + 1.8*sin(uTime*1.3+seed)) * uPixelRatio * (24.0 / -mv.z); }`,
      fragmentShader: `varying vec3 vColor; void main(){ float d = length(gl_PointCoord - 0.5); if(d>0.5) discard;
        float a = smoothstep(0.5, 0.05, d); gl_FragColor = vec4(vColor, a*0.9); }`,
    })
    const points = new THREE.Points(geo, mat); scene.add(points)

    // hero object: glowing wireframe knot ("a cell in flow space")
    const knotGeo = new THREE.TorusKnotGeometry(3.2, 0.9, 220, 28, 2, 3)
    const knotMat = new THREE.MeshBasicMaterial({ color: new THREE.Color(accent), wireframe: true, transparent: true, opacity: 0.16 })
    const knot = new THREE.Mesh(knotGeo, knotMat); knot.position.set(9, 1.5, -4); scene.add(knot)
    const ringGeo = new THREE.RingGeometry(5.2, 5.35, 128)
    const ring = new THREE.Mesh(ringGeo, new THREE.MeshBasicMaterial({ color: new THREE.Color(accent), transparent: true, opacity: 0.25, side: THREE.DoubleSide }))
    ring.position.copy(knot.position); scene.add(ring)

    const mouse = { x: 0, y: 0 }
    const onMove = (e) => { mouse.x = (e.clientX / window.innerWidth) * 2 - 1; mouse.y = -(e.clientY / window.innerHeight) * 2 + 1 }
    window.addEventListener('pointermove', onMove)
    const onResize = () => { camera.aspect = el.clientWidth / el.clientHeight; camera.updateProjectionMatrix(); renderer.setSize(el.clientWidth, el.clientHeight) }
    window.addEventListener('resize', onResize)

    let raf, t0 = performance.now()
    const tick = () => {
      const t = (performance.now() - t0) / 1000
      mat.uniforms.uTime.value = t
      points.rotation.y = t * 0.02; points.rotation.x = Math.sin(t * 0.05) * 0.05
      knot.rotation.x = t * 0.18; knot.rotation.y = t * 0.12
      ring.rotation.z = -t * 0.1; ring.rotation.x = Math.PI / 2 + Math.sin(t * 0.3) * 0.4
      const target = new THREE.Color(accentRef.current)
      knotMat.color.lerp(target, 0.03); ring.material.color.lerp(target, 0.03)
      camera.position.x += (mouse.x * 1.2 - camera.position.x) * 0.03
      camera.position.y += (mouse.y * 0.8 - camera.position.y) * 0.03
      camera.lookAt(0, 0, -6)
      renderer.render(scene, camera)
      raf = requestAnimationFrame(tick)
    }
    tick()
    return () => { cancelAnimationFrame(raf); window.removeEventListener('pointermove', onMove); window.removeEventListener('resize', onResize); renderer.dispose(); geo.dispose(); mat.dispose(); knotGeo.dispose(); knotMat.dispose(); ringGeo.dispose(); el.removeChild(renderer.domElement) }
  }, [])

  return <div ref={ref} className="starfield" style={{ opacity: intensity }} />
}
