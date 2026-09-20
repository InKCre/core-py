import { extensionDocs } from '../../../../../docs/_shared/website/extension-docs/preset.mts'

export default extensionDocs({
  name: 'inkcre/memos', title: 'Memos Core Extension', scope: 'python',
  description: 'Operate the Memos-compatible backend on Core.',
  sidebar: [{ text: 'Core Configuration', link: '/' }],
})
