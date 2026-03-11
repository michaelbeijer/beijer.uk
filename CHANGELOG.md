# Changelog

All notable changes to this project will be documented in this file.

## [1.5.0] - 2026-03-11

### Added
- Hidden/draft blog posts: mark posts as hidden to keep them off the public site while editing
- `hidden` boolean field in blog content schema (optional, defaults to visible)
- "Hidden" checkbox in the blog post editor
- Status column in admin posts list showing "Hidden" or "Visible" badges
- Quick "Hide/Unhide" toggle button on the posts list for one-click visibility changes
- Hidden posts are filtered from the public blog listing and individual post page generation

### Changed
- Hidden post rows appear dimmed in the admin posts list for visual clarity

## [1.4.0] - 2026-03-09

### Added
- Blog page editor in admin panel: edit the blog listing page title and intro text
- New `blog-page` content collection for blog listing page settings
- "Edit Blog Page" button on the Posts admin page
- Save & Commit to GitHub support for blog page settings

### Changed
- Navigation label inputs in admin now have visible borders and hover/focus styles
- Homepage intro text now supports line breaks (entered via admin textarea)
- Increased line spacing on homepage intro and tagline for better readability

### Fixed
- Homepage links (About, Work, Contact) now correctly use BASE_URL prefix for GitHub Pages
- Admin link in footer now matches the font size of other footer links
- Removed redundant About/Work links and horizontal rule from below CTA buttons on homepage

## [1.3.0] - 2026-03-09

### Added
- Font theme picker in admin panel (new "Appearance" tab)
- Five font themes: Clean & Modern (Inter), Classic Editorial (Playfair Display + Source Sans 3), Tech / Developer (Space Grotesk + IBM Plex Sans), Minimal & Refined (DM Sans), and Atkinson Hyperlegible (original)
- `src/content/settings/appearance.json` stores the selected font theme
- Google Fonts loaded conditionally based on selected theme for optimal performance
- CSS custom properties `--font-heading` and `--font-body` for flexible typography
- New `/appearance` admin route and `/api/appearance` API endpoint
- Live font previews in the admin theme picker

### Changed
- Body and heading fonts now use CSS variables instead of hardcoded Atkinson font
- Default font changed from Atkinson Hyperlegible to Inter

## [1.2.1] - 2026-02-20

### Added
- Per-tab visibility toggle in Navigation admin: uncheck "Visible" to hide a tab from the site without deleting it
- Hidden tabs remain accessible by direct URL; only the nav link is suppressed
- Hidden rows appear dimmed in the admin UI for clarity
- `hidden: true` field supported in `nav.json` items (omitted when visible, keeping the file clean)

## [1.2.0] - 2026-02-20

### Added
- Navigation management in admin panel: reorder, rename, add, and delete nav tabs
- `src/content/nav/nav.json` as the data-driven source of truth for site navigation
- Drag-and-drop row reordering on the Navigation admin page
- Inline label editing for existing nav tabs
- "Add New Tab" form that automatically creates the `.astro` page template and `.md` content file
- Home and Blog tabs protected from deletion
- New `/nav` admin route and API endpoints (`GET/POST /api/nav`, `POST /api/nav/add`, `DELETE /api/nav/<slug>`)

### Changed
- `Header.astro` now renders navigation dynamically from `nav.json` instead of hardcoded links

## [1.1.0] - 2026-01-21

### Added
- Hamburger menu for mobile navigation with slide-in panel
- Blog posts now grouped by year (2025, 2024, 2013)
- Bullet points for blog post listings
- New blog post: Termania interview (2013)
- New blog post: tranzlashion.com spoof translation company (2024)

### Changed
- Site title changed to michaelbeijer.co.uk
- Blog renamed to "Beijerblog" in navigation and page title
- Reduced heading sizes for better visual balance (h1: 2.5em, h2: 1.75em, h3: 1.4em)
- Removed featured/hero styling from first blog post
- Blog layout changed from grid to simple year-grouped list

### Fixed
- Mobile navigation now collapses into hamburger menu below 720px

## [1.0.0] - 2026-01-21

### Added
- Initial site launch with Astro static site generator
- Home page with professional summary and side projects
- Patents page detailing patent translation services
- Services page with translation, editing, and terminology offerings
- Work page showcasing experience and clients
- Testimonials page with 22 client quotes (2010-2025)
- Tools page listing software and workflow tools
- Blog with initial posts on CAT tools and translation technology
- Contact page with email and phone details
- About page with 30+ years experience, 25M+ words translated
- Back-to-top button on all pages
- RSS feed for blog posts
- Sitemap for SEO

### Fixed
- Base URL configuration for GitHub Pages deployment
- UTF-8 encoding for special characters
- Internal link paths with proper BASE_URL prefix