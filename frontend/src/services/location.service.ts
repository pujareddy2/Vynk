import { userService } from "./user.service";

export interface LiveLocationResult {
  locality: string;
  city?: string;
  state?: string;
  latitude?: number;
  longitude?: number;
  source: "GPS" | "IP" | "CACHE";
}

let cachedLocation: LiveLocationResult | null = null;
let detectionPromise: Promise<LiveLocationResult | null> | null = null;

/**
 * Automatically detects the user's real live location using browser HTML5 Geolocation,
 * followed by reverse geocoding to resolve neighborhood and city.
 * Falls back to IP-based city detection if browser GPS is restricted or denied.
 * Does NOT require any button click.
 */
export async function detectLiveLocation(): Promise<LiveLocationResult | null> {
  if (cachedLocation) {
    return cachedLocation;
  }

  if (detectionPromise) {
    return detectionPromise;
  }

  detectionPromise = new Promise(async (resolve) => {
    // 1. Try Browser HTML5 Geolocation API
    if (typeof window !== "undefined" && navigator.geolocation) {
      try {
        const position = await new Promise<GeolocationPosition>((res, rej) => {
          navigator.geolocation.getCurrentPosition(res, rej, {
            timeout: 6000,
            maximumAge: 300000, // 5 min cache
            enableHighAccuracy: true,
          });
        });

        const { latitude, longitude } = position.coords;

        // Reverse-geocode coordinates to actual neighborhood & city
        try {
          const geoRes = await fetch(
            `https://nominatim.openstreetmap.org/reverse?format=json&lat=${latitude}&lon=${longitude}&zoom=14`,
            { headers: { "Accept-Language": "en" } }
          );

          if (geoRes.ok) {
            const data = await geoRes.json();
            const addr = data.address || {};
            const suburb =
              addr.suburb ||
              addr.neighbourhood ||
              addr.residential ||
              addr.subdistrict ||
              addr.quarter;
            const city =
              addr.city ||
              addr.town ||
              addr.village ||
              addr.county ||
              addr.state_district;
            const state = addr.state;

            let localityName = "";
            if (suburb && city) {
              localityName = `${suburb}, ${city}`;
            } else if (city && state) {
              localityName = `${city}, ${state}`;
            } else if (city) {
              localityName = city;
            } else if (data.display_name) {
              const parts = data.display_name
                .split(",")
                .map((s: string) => s.trim());
              localityName = parts.slice(0, 2).join(", ");
            }

            if (localityName) {
              const result: LiveLocationResult = {
                locality: localityName,
                city,
                state,
                latitude,
                longitude,
                source: "GPS",
              };
              cachedLocation = result;
              resolve(result);
              return;
            }
          }
        } catch (revErr) {
          console.warn("Reverse geocode lookup error:", revErr);
        }

        // If reverse geocoding API timed out, return coordinate-derived representation
        const coordResult: LiveLocationResult = {
          locality: `${latitude.toFixed(3)}, ${longitude.toFixed(3)}`,
          latitude,
          longitude,
          source: "GPS",
        };
        cachedLocation = coordResult;
        resolve(coordResult);
        return;
      } catch (gpsErr) {
        console.warn("HTML5 Geolocation unavailable, falling back to IP:", gpsErr);
      }
    }

    // 2. Fallback to IP-based Geolocation (zero permission prompt required)
    try {
      const ipRes = await fetch("https://ipapi.co/json/");
      if (ipRes.ok) {
        const ipData = await ipRes.json();
        if (ipData.city) {
          const locString = ipData.region
            ? `${ipData.city}, ${ipData.region}`
            : ipData.city;
          const result: LiveLocationResult = {
            locality: locString,
            city: ipData.city,
            state: ipData.region,
            latitude: ipData.latitude,
            longitude: ipData.longitude,
            source: "IP",
          };
          cachedLocation = result;
          resolve(result);
          return;
        }
      }
    } catch (ipErr) {
      console.warn("IP geolocation fallback error:", ipErr);
    }

    resolve(null);
  });

  return detectionPromise;
}

/**
 * Automatically detects the user's real live location and pushes it straight
 * to the backend profile (PostgreSQL) and updates local storage.
 * Runs silently in the background on profile creation, login, or page load.
 */
export async function autoDetectAndSyncLocation(): Promise<string | null> {
  try {
    const live = await detectLiveLocation();
    if (!live || !live.locality) return null;

    // Check existing stored location
    let existingLoc = "";
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("vynk_user");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          existingLoc = parsed.location || "";
        } catch {}
      }
    }

    // Save to localStorage
    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("vynk_user");
      if (stored) {
        try {
          const parsed = JSON.parse(stored);
          parsed.location = live.locality;
          localStorage.setItem("vynk_user", JSON.stringify(parsed));
        } catch {}
      }
    }

    // Update backend user profile if changed or empty
    if (live.locality !== existingLoc) {
      await userService.updateProfile({ approx_locality: live.locality });
    }

    return live.locality;
  } catch (err) {
    console.warn("Auto-sync live location error:", err);
    return null;
  }
}
