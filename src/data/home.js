// Home page copy — verbatim from CLONE_SPEC.md §3 (and §2 for chrome copy).

export const BROCHURE_HREF = '/int/files/refire.pdf'

export const hero = {
  decor: '+ +',
  scroll: 'Scroll',
  subtitle: 'introducing',
  // Source string "<strong>A New</strong> generation" split on </strong>;
  // the arrow follows the first chunk.
  titleLines: ['A New', 'generation'],
  centerText: 'of fuel cell systems',
  link: { label: 'view our brochure', href: BROCHURE_HREF },
  video: { src: '/int/videos/main-new.mp4', poster: '/int/images/poster.png' },
}

export const saveTheDate = {
  number: '01',
  title: 'Save the date',
  subtitle: 'Refire Group',
  description:
    'We are excited to be part of Hannover Messe’s Hydrogen & Fuel Cell Expo. We look forward to meeting you there. Stay tuned for updates and plan your visit.',
}

export const aboutRefire = {
  title: '(About Refire)',
  description:
    'REFIRE is an international hydrogen energy technology company specializing in R&D, design, prototyping, testing, application engineering, and manufacturing of fuel cell systems for mobility and power products, superchargers, and grid support products.',
}

export const keyStats = [
  { label: 'key stat', number: 1, title: 'vehicles deployed', value: '4K+' },
  { label: 'key stat', number: 2, title: 'Tonnes Of CO2 Saved', value: '83K+' },
  { label: 'key stat', number: 3, title: 'Systems Delivered', value: '4K+' },
]

export const scrolledPicture = { src: '/int/images/prisma-1.jpg', alt: '' }

export const ticker = { text: 'Visit Us — ', repeat: 3 }

export const hannover = {
  title: 'Hannover Messe',
  contentTitle: 'BOOTH C45 | HALL 13 17-21 April 2023',
  contentSubtitle: 'HANNOVER MESSE Exhibition Grounds, Hannover, Germany',
  contentText:
    'REFIRE was founded in 2015 when a passionate group of engineers came together with the shared dream of propelling the development of hydrogen energy and popularizing the application of fuel cells. REFIRE hopes to reduce mankind’s dependence on fossil energy and contribute to the harmonious coexistence among all lives on our planet by making use of “hydrogen”, the most abundant element in the universe.',
  accordion: [
    {
      title: '17 April, PM',
      body: 'Panel Discussion - Heavy Duty Trucks: is Hydrogen the Future? @Public Forum, 14:00 (STAND D25 | HALL13)',
    },
    { title: '18 April, AM', body: 'GreenGT x REFIRE - product presentation@REFIRE booth' },
    {
      title: '18 April, PM',
      body: 'PRISMA XXII technical unveiling@Technical Stage, 15:00 (STAND B51 | HALL 13)',
    },
    { title: '19 April, PM', body: 'FC Development: Holistic by Design - presentation @REFIRE booth' },
    { title: '20 April, PM', body: 'APAS x REFIRE - product presentation@REFIRE booth' },
  ],
  contacts: [
    { label: 'Media liaison: ', email: 'media@refire.com' },
    { label: 'General enquiries: ', email: 'info@refire.com' },
  ],
}

export const textImage = {
  title: 'REFIRE is actively expanding its footprint domestic and internationally',
  text: 'In regions where policy is driving industry strategy and where commercialization can take place with fewer obstacles. We would like to help your region develop optimized policy choices, drive strategy, and build market opportunities for the benefit of the planet.',
  links: [{ label: 'view our brochure', href: BROCHURE_HREF }],
  image: '/int/images/prisma-2.jpg',
}
