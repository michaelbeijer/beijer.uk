# michaelbeijer.co.uk Admin Panel

A custom Flask-based CMS for managing the michaelbeijer.co.uk website content.

## Features

- **Blog Posts**: Create, edit, and delete blog posts with rich text editing
- **Static Pages**: Manage services, patents, work, tools, about, contact, testimonials pages
- **Homepage**: Edit homepage content (title, tagline, intro, additional content)
- **Navigation**: Add, remove, rename, and reorder site nav tabs with drag-and-drop
- **Rich Text Editor**: Jodit Editor with drag-to-resize image handles
- **Image Upload**: Direct upload to content directory
- **GitHub Integration**: Commit changes directly to GitHub from the admin panel

## Architecture

### Content Structure

```
src/content/
├── blog/           # Blog posts (markdown with HTML body)
│   ├── images/     # Blog post images
│   └── *.md
├── pages/          # Static page content
│   └── *.md
├── home/           # Homepage content
│   └── index.md
└── nav/            # Navigation configuration
    └── nav.json    # Ordered list of {label, href} nav items
```

### Admin Panel Structure

```
admin/
├── app.py              # Main Flask application
├── requirements.txt    # Python dependencies
├── Procfile           # Railway deployment
├── railway.json       # Railway configuration
├── start_dev.py       # Local development launcher
├── templates/
│   ├── base.html           # Base template with navigation
│   ├── login.html          # GitHub OAuth login page
│   ├── index.html          # Dashboard
│   ├── posts.html          # Blog posts list
│   ├── post_editor.html    # Blog post editor (Jodit)
│   ├── pages.html          # Static pages list
│   ├── page_editor.html    # Page editor (Jodit)
│   ├── home_editor.html    # Homepage editor (Jodit)
│   └── nav.html            # Navigation management (drag-and-drop)
└── static/
    └── css/
        └── admin.css       # Admin panel styles
```

## Local Development

### Prerequisites

- Python 3.9+
- pip

### Setup

```bash
cd admin
pip install -r requirements.txt
python start_dev.py
```

This starts the admin panel at http://localhost:5000 in development mode (no GitHub OAuth required).

### Development Mode

When `ADMIN_DEV_MODE=true` (set by start_dev.py), authentication is bypassed for local testing.

## Production Deployment (Railway)

### Environment Variables

| Variable | Description |
|----------|-------------|
| `FLASK_SECRET_KEY` | Random secret key for sessions |
| `GITHUB_CLIENT_ID` | GitHub OAuth App client ID |
| `GITHUB_CLIENT_SECRET` | GitHub OAuth App client secret |
| `GITHUB_REPO` | Repository name (e.g., `michaelbeijer/michaelbeijer.co.uk`) |
| `ALLOWED_GITHUB_USERS` | Comma-separated list of allowed GitHub usernames |
| `CALLBACK_URL` | OAuth callback URL (e.g., `https://your-app.railway.app/auth/github/callback`) |
| `PRODUCTION` | Set to `true` for production mode |

### GitHub OAuth App Setup

1. Go to GitHub → Settings → Developer settings → OAuth Apps
2. Create new OAuth App:
   - **Application name**: michaelbeijer.co.uk Admin
   - **Homepage URL**: https://michaelbeijer.co.uk
   - **Callback URL**: https://your-railway-url/auth/github/callback
3. Copy Client ID and Client Secret to Railway environment variables

### Deploy to Railway

1. Push code to GitHub
2. Create new Railway project from GitHub repo
3. Set environment variables
4. Deploy

## Editor: Jodit

The admin panel uses [Jodit Editor](https://xdsoft.net/jodit/) (MIT licensed) for rich text editing.

### Key Features

- Drag-to-resize image handles (corner and edge handles)
- Aspect ratio maintained by default
- Image upload integration
- Full HTML output (stored directly in markdown files)
- No premium features required

### Configuration

```javascript
const editor = Jodit.make('#editor', {
    height: 500,
    toolbarButtonSize: 'middle',
    buttons: [
        'bold', 'italic', 'underline', '|',
        'ul', 'ol', '|',
        'outdent', 'indent', '|',
        'font', 'fontsize', '|',
        'image', 'link', 'table', '|',
        'align', '|',
        'undo', 'redo', '|',
        'hr', 'eraser', 'fullsize'
    ],
    uploader: {
        url: '/api/upload',
        // ... upload configuration
    },
    imageDefaultWidth: 400,
    resizer: {
        showSize: true,
        useAspectRatio: true
    }
});
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/posts` | POST | Create new blog post |
| `/api/posts/<slug>` | POST | Update blog post |
| `/api/posts/<slug>` | DELETE | Delete blog post |
| `/api/pages` | POST | Create new page |
| `/api/pages/<slug>` | POST | Update page |
| `/api/pages/<slug>` | DELETE | Delete page |
| `/api/home` | POST | Update homepage content |
| `/api/nav` | GET | Get current nav items |
| `/api/nav` | POST | Save full nav list (reorder + rename) |
| `/api/nav/add` | POST | Add nav tab (creates `.astro` + `.md` files) |
| `/api/nav/<slug>` | DELETE | Remove nav tab (deletes `.astro` + `.md` files) |
| `/api/upload` | POST | Upload image |
| `/api/git/commit` | POST | Commit file to GitHub |

## Content Format

### Blog Post (markdown)

```markdown
---
title: "Post Title"
description: "Post description for SEO"
pubDate: "2024-01-15"
heroImage: "./images/hero.jpg"
---

<p>HTML content from Jodit editor...</p>
```

### Static Page (markdown)

```markdown
---
title: "Page Title"
description: "Page description for SEO"
---

<p>HTML content from Jodit editor...</p>
```

### Homepage (markdown)

```markdown
---
title: "Michael Beijer"
tagline: "Technical translator and terminology specialist"
intro: "Introduction paragraph..."
---

<p>Additional HTML content...</p>
```

## Image Handling

### Upload Process

1. User drags/selects image in Jodit editor
2. Image uploaded to `/api/upload`
3. Saved to `src/content/blog/images/` with unique filename
4. URL returned to editor for insertion

### Resize Behavior

- Images can be resized by dragging corner handles
- Aspect ratio maintained by default
- Size stored as inline `style` attribute (e.g., `style="width: 400px;"`)
- Images remain sharp as only display size changes, not actual file

## Workflow

1. **Edit content** in admin panel (http://localhost:5000 or Railway URL)
2. **Save** to local files (development) or via GitHub API (production)
3. **Commit to GitHub** using "Save & Commit to GitHub" button
4. **Automatic rebuild** via GitHub Actions / Netlify / Vercel
5. **Live site updated** with new content

## Dependencies

```
Flask==3.0.0
gunicorn==21.2.0
PyGithub==2.1.1
requests==2.31.0
PyYAML==6.0.1
Werkzeug==3.0.1
markdown==3.5.1
```

## Troubleshooting

### Editor shows read-only content
- Check browser console for JavaScript errors
- Ensure Jodit CSS and JS are loading from CDN

### Images not displaying
- Check image path (should be relative like `./images/filename.jpg`)
- Verify image exists in `src/content/blog/images/`

### GitHub commit fails
- Verify GitHub OAuth token has repo write access
- Check `GITHUB_REPO` environment variable format
- Ensure user is in `ALLOWED_GITHUB_USERS` list

### Lists not formatting correctly
- Content uses HTML (not markdown) for formatting
- Check CSS includes proper list styles
