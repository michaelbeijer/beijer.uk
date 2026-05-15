// Site-wide constants.
// These are sourced from src/content/settings/site.json so they can be edited
// via the admin panel (Site Settings page). Do not hard-code values here -
// edit the JSON instead.
import siteSettings from './content/settings/site.json';

// Site identity (header brand, page titles, meta description)
export const SITE_TITLE = siteSettings.siteTitle;
export const SITE_SEO_TITLE = siteSettings.siteSeoTitle;
export const SITE_DESCRIPTION = siteSettings.siteDescription;

// Footer text block
export const FOOTER_NAME = siteSettings.footerName;
export const FOOTER_TAGLINE = siteSettings.footerTagline;

// Contact info
export const CONTACT_EMAIL = siteSettings.contactEmail;
export const CONTACT_PHONE = siteSettings.contactPhone;

// External profile / project URLs
export const LINKEDIN_URL = siteSettings.linkedinUrl;
export const PROZ_FEEDBACK_URL = siteSettings.prozFeedbackUrl;
export const SUPERVERTALER_URL = siteSettings.supervertalerUrl;
export const BEIJERTERM_URL = siteSettings.beijertermUrl;
export const ADMIN_PANEL_URL = siteSettings.adminPanelUrl;
