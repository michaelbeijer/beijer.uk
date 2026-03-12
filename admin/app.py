"""
michaelbeijer.co.uk Admin Panel
Custom CMS for managing blog posts, pages, and homepage content
Uses Jodit Editor for rich text editing with image drag-resize handles
"""
import os
import sys
import re
import json
import base64
import yaml
import markdown
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, send_from_directory, Response
import requests
from github import Github, GithubException
from werkzeug.utils import secure_filename

# Markdown to HTML converter (extra includes tables, fenced_code, etc.)
md = markdown.Markdown(extensions=['extra', 'sane_lists'])

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Development/Production mode
ADMIN_DEV_MODE = os.environ.get('ADMIN_DEV_MODE', '').lower() == 'true'
PRODUCTION_MODE = os.environ.get('PRODUCTION', '').lower() == 'true'
IS_DEV = ADMIN_DEV_MODE and not PRODUCTION_MODE

# GitHub OAuth configuration
GITHUB_CLIENT_ID = os.environ.get('GITHUB_CLIENT_ID', '')
GITHUB_CLIENT_SECRET = os.environ.get('GITHUB_CLIENT_SECRET', '')
GITHUB_REPO_OWNER = 'michaelbeijer'
GITHUB_REPO_NAME = 'michaelbeijer.co.uk'
ALLOWED_USERS = os.environ.get('ALLOWED_GITHUB_USERS', 'michaelbeijer').split(',')
CALLBACK_URL = os.environ.get('CALLBACK_URL', 'http://localhost:5000/auth/github/callback')

# Content paths
APP_DIR = Path(__file__).parent.resolve()
DEFAULT_BASE_DIR = APP_DIR.parent if (APP_DIR.parent / 'src' / 'content').exists() else APP_DIR
BASE_DIR = Path(os.environ.get('BASE_DIR', str(DEFAULT_BASE_DIR))).resolve()
CONTENT_DIR = BASE_DIR / 'src' / 'content'
BLOG_DIR = CONTENT_DIR / 'blog'
PAGES_DIR = CONTENT_DIR / 'pages'
HOME_DIR = CONTENT_DIR / 'home'
IMAGES_DIR = BLOG_DIR / 'images'
NAV_DIR = CONTENT_DIR / 'nav'
NAV_FILE = NAV_DIR / 'nav.json'
BLOG_PAGE_DIR = CONTENT_DIR / 'blog-page'
SETTINGS_DIR = CONTENT_DIR / 'settings'
APPEARANCE_FILE = SETTINGS_DIR / 'appearance.json'
PAGES_ASTRO_DIR = BASE_DIR / 'src' / 'pages'
USE_GITHUB_CONTENT = (
    os.environ.get('USE_GITHUB_CONTENT', '').lower() == 'true' or
    (PRODUCTION_MODE and not (HOME_DIR / 'index.md').exists())
)

# Ensure directories exist
if not USE_GITHUB_CONTENT:
    IMAGES_DIR.mkdir(parents=True, exist_ok=True)


def get_github_token() -> Optional[str]:
    """Get GitHub token from session"""
    return session.get('github_token')


def require_auth(f):
    """Decorator to require GitHub authentication"""
    def wrapper(*args, **kwargs):
        # Bypass auth in development mode
        if IS_DEV:
            return f(*args, **kwargs)

        # Production: require GitHub OAuth
        if 'github_token' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    wrapper.__name__ = f.__name__
    return wrapper


