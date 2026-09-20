import { extensionDocs } from '../../../../../docs/_shared/website/extension-docs/preset.mts'

export default extensionDocs({
  name: 'inkcre/memos', title: 'Memos for InKCre', scope: 'global',
  description: 'Capture notes in InKCre with a Memos-compatible app.',
  sidebar: [{ text: 'Overview', link: '/' }, { text: 'Connect Your App', link: '/connect' }],
})
