// Shared GSAP instance with the plugins/eases the original registers
// (_app bundle: CustomEase.create("easeFormHoverLine", ...), ("easeDecorLine", ...)).
import gsap from 'gsap'
import { CustomEase } from 'gsap/CustomEase'
import { DrawSVGPlugin } from 'gsap/DrawSVGPlugin'

gsap.registerPlugin(CustomEase, DrawSVGPlugin)
CustomEase.create('easeFormHoverLine', '0.215, 0.61, 0.355, 1')
CustomEase.create('easeDecorLine', '0.075, 0.82, 0.165, 1')

export default gsap
