/**
 * Client-side Google Drive integration using Google Identity Services (GIS).
 *
 * Creates Google Docs in the **user's own Drive** via an OAuth popup,
 * avoiding any service-account storage quota issues.
 */

const SCOPES = "https://www.googleapis.com/auth/drive.file";

// In-memory token cache (not persisted to storage)
let _cachedToken: string | null = null;
let _tokenExpiry = 0;

declare global {
  interface Window {
    google?: {
      accounts: {
        oauth2: {
          initTokenClient: (config: {
            client_id: string;
            scope: string;
            callback: (resp: { access_token?: string; error?: string; expires_in?: number }) => void;
          }) => { requestAccessToken: () => void };
        };
      };
    };
  }
}

/**
 * Request an OAuth access token via Google Identity Services popup consent.
 * Returns a cached token if one is still valid.
 */
export function requestGoogleToken(): Promise<string> {
  // Return cached token if still valid (with 60s buffer)
  if (_cachedToken && Date.now() < _tokenExpiry - 60_000) {
    return Promise.resolve(_cachedToken);
  }

  const clientId = process.env.NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID;
  if (!clientId) {
    return Promise.reject(new Error("Google OAuth Client ID is not configured."));
  }

  if (!window.google?.accounts?.oauth2) {
    return Promise.reject(
      new Error("Google Identity Services script not loaded. Please try again."),
    );
  }

  return new Promise<string>((resolve, reject) => {
    const client = window.google!.accounts.oauth2.initTokenClient({
      client_id: clientId,
      scope: SCOPES,
      callback: (resp) => {
        if (resp.error) {
          reject(new Error(`Google auth failed: ${resp.error}`));
          return;
        }
        if (!resp.access_token) {
          reject(new Error("No access token received from Google."));
          return;
        }
        _cachedToken = resp.access_token;
        _tokenExpiry = Date.now() + (resp.expires_in ?? 3600) * 1000;
        resolve(resp.access_token);
      },
    });

    client.requestAccessToken();
  });
}

/**
 * Convert an SVG URL to a PNG base64 data URI via an offscreen canvas.
 * Returns null if conversion fails (caller should keep original).
 */
async function svgUrlToBase64Png(url: string): Promise<string | null> {
  try {
    const res = await fetch(url);
    if (!res.ok) return null;
    const svgText = await res.text();
    const blob = new Blob([svgText], { type: "image/svg+xml;charset=utf-8" });
    const blobUrl = URL.createObjectURL(blob);

    return await new Promise<string | null>((resolve) => {
      const img = new Image();
      img.onload = () => {
        const canvas = document.createElement("canvas");
        // Render at 2x for sharpness
        canvas.width = img.naturalWidth * 2 || 400;
        canvas.height = img.naturalHeight * 2 || 200;
        const ctx = canvas.getContext("2d")!;
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
        URL.revokeObjectURL(blobUrl);
        resolve(canvas.toDataURL("image/png"));
      };
      img.onerror = () => {
        URL.revokeObjectURL(blobUrl);
        resolve(null);
      };
      img.src = blobUrl;
    });
  } catch {
    return null;
  }
}

/**
 * Replace SVG <img> src attributes in the HTML with base64 PNG data URIs.
 * Google Docs HTML import does not support SVG images.
 */
async function replaceSvgImagesWithPng(html: string): Promise<string> {
  const svgImgRegex = /<img([^>]*?)src=["']([^"']+\.svg)["']([^>]*?)\/?>/gi;
  const matches = [...html.matchAll(svgImgRegex)];
  if (matches.length === 0) return html;

  let result = html;
  for (const match of matches) {
    const [fullMatch, before, svgUrl, after] = match;
    const pngDataUri = await svgUrlToBase64Png(svgUrl);
    if (pngDataUri) {
      result = result.replace(fullMatch, `<img${before}src="${pngDataUri}"${after}/>`);
    }
  }
  return result;
}

/**
 * Upload an HTML string to Google Drive as a native Google Doc (multipart upload).
 *
 * @returns The edit URL of the newly created Google Doc.
 */
export async function uploadHtmlAsGoogleDoc(
  html: string,
  title: string,
  token: string,
): Promise<string> {
  // Convert SVG images to PNG so Google Docs can render them
  const processedHtml = await replaceSvgImagesWithPng(html);

  const metadata = {
    name: title,
    mimeType: "application/vnd.google-apps.document",
  };

  const boundary = "----GDocUploadBoundary";
  const body =
    `--${boundary}\r\n` +
    `Content-Type: application/json; charset=UTF-8\r\n\r\n` +
    `${JSON.stringify(metadata)}\r\n` +
    `--${boundary}\r\n` +
    `Content-Type: text/html; charset=UTF-8\r\n\r\n` +
    `${processedHtml}\r\n` +
    `--${boundary}--`;

  const res = await fetch(
    "https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id",
    {
      method: "POST",
      headers: {
        Authorization: `Bearer ${token}`,
        "Content-Type": `multipart/related; boundary=${boundary}`,
      },
      body,
    },
  );

  if (!res.ok) {
    const errText = await res.text().catch(() => "");
    throw new Error(`Drive upload failed (${res.status}): ${errText}`);
  }

  const data = await res.json();
  return `https://docs.google.com/document/d/${data.id}/edit`;
}
