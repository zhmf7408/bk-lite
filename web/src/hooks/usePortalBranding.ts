'use client';

import { useEffect, useMemo, useState } from 'react';

const DEFAULT_PORTAL_NAME = 'BlueKing Lite';
const DEFAULT_PORTAL_LOGO_URL = '/logo-site.png';
const DEFAULT_PORTAL_FAVICON_URL = '/logo-site.png';
const DEFAULT_WATERMARK_TEXT = 'BlueKing Lite · ${username} · ${date}';
const PORTAL_BRANDING_EVENT = 'portal-branding-updated';

export interface PortalBrandingState {
  portalName: string;
  logoUrl: string;
  faviconUrl: string;
  watermarkEnabled: boolean;
  watermarkText: string;
}

const DEFAULT_STATE: PortalBrandingState = {
  portalName: DEFAULT_PORTAL_NAME,
  logoUrl: DEFAULT_PORTAL_LOGO_URL,
  faviconUrl: DEFAULT_PORTAL_FAVICON_URL,
  watermarkEnabled: false,
  watermarkText: DEFAULT_WATERMARK_TEXT,
};

const resolveUrl = (value?: string, fallback = DEFAULT_PORTAL_LOGO_URL) => {
  const normalizedValue = value?.trim();
  return normalizedValue || fallback;
};

const normalizeBranding = (settings?: {
  portal_name?: string;
  portal_logo_url?: string;
  portal_favicon_url?: string;
  watermark_enabled?: string;
  watermark_text?: string;
}): PortalBrandingState => ({
  portalName: settings?.portal_name?.trim() || DEFAULT_PORTAL_NAME,
  logoUrl: resolveUrl(settings?.portal_logo_url, DEFAULT_PORTAL_LOGO_URL),
  faviconUrl: resolveUrl(settings?.portal_favicon_url, DEFAULT_PORTAL_FAVICON_URL),
  watermarkEnabled: settings?.watermark_enabled === '1',
  watermarkText: settings?.watermark_text?.trim() || DEFAULT_WATERMARK_TEXT,
});

export const emitPortalBrandingUpdated = (branding: Partial<PortalBrandingState>) => {
  if (typeof window === 'undefined') {
    return;
  }

  window.dispatchEvent(new CustomEvent<Partial<PortalBrandingState>>(PORTAL_BRANDING_EVENT, {
    detail: branding,
  }));
};

export const usePortalBranding = () => {
  const [branding, setBranding] = useState<PortalBrandingState>(DEFAULT_STATE);

  useEffect(() => {
    let cancelled = false;

    const fetchBranding = async () => {
      try {
        const response = await fetch('/api/proxy/core/api/get_bk_settings/', {
          cache: 'no-store',
        });

        if (!response.ok) {
          if (!cancelled) {
            setBranding(DEFAULT_STATE);
          }
          return;
        }

        const payload = await response.json();
        const settings = payload?.data || {};

        if (!payload?.result || cancelled) {
          return;
        }

        setBranding(normalizeBranding(settings));
      } catch {
        if (!cancelled) {
          setBranding(DEFAULT_STATE);
        }
      }
    };

    fetchBranding();

    const handleBrandingUpdated = (event: Event) => {
      const nextBranding = (event as CustomEvent<Partial<PortalBrandingState>>).detail;
      if (!nextBranding || cancelled) {
        return;
      }

      setBranding((previousBranding) => ({
        ...previousBranding,
        ...nextBranding,
      }));
    };

    window.addEventListener(PORTAL_BRANDING_EVENT, handleBrandingUpdated as EventListener);

    return () => {
      cancelled = true;
      window.removeEventListener(PORTAL_BRANDING_EVENT, handleBrandingUpdated as EventListener);
    };
  }, []);

  return useMemo(() => branding, [branding]);
};

export const portalBrandingDefaults = {
  portalName: DEFAULT_PORTAL_NAME,
  logoUrl: DEFAULT_PORTAL_LOGO_URL,
  faviconUrl: DEFAULT_PORTAL_FAVICON_URL,
  watermarkEnabled: false,
  watermarkText: DEFAULT_WATERMARK_TEXT,
};
