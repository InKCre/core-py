# Mail Extension for InKCre

This extension provides IMAP email source functionality for InKCre.

## Features

- Collect emails from IMAP servers
- Support for SSL/TLS connections
- Email parsing and organization
- Automatic tracking of processed emails

## Configuration

The extension requires the following configuration:

- `imap_server`: IMAP server address (e.g., `imap.gmail.com`)
- `imap_port`: IMAP port (default: `993` for SSL)
- `use_ssl`: Whether to use SSL/TLS connection (default: `true`)
- `username`: Email account username
- `password`: Email account password or app-specific password

## Usage

1. Install the extension in the InKCre database
2. Configure IMAP settings
3. Create an IMAP source via the API endpoint: `POST /mail/imap`
4. Emails will be collected based on the configured schedule

## Notes

- For Gmail, you may need to use an app-specific password
- The extension tracks the last processed email UID to avoid duplicates
- Emails are stored as blocks with their content and metadata
