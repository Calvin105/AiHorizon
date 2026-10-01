import type { NextConfig } from "next";

/** Where the browser's /api calls are forwarded. The backend stays on
 * localhost; only this server needs to be reachable — so a phone on the
 * booth Wi-Fi can use the app with just the laptop's address. */
const API_TARGET = process.env.API_PROXY_TARGET ?? "http://127.0.0.1:8001";

const nextConfig: NextConfig = {
  // The dev-mode route indicator badge renders fixed to the bottom-left
  // corner, right on top of the chat panel's input row in this layout —
  // it eats clicks meant for the chips/Confirm button. Dev-only chrome,
  // not present in a production build, so turning it off costs nothing.
  devIndicators: false,
  async rewrites() {
    return [{ source: "/api/:path*", destination: `${API_TARGET}/api/:path*` }];
  },
};

export default nextConfig;
