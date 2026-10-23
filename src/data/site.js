// Site-wide chrome copy — verbatim from CLONE_SPEC.md §2 and §3.9.

export const preloader = {
  decorLeft: '++',
  decorRight: ['1.00784', '1.00811'],
  initializing: 'initializing',
  tagline: 'Creating a Sustainable Future',
}

export const header = { contact: 'Contact', close: 'Close' }

export const cookie = { title: 'We use cookies to make things better', close: 'Close' }

export const contact = {
  // Live site uses this placeholder mailto (spec §2.6 / §8.7).
  titleHref: 'mailto:test@test.en',
  titleLines: ['contact', 'us today'],
  formTitle: 'Contact form',
  formText: 'Send us a message and we’ll get back to you as soon as possible.',
  lists: [
    { title: 'Phone us', lines: [
        // { prefix, text, href } renders "prefix <a href>text</a>" (source markup: tel links)
        { prefix: 'Germany', text: '+1 790 790 9238', href: 'tel:+17907909238' },
        { prefix: 'France', text: '+1 893 233 2030', href: 'tel:+18932332030' },
      ] },
    { title: 'Hours', lines: ['Monday - Friday 8:00AM - 8:00PM', 'Saturday & Sunday Closed'] },
  ],
  select: {
    placeholder: 'Select a department you’d like to reach*',
    options: ['Media', 'Sales', 'General'],
  },
  rows: [
    [
      { name: 'fname', placeholder: 'First Name*' },
      { name: 'lname', placeholder: 'Last Name*' },
    ],
    [
      { name: 'email', placeholder: 'Email*' },
      { name: 'subject', placeholder: 'Subject*' },
    ],
  ],
  message: { name: 'message', placeholder: 'Message*' },
  note: '*By submitting, the data provided will be used to perform your request according to the Privacy Policy',
  submit: 'submit',
}

export const footer = {
  brand: 'Refire',
  rights: ' all rights reserved',
  backToTop: 'Back to Top',
}