def get_github_repo():
    """Get authenticated GitHub repo object from session token."""
    github_token = get_github_token()
    if not github_token:
        return None, "GitHub authentication required"

    try:
        g = Github(github_token)
        repo = g.get_repo(f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")
        return repo, None
    except GithubException as e:
        return None, f"GitHub API error: {e.data.get('message', str(e))}"
    except Exception as e:
        return None, f"Error: {str(e)}"


def gh_list_markdown(dir_path: str, reverse: bool = False):
    """List markdown files in a GitHub directory and return decoded content."""
    repo, error = get_github_repo()
    if error:
        return None, error

    try:
        contents = repo.get_contents(dir_path, ref="main")
        if not isinstance(contents, list):
            contents = [contents]

        md_files = [c for c in contents if c.type == 'file' and c.name.endswith('.md')]
        md_files.sort(key=lambda x: x.name, reverse=reverse)

        items = []
        for item in md_files:
            items.append({
                'name': item.name,
                'path': item.path,
                'sha': item.sha,
                'content': item.decoded_content.decode('utf-8')
            })
        return items, None
    except GithubException as e:
        if e.status == 404:
            return [], None
        return None, f"GitHub API error: {e.data.get('message', str(e))}"
    except Exception as e:
        return None, f"Error: {str(e)}"


def gh_read_text(path: str):
    """Read a UTF-8 text file from GitHub."""
    repo, error = get_github_repo()
    if error:
        return None, None, error

    try:
        file_obj = repo.get_contents(path, ref="main")
        return file_obj.decoded_content.decode('utf-8'), file_obj.sha, None
    except GithubException as e:
        if e.status == 404:
            return None, None, 'not_found'
        return None, None, f"GitHub API error: {e.data.get('message', str(e))}"
    except Exception as e:
        return None, None, f"Error: {str(e)}"


def gh_upsert_text(path: str, content: str, commit_message: str):
    """Create or update a UTF-8 text file in GitHub."""
    repo, error = get_github_repo()
    if error:
        return False, error

    try:
        try:
            existing = repo.get_contents(path, ref="main")
            repo.update_file(
                path=path,
                message=commit_message,
                content=content,
                sha=existing.sha,
                branch="main"
            )
            return True, f"Updated {path} on GitHub"
        except GithubException as e:
            if e.status != 404:
                raise
            repo.create_file(
                path=path,
                message=commit_message,
                content=content,
                branch="main"
            )
            return True, f"Created {path} on GitHub"
    except GithubException as e:
        return False, f"GitHub API error: {e.data.get('message', str(e))}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def gh_delete_path(path: str, commit_message: str):
    """Delete a file from GitHub."""
    repo, error = get_github_repo()
    if error:
        return False, error

    try:
        file_obj = repo.get_contents(path, ref="main")
        repo.delete_file(
            path=path,
            message=commit_message,
            sha=file_obj.sha,
            branch="main"
        )
        return True, f"Deleted {path} from GitHub"
    except GithubException as e:
        if e.status == 404:
            return False, "not_found"
        return False, f"GitHub API error: {e.data.get('message', str(e))}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def git_commit_and_push(file_path: str, commit_message: str) -> Tuple[bool, str]:
    """Add, commit, and push a file to GitHub using GitHub API"""
    github_token = get_github_token()

    # In dev mode without token, just save locally
    if IS_DEV and not github_token:
        return True, "Saved locally (dev mode - no GitHub commit)"

    if not github_token:
        return False, "GitHub authentication required"

    try:
        g = Github(github_token)
        repo = g.get_repo(f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")

        # Make file_path relative to BASE_DIR
        try:
            rel_path = Path(file_path).relative_to(BASE_DIR)
        except ValueError:
            return False, "File path is not within repository"

        # Convert Windows path separators to forward slashes for GitHub
        github_path = str(rel_path).replace('\\', '/')

        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Try to get the existing file to update it
        try:
            file_contents = repo.get_contents(github_path, ref="main")
            repo.update_file(
                path=github_path,
                message=commit_message,
                content=content,
                sha=file_contents.sha,
                branch="main"
            )
            return True, f"Successfully updated {github_path} on GitHub!"
        except GithubException as e:
            if e.status == 404:
                repo.create_file(
                    path=github_path,
                    message=commit_message,
                    content=content,
                    branch="main"
                )
                return True, f"Successfully created {github_path} on GitHub!"
            else:
                raise

    except GithubException as e:
        return False, f"GitHub API error: {e.data.get('message', str(e))}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def git_delete_file(file_path: str, commit_message: str) -> Tuple[bool, str]:
    """Delete a file from GitHub using GitHub API"""
    github_token = get_github_token()

    if IS_DEV and not github_token:
        return True, "Deleted locally (dev mode - no GitHub commit)"

    if not github_token:
        return False, "GitHub authentication required"

    try:
        g = Github(github_token)
        repo = g.get_repo(f"{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}")

        try:
            rel_path = Path(file_path).relative_to(BASE_DIR)
        except ValueError:
            return False, "File path is not within repository"

        github_path = str(rel_path).replace('\\', '/')

        try:
            file_contents = repo.get_contents(github_path, ref="main")
            repo.delete_file(
                path=github_path,
                message=commit_message,
                sha=file_contents.sha,
                branch="main"
            )
            return True, f"Successfully deleted {github_path} from GitHub!"
        except GithubException as e:
            if e.status == 404:
                return True, "File not found on GitHub (already deleted)"
            else:
                raise

    except GithubException as e:
        return False, f"GitHub API error: {e.data.get('message', str(e))}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def parse_frontmatter(content: str) -> Tuple[Dict, str]:
    """Parse YAML frontmatter and body from markdown content"""
    if not content.startswith('---'):
        return {}, content

    parts = content.split('---', 2)
    if len(parts) < 3:
        return {}, content

    try:
        frontmatter = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError:
        frontmatter = {}

    body = parts[2].strip()
    return frontmatter, body


def generate_markdown(frontmatter: Dict, body: str) -> str:
    """Generate markdown file from frontmatter and body"""
    fm_str = yaml.dump(frontmatter, allow_unicode=True, sort_keys=False, default_flow_style=False)
    return f"---\n{fm_str}---\n\n{body}\n"


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug"""
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '_', text)
    return text.strip('_')


def markdown_to_html(text: str) -> str:
    """Convert markdown to HTML for CKEditor"""
    md.reset()
    return md.convert(text)


# =============================================================================
# Routes
# =============================================================================

@app.route('/health')
def health():
    """Unauthenticated health endpoint for Railway deploy checks."""
    return jsonify({'status': 'ok'}), 200


@app.route('/')
def index():
    """Admin dashboard"""
    # In production, show login page directly for anonymous users.
    # This keeps "/" healthy (HTTP 200) for platform health checks.
    if not IS_DEV and 'github_token' not in session:
        return render_template(
            'login.html',
            github_client_id=GITHUB_CLIENT_ID,
            callback_url=CALLBACK_URL,
            dev_mode=IS_DEV
        )

    posts = []
    page_count = 0

    if USE_GITHUB_CONTENT:
        blog_items, blog_err = gh_list_markdown('src/content/blog', reverse=True)
        page_items, page_err = gh_list_markdown('src/content/pages', reverse=False)

        if blog_err:
            return f'Error loading blog posts from GitHub: {blog_err}', 500
        if page_err:
            return f'Error loading pages from GitHub: {page_err}', 500

        for item in (blog_items or [])[:5]:
            fm, _ = parse_frontmatter(item['content'])
            posts.append({
                'slug': Path(item['name']).stem,
                'title': fm.get('title', Path(item['name']).stem),
                'pubDate': fm.get('pubDate', '')
            })
        post_count = len(blog_items or [])
        page_count = len(page_items or [])
    else:
        for file in sorted(BLOG_DIR.glob('*.md'), reverse=True)[:5]:
            with open(file, 'r', encoding='utf-8') as f:
                fm, _ = parse_frontmatter(f.read())
                posts.append({
                    'slug': file.stem,
                    'title': fm.get('title', file.stem),
                    'pubDate': fm.get('pubDate', '')
                })
        post_count = len(list(BLOG_DIR.glob('*.md')))
        page_count = len(list(PAGES_DIR.glob('*.md')))

    stats = {
        'posts': post_count,
        'pages': page_count,
    }

    return render_template('index.html', stats=stats, recent_posts=posts)


@app.route('/login')
def login():
    """GitHub OAuth login page"""
    if 'github_token' in session:
        return redirect(url_for('index'))

    return render_template('login.html',
                          github_client_id=GITHUB_CLIENT_ID,
                          callback_url=CALLBACK_URL,
                          dev_mode=IS_DEV)


@app.route('/auth/github/callback')
def github_callback():
    """Handle GitHub OAuth callback"""
    code = request.args.get('code')
    if not code:
        return 'Error: No authorization code received', 400

    token_url = 'https://github.com/login/oauth/access_token'
    response = requests.post(token_url, data={
        'client_id': GITHUB_CLIENT_ID,
        'client_secret': GITHUB_CLIENT_SECRET,
        'code': code,
        'redirect_uri': CALLBACK_URL
    }, headers={'Accept': 'application/json'})

    if response.status_code != 200:
        return f'Error getting access token: {response.text}', 400

    data = response.json()
    access_token = data.get('access_token')

    if not access_token:
        return 'Error: No access token in response', 400

    user_response = requests.get('https://api.github.com/user',
                                 headers={'Authorization': f'token {access_token}'})
    if user_response.status_code == 200:
        user_data = user_response.json()
        username = user_data.get('login')

        if username not in ALLOWED_USERS:
            return f'Error: User {username} is not authorized to access this admin panel', 403

        session['github_token'] = access_token
        session['github_user'] = username
    else:
        return 'Error: Could not get user info from GitHub', 400

    return redirect(url_for('index'))


@app.route('/auth/dev-login', methods=['POST'])
def dev_login():
    """Development mode login (bypass OAuth)"""
    if not IS_DEV:
        return 'Dev mode not enabled', 403

    session['github_token'] = 'dev-token'
    session['github_user'] = 'dev-user'
    return redirect(url_for('index'))


@app.route('/logout')
def logout():
    """Logout"""
    session.clear()
    return redirect(url_for('login'))


# =============================================================================
# Blog Posts
# =============================================================================

@app.route('/posts')
@require_auth
def posts():
    """List all blog posts"""
    posts_data = []

    if USE_GITHUB_CONTENT:
        items, error = gh_list_markdown('src/content/blog', reverse=True)
        if error:
            return f'Error loading posts: {error}', 500

        for item in items or []:
            fm, _ = parse_frontmatter(item['content'])
            slug = Path(item['name']).stem
            posts_data.append({
                'slug': slug,
                'title': fm.get('title', slug),
                'pubDate': fm.get('pubDate', ''),
                'description': fm.get('description', '')[:100] + '...' if fm.get('description', '') else '',
                'hidden': fm.get('hidden', False)
            })
    else:
        for file in sorted(BLOG_DIR.glob('*.md'), reverse=True):
            with open(file, 'r', encoding='utf-8') as f:
                fm, _ = parse_frontmatter(f.read())
                posts_data.append({
                    'slug': file.stem,
                    'title': fm.get('title', file.stem),
                    'pubDate': fm.get('pubDate', ''),
                    'description': fm.get('description', '')[:100] + '...' if fm.get('description', '') else '',
                    'hidden': fm.get('hidden', False)
                })

    return render_template('posts.html', posts=posts_data)


@app.route('/posts/new')
@require_auth
def new_post():
    """Create a new blog post"""
    return render_template('post_editor.html',
                          post=None,
                          is_new=True)


@app.route('/posts/<slug>')
@require_auth
def edit_post(slug):
    """Edit a blog post"""
    if USE_GITHUB_CONTENT:
        content, _, error = gh_read_text(f'src/content/blog/{slug}.md')
        if error == 'not_found':
            return 'Post not found', 404
        if error:
            return f'Error loading post: {error}', 500
    else:
        file_path = BLOG_DIR / f'{slug}.md'
        if not file_path.exists():
            return 'Post not found', 404

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    fm, body = parse_frontmatter(content)

    # Convert markdown to HTML for CKEditor
    body_html = markdown_to_html(body)
    # Rewrite image paths so they display in the admin editor
    body_html = body_html.replace('./images/', '/blog-images/')

    post = {
        'slug': slug,
        'title': fm.get('title', ''),
        'description': fm.get('description', ''),
        'pubDate': fm.get('pubDate', ''),
        'heroImage': fm.get('heroImage', ''),
        'hidden': fm.get('hidden', False),
        'body': body_html
    }

    return render_template('post_editor.html', post=post, is_new=False)


@app.route('/api/posts', methods=['POST'])
@require_auth
def api_create_post():
    """Create a new blog post"""
    data = request.json
    title = data.get('title', '').strip()

    if not title:
        return jsonify({'error': 'Title is required'}), 400

    slug = slugify(title)

    frontmatter = {
        'title': title,
        'description': data.get('description', ''),
        'pubDate': data.get('pubDate', datetime.now().strftime('%Y-%m-%d')),
    }

    if data.get('heroImage'):
        frontmatter['heroImage'] = data['heroImage']

    if data.get('hidden'):
        frontmatter['hidden'] = True

    # Convert editor image paths back to relative paths for markdown
    body = data.get('body', '').replace('/blog-images/', './images/')
    content = generate_markdown(frontmatter, body)

    if USE_GITHUB_CONTENT:
        existing, _, read_error = gh_read_text(f'src/content/blog/{slug}.md')
        if read_error is None and existing is not None:
            return jsonify({'error': 'A post with this title already exists'}), 400
        if read_error not in ('not_found', None):
            return jsonify({'error': read_error}), 500

        success, message = gh_upsert_text(
            f'src/content/blog/{slug}.md',
            content,
            f'Create blog post: {title}'
        )
        if not success:
            return jsonify({'error': message}), 500
    else:
        file_path = BLOG_DIR / f'{slug}.md'
        if file_path.exists():
            return jsonify({'error': 'A post with this title already exists'}), 400

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return jsonify({'success': True, 'slug': slug})


@app.route('/api/posts/<slug>', methods=['GET', 'POST', 'DELETE'])
@require_auth
def api_post(slug):
    """Get, update, or delete a blog post"""
    file_path = BLOG_DIR / f'{slug}.md'
    gh_path = f'src/content/blog/{slug}.md'

    if request.method == 'GET':
        if USE_GITHUB_CONTENT:
            content, _, error = gh_read_text(gh_path)
            if error == 'not_found':
                return jsonify({'error': 'Post not found'}), 404
            if error:
                return jsonify({'error': error}), 500
        else:
            if not file_path.exists():
                return jsonify({'error': 'Post not found'}), 404

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        fm, body = parse_frontmatter(content)
        return jsonify({
            'slug': slug,
            'title': fm.get('title', ''),
            'description': fm.get('description', ''),
            'pubDate': fm.get('pubDate', ''),
            'heroImage': fm.get('heroImage', ''),
            'hidden': fm.get('hidden', False),
            'body': body
        })

    elif request.method == 'POST':
        data = request.json

        frontmatter = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
            'pubDate': data.get('pubDate', ''),
        }

        if data.get('heroImage'):
            frontmatter['heroImage'] = data['heroImage']

        if data.get('hidden'):
            frontmatter['hidden'] = True

        # Convert editor image paths back to relative paths for markdown
        body = data.get('body', '').replace('/blog-images/', './images/')
        content = generate_markdown(frontmatter, body)

        if USE_GITHUB_CONTENT:
            success, message = gh_upsert_text(
                gh_path,
                content,
                f"Update blog post: {data.get('title', slug)}"
            )
            if not success:
                return jsonify({'error': message}), 500
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return jsonify({'success': True})

    elif request.method == 'DELETE':
        if USE_GITHUB_CONTENT:
            success, message = gh_delete_path(gh_path, f'Delete blog post: {slug}')
            if not success and message == 'not_found':
                return jsonify({'error': 'Post not found'}), 404
            if not success:
                return jsonify({'error': message}), 500
        else:
            if not file_path.exists():
                return jsonify({'error': 'Post not found'}), 404

            file_path.unlink()
        return jsonify({'success': True})


# =============================================================================
# Static Pages
# =============================================================================

@app.route('/pages')
@require_auth
def pages():
    """List all static pages"""
    pages_data = []

    if USE_GITHUB_CONTENT:
        items, error = gh_list_markdown('src/content/pages', reverse=False)
        if error:
            return f'Error loading pages: {error}', 500

        for item in items or []:
            fm, _ = parse_frontmatter(item['content'])
            slug = Path(item['name']).stem
            pages_data.append({
                'slug': slug,
                'title': fm.get('title', slug),
                'description': fm.get('description', '')
            })
    else:
        for file in sorted(PAGES_DIR.glob('*.md')):
            with open(file, 'r', encoding='utf-8') as f:
                fm, _ = parse_frontmatter(f.read())
                pages_data.append({
                    'slug': file.stem,
                    'title': fm.get('title', file.stem),
                    'description': fm.get('description', '')
                })

    return render_template('pages.html', pages=pages_data)


@app.route('/pages/new')
@require_auth
def new_page():
    """Create a new static page"""
    return render_template('page_editor.html', page=None, is_new=True)


@app.route('/pages/<slug>')
@require_auth
def edit_page(slug):
    """Edit a static page"""
    if USE_GITHUB_CONTENT:
        content, _, error = gh_read_text(f'src/content/pages/{slug}.md')
        if error == 'not_found':
            return 'Page not found', 404
        if error:
            return f'Error loading page: {error}', 500
    else:
        file_path = PAGES_DIR / f'{slug}.md'
        if not file_path.exists():
            return 'Page not found', 404

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    fm, body = parse_frontmatter(content)

    # Convert markdown to HTML for CKEditor
    body_html = markdown_to_html(body)

    page = {
        'slug': slug,
        'title': fm.get('title', ''),
        'description': fm.get('description', ''),
        'body': body_html
    }

    return render_template('page_editor.html', page=page, is_new=False)


@app.route('/api/pages', methods=['POST'])
@require_auth
def api_create_page():
    """Create a new static page"""
    data = request.json
    title = data.get('title', '').strip()
    slug = data.get('slug', '').strip()

    if not title:
        return jsonify({'error': 'Title is required'}), 400

    if not slug:
        slug = slugify(title)

    frontmatter = {
        'title': title,
        'description': data.get('description', ''),
    }

    body = data.get('body', '')
    content = generate_markdown(frontmatter, body)

    if USE_GITHUB_CONTENT:
        existing, _, read_error = gh_read_text(f'src/content/pages/{slug}.md')
        if read_error is None and existing is not None:
            return jsonify({'error': 'A page with this slug already exists'}), 400
        if read_error not in ('not_found', None):
            return jsonify({'error': read_error}), 500

        success, message = gh_upsert_text(
            f'src/content/pages/{slug}.md',
            content,
            f'Create page: {title}'
        )
        if not success:
            return jsonify({'error': message}), 500
    else:
        file_path = PAGES_DIR / f'{slug}.md'
        if file_path.exists():
            return jsonify({'error': 'A page with this slug already exists'}), 400

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

    return jsonify({'success': True, 'slug': slug})


@app.route('/api/pages/<slug>', methods=['GET', 'POST', 'DELETE'])
@require_auth
def api_page(slug):
    """Get, update, or delete a static page"""
    file_path = PAGES_DIR / f'{slug}.md'
    gh_path = f'src/content/pages/{slug}.md'

    if request.method == 'GET':
        if USE_GITHUB_CONTENT:
            content, _, error = gh_read_text(gh_path)
            if error == 'not_found':
                return jsonify({'error': 'Page not found'}), 404
            if error:
                return jsonify({'error': error}), 500
        else:
            if not file_path.exists():
                return jsonify({'error': 'Page not found'}), 404

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        fm, body = parse_frontmatter(content)
        return jsonify({
            'slug': slug,
            'title': fm.get('title', ''),
            'description': fm.get('description', ''),
            'body': body
        })

    elif request.method == 'POST':
        data = request.json

        frontmatter = {
            'title': data.get('title', ''),
            'description': data.get('description', ''),
        }

        body = data.get('body', '')
        content = generate_markdown(frontmatter, body)

        if USE_GITHUB_CONTENT:
            success, message = gh_upsert_text(
                gh_path,
                content,
                f"Update page: {data.get('title', slug)}"
            )
            if not success:
                return jsonify({'error': message}), 500
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return jsonify({'success': True})

    elif request.method == 'DELETE':
        if USE_GITHUB_CONTENT:
            success, message = gh_delete_path(gh_path, f'Delete page: {slug}')
            if not success and message == 'not_found':
                return jsonify({'error': 'Page not found'}), 404
            if not success:
                return jsonify({'error': message}), 500
        else:
            if not file_path.exists():
                return jsonify({'error': 'Page not found'}), 404

            file_path.unlink()
        return jsonify({'success': True})


# =============================================================================
# Homepage
# =============================================================================

@app.route('/home')
@require_auth
def home():
    """Edit homepage content"""
    if USE_GITHUB_CONTENT:
        content, _, error = gh_read_text('src/content/home/index.md')
        if error == 'not_found':
            return 'Homepage content not found', 404
        if error:
            return f'Error loading homepage: {error}', 500
    else:
        file_path = HOME_DIR / 'index.md'
        if not file_path.exists():
            return 'Homepage content not found', 404

        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

    fm, body = parse_frontmatter(content)

    # Convert markdown to HTML for CKEditor
    body_html = markdown_to_html(body)

    home_data = {
        'title': fm.get('title', ''),
        'tagline': fm.get('tagline', ''),
        'intro': fm.get('intro', ''),
        'body': body_html
    }

    return render_template('home_editor.html', home=home_data)


@app.route('/api/home', methods=['GET', 'POST'])
@require_auth
def api_home():
    """Get or update homepage content"""
    file_path = HOME_DIR / 'index.md'
    gh_path = 'src/content/home/index.md'

    if request.method == 'GET':
        if USE_GITHUB_CONTENT:
            content, _, error = gh_read_text(gh_path)
            if error == 'not_found':
                return jsonify({'error': 'Homepage not found'}), 404
            if error:
                return jsonify({'error': error}), 500
        else:
            if not file_path.exists():
                return jsonify({'error': 'Homepage not found'}), 404

            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()

        fm, body = parse_frontmatter(content)
        return jsonify({
            'title': fm.get('title', ''),
            'tagline': fm.get('tagline', ''),
            'intro': fm.get('intro', ''),
            'body': body
        })

    elif request.method == 'POST':
        data = request.json

        frontmatter = {
            'title': data.get('title', ''),
            'tagline': data.get('tagline', ''),
            'intro': data.get('intro', ''),
        }

        body = data.get('body', '')
        content = generate_markdown(frontmatter, body)

        if USE_GITHUB_CONTENT:
            success, message = gh_upsert_text(
                gh_path,
                content,
                'Update homepage content'
            )
            if not success:
                return jsonify({'error': message}), 500
        else:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return jsonify({'success': True})


# =============================================================================
# Blog Page
# =============================================================================

@app.route('/blog-page')
@require_auth
def blog_page():
    """Edit blog listing page settings"""
    gh_path = 'src/content/blog-page/index.md'

    if USE_GITHUB_CONTENT:
        content, _, error = gh_read_text(gh_path)
        if error == 'not_found':
            fm, body = {'title': 'Blog', 'intro': ''}, ''
        elif error:
            return f'Error loading blog page settings: {error}', 500
        else:
            fm, body = parse_frontmatter(content)
    else:
        file_path = BLOG_PAGE_DIR / 'index.md'
        if not file_path.exists():
            fm, body = {'title': 'Blog', 'intro': ''}, ''
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                fm, body = parse_frontmatter(f.read())

    blog_data = {
        'title': fm.get('title', 'Blog'),
        'intro': fm.get('intro', ''),
        'body': body.strip(),
    }
    return render_template('blog_page_editor.html', blog=blog_data)


@app.route('/api/blog-page', methods=['GET', 'POST'])
@require_auth
def api_blog_page():
    """Get or update blog listing page settings"""
    file_path = BLOG_PAGE_DIR / 'index.md'
    gh_path = 'src/content/blog-page/index.md'

    if request.method == 'GET':
        if USE_GITHUB_CONTENT:
            content, _, error = gh_read_text(gh_path)
            if error == 'not_found':
                return jsonify({'title': 'Blog', 'intro': '', 'body': ''})
            if error:
                return jsonify({'error': error}), 500
            fm, body = parse_frontmatter(content)
        else:
            if not file_path.exists():
                return jsonify({'title': 'Blog', 'intro': '', 'body': ''})
            with open(file_path, 'r', encoding='utf-8') as f:
                fm, body = parse_frontmatter(f.read())

        return jsonify({
            'title': fm.get('title', 'Blog'),
            'intro': fm.get('intro', ''),
            'body': body.strip(),
        })

    elif request.method == 'POST':
        data = request.json

        frontmatter = {
            'title': data.get('title', 'Blog'),
            'intro': data.get('intro', ''),
        }

        content = generate_markdown(frontmatter, data.get('body', ''))

        if USE_GITHUB_CONTENT:
            success, message = gh_upsert_text(
                gh_path, content, 'Update blog page settings'
            )
            if not success:
                return jsonify({'error': message}), 500
        else:
            BLOG_PAGE_DIR.mkdir(parents=True, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)

        return jsonify({'success': True})


# =============================================================================
# Image Upload
# =============================================================================

@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_image():
    """Handle image upload from CKEditor"""
    if 'upload' not in request.files:
        return jsonify({'error': {'message': 'No file uploaded'}}), 400

    file = request.files['upload']

    if file.filename == '':
        return jsonify({'error': {'message': 'No file selected'}}), 400

    # Validate file type
    allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
    ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''

    if ext not in allowed_extensions:
        return jsonify({'error': {'message': 'Invalid file type'}}), 400

    # Generate unique filename
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = secure_filename(f"{timestamp}_{file.filename}")

    if USE_GITHUB_CONTENT:
        github_token = get_github_token()
        if not github_token:
            return jsonify({'error': {'message': 'GitHub authentication required'}}), 401

        github_path = f"src/content/blog/images/{filename}"
        github_api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{github_path}"
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github+json'
        }

        file_bytes = file.read()
        encoded_content = base64.b64encode(file_bytes).decode('ascii')
        payload = {
            'message': f'Upload image: {filename}',
            'content': encoded_content,
            'branch': 'main'
        }

        # If file exists, update it; otherwise create it.
        get_resp = requests.get(github_api_url, headers=headers, params={'ref': 'main'})
        if get_resp.status_code == 200:
            payload['sha'] = get_resp.json().get('sha')
        elif get_resp.status_code != 404:
            return jsonify({'error': {'message': f'GitHub API error: {get_resp.text}'}}), 500

        put_resp = requests.put(github_api_url, headers=headers, json=payload, timeout=30)
        if put_resp.status_code not in (200, 201):
            return jsonify({'error': {'message': f'GitHub upload failed: {put_resp.text}'}}), 500
    else:
        # Save file locally in development mode.
        file_path = IMAGES_DIR / filename
        file.save(str(file_path))

    # Return URL that works in the editor (served by Flask)
    return jsonify({
        'url': f'/blog-images/{filename}'
    })


@app.route('/blog-images/<filename>')
@require_auth
def serve_blog_image(filename):
    """Serve blog images so they display in the admin editor"""
    filename = secure_filename(filename)
    if USE_GITHUB_CONTENT:
        github_token = get_github_token()
        if not github_token:
            return 'Unauthorized', 401
        gh_path = f"src/content/blog/images/{filename}"
        api_url = f"https://api.github.com/repos/{GITHUB_REPO_OWNER}/{GITHUB_REPO_NAME}/contents/{gh_path}"
        headers = {
            'Authorization': f'token {github_token}',
            'Accept': 'application/vnd.github+json'
        }
        resp = requests.get(api_url, headers=headers, params={'ref': 'main'})
        if resp.status_code != 200:
            return 'Image not found', 404
        data = resp.json()
        content = base64.b64decode(data['content'])
        # Determine content type from extension
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        content_types = {'jpg': 'image/jpeg', 'jpeg': 'image/jpeg', 'png': 'image/png', 'gif': 'image/gif', 'webp': 'image/webp'}
        ct = content_types.get(ext, 'application/octet-stream')
        return Response(content, mimetype=ct)
    else:
        return send_from_directory(str(IMAGES_DIR), filename)


# =============================================================================
# Navigation Management
# =============================================================================

NAV_GH_PATH = 'src/content/nav/nav.json'
PROTECTED_HREFS = {'/', '/blog'}


def read_nav():
    """Read nav.json and return list of {label, href} dicts."""
    if USE_GITHUB_CONTENT:
        content, _, error = gh_read_text(NAV_GH_PATH)
        if error == 'not_found':
            return [], None
        if error:
            return None, error
        try:
            return json.loads(content), None
        except json.JSONDecodeError as e:
            return None, f"Invalid nav.json: {e}"
    else:
        if not NAV_FILE.exists():
            return [], None
        with open(NAV_FILE, 'r', encoding='utf-8') as f:
            return json.load(f), None


def write_nav(items, commit_message='Update navigation'):
    """Write nav.json with the given list of {label, href} dicts."""
    content = json.dumps(items, indent=2, ensure_ascii=False) + '\n'
    if USE_GITHUB_CONTENT:
        return gh_upsert_text(NAV_GH_PATH, content, commit_message)
    else:
        NAV_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(NAV_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, 'Saved nav.json locally'


def generate_astro_page(slug):
    """Return the content of a generic .astro page file for a given slug."""
    return f"""---
import Page from '../layouts/Page.astro';
import {{ getEntry, render }} from 'astro:content';
import {{ SITE_SEO_TITLE }} from '../consts';

const page = await getEntry('pages', '{slug}');
if (!page) throw new Error('{slug}.md not found');
const {{ Content }} = await render(page);
---

<Page title={{`${{page.data.title}} | ${{SITE_SEO_TITLE}}`}} description={{page.data.description}}>
\t<h1>{{page.data.title}}</h1>
\t<Content />
</Page>
"""


@app.route('/nav')
@require_auth
def nav():
    """Manage site navigation"""
    items, error = read_nav()
    if error:
        return f'Error loading navigation: {error}', 500
    return render_template('nav.html', nav_items=items, protected_hrefs=list(PROTECTED_HREFS))


@app.route('/api/nav', methods=['GET', 'POST'])
@require_auth
def api_nav():
    """Get or update the full nav list (reorder + rename)."""
    if request.method == 'GET':
        items, error = read_nav()
        if error:
            return jsonify({'error': error}), 500
        return jsonify(items)

    elif request.method == 'POST':
        data = request.json
        if not isinstance(data, list):
            return jsonify({'error': 'Expected a list of nav items'}), 400
        cleaned = []
        for item in data:
            if 'label' not in item or 'href' not in item:
                return jsonify({'error': 'Each item must have label and href'}), 400
            entry = {'label': item['label'], 'href': item['href']}
            if item.get('hidden'):
                entry['hidden'] = True
            cleaned.append(entry)

        success, message = write_nav(cleaned, 'Update navigation order/labels')
        if not success:
            return jsonify({'error': message}), 500
        return jsonify({'success': True})


@app.route('/api/nav/add', methods=['POST'])
@require_auth
def api_nav_add():
    """Add a new nav item, creating the .md and .astro files."""
    data = request.json
    label = data.get('label', '').strip()
    slug = data.get('slug', '').strip()

    if not label:
        return jsonify({'error': 'Label is required'}), 400
    if not slug:
        slug = slugify(label)
    if not slug:
        return jsonify({'error': 'Could not generate a valid slug'}), 400

    href = f'/{slug}'

    # Check slug not already in nav
    items, error = read_nav()
    if error:
        return jsonify({'error': error}), 500
    if any(item['href'] == href for item in items):
        return jsonify({'error': f'A nav item with href "{href}" already exists'}), 400

    # Create the .md content file
    frontmatter = {'title': label, 'description': ''}
    body = 'Edit this page content in the admin panel.'
    md_content = generate_markdown(frontmatter, body)
    md_path = f'src/content/pages/{slug}.md'

    if USE_GITHUB_CONTENT:
        existing, _, read_error = gh_read_text(md_path)
        if read_error is None and existing is not None:
            return jsonify({'error': f'A page with slug "{slug}" already exists'}), 400
        success, message = gh_upsert_text(md_path, md_content, f'Create page: {label}')
        if not success:
            return jsonify({'error': message}), 500
    else:
        file_path = PAGES_DIR / f'{slug}.md'
        if file_path.exists():
            return jsonify({'error': f'A page with slug "{slug}" already exists'}), 400
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(md_content)

    # Create the .astro page file
    astro_content = generate_astro_page(slug)
    astro_path = f'src/pages/{slug}.astro'

    if USE_GITHUB_CONTENT:
        success, message = gh_upsert_text(astro_path, astro_content, f'Create page template: {slug}.astro')
        if not success:
            return jsonify({'error': message}), 500
    else:
        astro_file = PAGES_ASTRO_DIR / f'{slug}.astro'
        with open(astro_file, 'w', encoding='utf-8') as f:
            f.write(astro_content)

    # Add to nav list
    items.append({'label': label, 'href': href})
    success, message = write_nav(items, f'Add nav item: {label}')
    if not success:
        return jsonify({'error': message}), 500

    return jsonify({'success': True, 'slug': slug})


@app.route('/api/nav/<slug>', methods=['DELETE'])
@require_auth
def api_nav_delete(slug):
    """Remove a nav item and delete its .md and .astro files."""
    href = f'/{slug}'

    if href in PROTECTED_HREFS:
        return jsonify({'error': 'This nav item cannot be deleted'}), 400

    items, error = read_nav()
    if error:
        return jsonify({'error': error}), 500

    if not any(item['href'] == href for item in items):
        return jsonify({'error': 'Nav item not found'}), 404

    # Remove from nav list
    new_items = [item for item in items if item['href'] != href]
    success, message = write_nav(new_items, f'Remove nav item: {slug}')
    if not success:
        return jsonify({'error': message}), 500

    # Delete .md content file
    md_path = f'src/content/pages/{slug}.md'
    if USE_GITHUB_CONTENT:
        gh_delete_path(md_path, f'Delete page: {slug}')
    else:
        md_file = PAGES_DIR / f'{slug}.md'
        if md_file.exists():
            md_file.unlink()

    # Delete .astro page file
    astro_path = f'src/pages/{slug}.astro'
    if USE_GITHUB_CONTENT:
        gh_delete_path(astro_path, f'Delete page template: {slug}.astro')
    else:
        astro_file = PAGES_ASTRO_DIR / f'{slug}.astro'
        if astro_file.exists():
            astro_file.unlink()

    return jsonify({'success': True})


# =============================================================================
# Appearance Settings
# =============================================================================

APPEARANCE_GH_PATH = 'src/content/settings/appearance.json'
VALID_FONT_THEMES = {'atkinson', 'inter', 'editorial', 'tech', 'minimal'}


def read_appearance():
    """Read appearance.json and return settings dict."""
    if USE_GITHUB_CONTENT:
        content, _, error = gh_read_text(APPEARANCE_GH_PATH)
        if error == 'not_found':
            return {'fontTheme': 'inter'}, None
        if error:
            return None, error
        try:
            return json.loads(content), None
        except json.JSONDecodeError as e:
            return None, f"Invalid appearance.json: {e}"
    else:
        if not APPEARANCE_FILE.exists():
            return {'fontTheme': 'inter'}, None
        with open(APPEARANCE_FILE, 'r', encoding='utf-8') as f:
            return json.load(f), None


def write_appearance(settings, commit_message='Update appearance settings'):
    """Write appearance.json with the given settings dict."""
    content = json.dumps(settings, indent=2, ensure_ascii=False) + '\n'
    if USE_GITHUB_CONTENT:
        return gh_upsert_text(APPEARANCE_GH_PATH, content, commit_message)
    else:
        SETTINGS_DIR.mkdir(parents=True, exist_ok=True)
        with open(APPEARANCE_FILE, 'w', encoding='utf-8') as f:
            f.write(content)
        return True, 'Saved appearance.json locally'


@app.route('/appearance')
@require_auth
def appearance():
    """Manage site appearance"""
    settings, error = read_appearance()
    if error:
        return f'Error loading appearance settings: {error}', 500
    return render_template('appearance.html', settings=settings)


@app.route('/api/appearance', methods=['GET', 'POST'])
@require_auth
def api_appearance():
    """Get or update appearance settings."""
    if request.method == 'GET':
        settings, error = read_appearance()
        if error:
            return jsonify({'error': error}), 500
        return jsonify(settings)

    elif request.method == 'POST':
        data = request.json
        font_theme = data.get('fontTheme', '').strip()

        if font_theme not in VALID_FONT_THEMES:
            return jsonify({'error': f'Invalid font theme: {font_theme}'}), 400

        settings = {'fontTheme': font_theme}
        success, message = write_appearance(settings, f'Update font theme to {font_theme}')
        if not success:
            return jsonify({'error': message}), 500
        return jsonify({'success': True})


# =============================================================================
# Git Operations
# =============================================================================

@app.route('/api/git/commit', methods=['POST'])
@require_auth
def git_commit():
    """Commit and push changes to GitHub"""
    data = request.json
    file_path = data.get('file_path', '')
    commit_message = data.get('commit_message', '')

    if not file_path:
        return jsonify({'error': 'File path is required'}), 400

    if not commit_message:
        return jsonify({'error': 'Commit message is required'}), 400

    if USE_GITHUB_CONTENT:
        # In GitHub-content mode, save/update endpoints already commit directly.
        return jsonify({'success': True, 'message': 'Already committed directly to GitHub'})

    abs_path = BASE_DIR / file_path
    if not abs_path.exists():
        return jsonify({'error': 'File does not exist'}), 404

    success, message = git_commit_and_push(str(abs_path), commit_message)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 500


@app.route('/api/git/delete', methods=['POST'])
@require_auth
def git_delete():
    """Delete a file from GitHub"""
    data = request.json
    file_path = data.get('file_path', '')
    commit_message = data.get('commit_message', '')

    if not file_path:
        return jsonify({'error': 'File path is required'}), 400

    if not commit_message:
        return jsonify({'error': 'Commit message is required'}), 400

    if USE_GITHUB_CONTENT:
        return jsonify({'success': True, 'message': 'Delete is handled directly in GitHub mode'})

    abs_path = BASE_DIR / file_path

    success, message = git_delete_file(str(abs_path), commit_message)

    if success:
        return jsonify({'success': True, 'message': message})
    else:
        return jsonify({'error': message}), 500


if __name__ == '__main__':
    port = int(os.environ.get('ADMIN_PORT', 5000))
    debug = os.environ.get('ADMIN_DEBUG', 'true').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
