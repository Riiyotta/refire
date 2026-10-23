import { useEffect, useRef } from 'react'
import * as THREE from 'three'

// Shader source verbatim from CLONE_SPEC.md §3.8.
const vertexShader = `
uniform float time;
varying vec2 vUv;
varying vec3 vPosition;
uniform vec2 pixels;
float PI = 3.141592653589793238;
void main() {
	vUv = uv;
	gl_Position = (projectionMatrix * modelViewMatrix) * vec4(position, 1.0);
}
`
const fragmentShader = `
uniform float time;
uniform float progress;
uniform sampler2D uDataTexture;
uniform sampler2D uTexture;
uniform vec4 resolution;
varying vec2 vUv;
varying vec3 vPosition;
float PI = 3.141592653589793238;
float getBounds(vec2 uv) {
	return ((step(0., uv.x) * step(0., uv.y)) * (1. - step(1., uv.x))) * (1. - step(1., uv.y));
}
void main() {
	vec2 newUV = ((vUv - vec2(0.5)) / resolution.zw) + vec2(0.5);
	vec2 uvs = newUV;
	vec2 uvs2 = newUV;
	float cProgress = 1. - progress;
	uvs -= 0.5;
	uvs /= (1. + (0.2 * progress));
	uvs += 0.5;
	uvs2.y += (1. * cProgress);
	uvs.y += (0.3 * cProgress);
	float bounds1 = getBounds(uvs2);
	vec4 offset = texture2D(uDataTexture, vUv);
	gl_FragColor = texture2D(uTexture, uvs - (0.02 * offset.rg)) * bounds1;
}
`

const GRID = 20 // 20x20 RGBA float DataTexture
const RELAXATION = 0.9
const MOUSE_RADIUS = 0.15 // × GRID
const STRENGTH = 100 * 0.7

/**
 * three.js image with progress reveal + mouse-velocity distortion (spec §3.8).
 *
 * Rendered in its final state (progress = 1). The Animation pass drives the
 * entrance (progress 0 → 1, 1s circ.out, at threshold .7) through the API:
 *   - `onReady(api)` prop, and
 *   - `element.shaderApi` on the root (found via [data-anim="shader-reveal"])
 * api = { uniforms, setProgress(p), render() }
 *
 * Props: src, alt, className
 */
