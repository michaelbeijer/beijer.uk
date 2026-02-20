# Changelog

All notable changes to this project will be documented in this file.

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