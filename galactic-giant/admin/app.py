"""
michaelbeijer.co.uk Admin Panel
Custom CMS for managing blog posts, pages, and homepage content
Uses Jodit Editor for rich text editing with image drag-resize handles
"""
import os
import sys
import re
import yaml
import markdown
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
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
BASE_DIR = Path(__file__).parent.parent
CONTENT_DIR = BASE_DIR / 'src' / 'content'
BLOG_DIR = CONTENT_DIR / 'blog'
PAGES_DIR = CONTENT_DIR / 'pages'
HOME_DIR = CONTENT_DIR / 'home'
IMAGES_DIR = BLOG_DIR / 'images'

# Ensure directories exist
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

@app.route('/')
@require_auth
def index():
    """Admin dashboard"""
    stats = {
        'posts': len(list(BLOG_DIR.glob('*.md'))),
        'pages': len(list(PAGES_DIR.glob('*.md'))),
    }

    # Recent posts
    posts = []
    for file in sorted(BLOG_DIR.glob('*.md'), reverse=True)[:5]:
        with open(file, 'r', encoding='utf-8') as f:
            fm, _ = parse_frontmatter(f.read())
            posts.append({
                'slug': file.stem,
                'title': fm.get('title', file.stem),
                'pubDate': fm.get('pubDate', '')
            })

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

    for file in sorted(BLOG_DIR.glob('*.md'), reverse=True):
        with open(file, 'r', encoding='utf-8') as f:
            fm, _ = parse_frontmatter(f.read())
            posts_data.append({
                'slug': file.stem,
                'title': fm.get('title', file.stem),
                'pubDate': fm.get('pubDate', ''),
                'description': fm.get('description', '')[:100] + '...' if fm.get('description', '') else ''
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
    file_path = BLOG_DIR / f'{slug}.md'

    if not file_path.exists():
        return 'Post not found', 404

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    fm, body = parse_frontmatter(content)

    # Convert markdown to HTML for CKEditor
    body_html = markdown_to_html(body)

    post = {
        'slug': slug,
        'title': fm.get('title', ''),
        'description': fm.get('description', ''),
        'pubDate': fm.get('pubDate', ''),
        'heroImage': fm.get('heroImage', ''),
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
    file_path = BLOG_DIR / f'{slug}.md'

    if file_path.exists():
        return jsonify({'error': 'A post with this title already exists'}), 400

    frontmatter = {
        'title': title,
        'description': data.get('description', ''),
        'pubDate': data.get('pubDate', datetime.now().strftime('%Y-%m-%d')),
    }

    if data.get('heroImage'):
        frontmatter['heroImage'] = data['heroImage']

    body = data.get('body', '')
    content = generate_markdown(frontmatter, body)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return jsonify({'success': True, 'slug': slug})


@app.route('/api/posts/<slug>', methods=['GET', 'POST', 'DELETE'])
@require_auth
def api_post(slug):
    """Get, update, or delete a blog post"""
    file_path = BLOG_DIR / f'{slug}.md'

    if request.method == 'GET':
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

        body = data.get('body', '')
        content = generate_markdown(frontmatter, body)

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({'success': True})

    elif request.method == 'DELETE':
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

    file_path = PAGES_DIR / f'{slug}.md'

    if file_path.exists():
        return jsonify({'error': 'A page with this slug already exists'}), 400

    frontmatter = {
        'title': title,
        'description': data.get('description', ''),
    }

    body = data.get('body', '')
    content = generate_markdown(frontmatter, body)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    return jsonify({'success': True, 'slug': slug})


@app.route('/api/pages/<slug>', methods=['GET', 'POST', 'DELETE'])
@require_auth
def api_page(slug):
    """Get, update, or delete a static page"""
    file_path = PAGES_DIR / f'{slug}.md'

    if request.method == 'GET':
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

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return jsonify({'success': True})

    elif request.method == 'DELETE':
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

    if request.method == 'GET':
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

    # Save file
    file_path = IMAGES_DIR / filename
    file.save(str(file_path))

    # Return URL for CKEditor (relative path for markdown)
    return jsonify({
        'url': f'./images/{filename}'
    })


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