export default function ShaderPicture({ src, alt = '', className = '', onReady }) {
  const rootRef = useRef(null)

  useEffect(() => {
    const root = rootRef.current

    const renderer = new THREE.WebGLRenderer()
    renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2))
    // clearColor token lives in tailwind.config.cjs, exposed as --webgl-clear
    const clear = getComputedStyle(document.documentElement).getPropertyValue('--webgl-clear').trim()
    renderer.setClearColor(new THREE.Color(clear), 1)
    renderer.outputEncoding = THREE.sRGBEncoding
    renderer.domElement.className = 'absolute left-0 top-0 z-2 h-full w-full'
    root.appendChild(renderer.domElement)

    const scene = new THREE.Scene()
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 1, 1000)
    camera.position.z = 2

    const data = new Float32Array(4 * GRID * GRID)
    const dataTexture = new THREE.DataTexture(data, GRID, GRID, THREE.RGBAFormat, THREE.FloatType)
    dataTexture.magFilter = dataTexture.minFilter = THREE.NearestFilter
    dataTexture.needsUpdate = true

    // Detached image for the texture: three r150 sizes texStorage from
    // image.width/height, which for an in-DOM <img> is its CSS layout size.
    const texImg = new Image()
    texImg.crossOrigin = 'anonymous'
    const texture = new THREE.Texture(texImg)
    const uniforms = {
      time: { value: 0 },
      progress: { value: 1 },
      uTexture: { value: texture },
      uDataTexture: { value: dataTexture },
      resolution: { value: new THREE.Vector4() },
    }
    const material = new THREE.ShaderMaterial({ uniforms, vertexShader, fragmentShader })
    let geometry = new THREE.PlaneGeometry(1, 1, 1, 1)
    const mesh = new THREE.Mesh(geometry, material)
    scene.add(mesh)

    let W = 0
    let H = 0
    const resize = () => {
      W = root.clientWidth
      H = root.clientHeight
      if (!W || !H) return
      renderer.setSize(W, H, false)
      camera.left = -W / 2
      camera.right = W / 2
      camera.top = H / 2
      camera.bottom = -H / 2
      camera.updateProjectionMatrix()
      geometry.dispose()
      geometry = new THREE.PlaneGeometry(W, H, 1, 1)
      mesh.geometry = geometry
      // Cover math (spec §3.8)
      const iw = texImg.naturalWidth
      const ih = texImg.naturalHeight
      if (iw && ih) {
        const scale = Math.max(W / iw, H / ih)
        uniforms.resolution.value.set(W, H, (iw * scale) / W, (ih * scale) / H)
      }
      render()
    }

    const render = () => {
      if (W && H && texImg.naturalWidth) renderer.render(scene, camera)
    }

    // Mouse distortion (spec §3.8)
    const mouse = { x: 0, y: 0, prevX: 0, prevY: 0, vX: 0, vY: 0 }
    const onMove = (e) => {
      const r = root.getBoundingClientRect()
      mouse.x = (e.clientX - r.left) / r.width
      mouse.y = (e.clientY - r.top) / r.height
      mouse.vX = mouse.x - mouse.prevX
      mouse.vY = mouse.y - mouse.prevY
      mouse.prevX = mouse.x
      mouse.prevY = mouse.y
    }
    const updateData = () => {
      for (let i = 0; i < data.length; i += 4) {
        data[i] *= RELAXATION
        data[i + 1] *= RELAXATION
      }
      const gx = GRID * mouse.x
      const gy = GRID * (1 - mouse.y)
      const maxDist = GRID * MOUSE_RADIUS
      for (let i = 0; i < GRID; i++) {
        for (let j = 0; j < GRID; j++) {
          const dist = Math.hypot(gx - i, gy - j)
          if (dist < maxDist) {
            const index = 4 * (i + GRID * j)
            const power = Math.min(Math.max(maxDist / dist, 0), 10)
            data[index] += STRENGTH * mouse.vX * power
            data[index + 1] -= STRENGTH * mouse.vY * power
          }
        }
      }
      mouse.vX *= RELAXATION
      mouse.vY *= RELAXATION
      dataTexture.needsUpdate = true
    }

    let raf = 0
    const loop = () => {
      updateData()
      render()
      raf = requestAnimationFrame(loop)
    }
    // Render loop runs only while the picture is in view (spec §3.8 / §4.1).
    const io = new IntersectionObserver(([entry]) => {
      cancelAnimationFrame(raf)
      if (entry.isIntersecting) raf = requestAnimationFrame(loop)
    })
    io.observe(root)

    const onLoad = () => {
      texture.needsUpdate = true
      resize()
    }
    texImg.addEventListener('load', onLoad)
    texImg.src = src

    const ro = new ResizeObserver(resize)
    ro.observe(root)
    root.addEventListener('mousemove', onMove)

    const api = {
      uniforms,
      setProgress: (p) => {
        uniforms.progress.value = p
        render()
      },
      render,
    }
    root.shaderApi = api
    onReady?.(api)

    return () => {
      cancelAnimationFrame(raf)
      io.disconnect()
      ro.disconnect()
      texImg.removeEventListener('load', onLoad)
      root.removeEventListener('mousemove', onMove)
      delete root.shaderApi
      geometry.dispose()
      material.dispose()
      texture.dispose()
      dataTexture.dispose()
      renderer.dispose()
      renderer.domElement.remove()
    }
  }, [src, onReady])

  return (
    <div ref={rootRef} className={`relative h-full w-full ${className}`} data-anim="shader-reveal" data-anim-threshold="0.7">
      <div className="invisible relative h-full w-full opacity-0">
        <img
          src={src}
          alt={alt}
          crossOrigin="anonymous"
          className="absolute left-0 top-0 h-full w-full object-cover"
        />
      </div>
    </div>
  )
}
