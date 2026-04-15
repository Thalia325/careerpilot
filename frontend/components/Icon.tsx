"use client";

import { ReactNode } from "react";

type IconName =
  | "home"
  | "search"
  | "chart"
  | "user"
  | "users"
  | "briefcase"
  | "clock"
  | "chat"
  | "clipboard"
  | "file"
  | "target"
  | "map"
  | "logout"
  | "loading"
  | "paperclip"
  | "edit"
  | "star"
  | "close"
  | "menu"
  | "send"
  | "code"
  | "dollar-sign"
  | "building"
  | "lightbulb"
  | "check-circle"
  | "alert-circle"
  | "trending-up"
  | "hash"
  | "check"
  | "plus"
  | "tag"
  | "upload";

const paths: Record<IconName, string> = {
  home: "M3 9.5L12 3l9 6.5V20a1 1 0 01-1 1h-5v-6H9v6H4a1 1 0 01-1-1V9.5z",
  search: "M10.5 4a6.5 6.5 0 100 13 6.5 6.5 0 000-13zM20 20l-4.35-4.35",
  chart: "M4 20V10M10 20V4M16 20v-7M22 20H2",
  user: "M12 11a4 4 0 100-8 4 4 0 000 8zM4 21v-1a6 6 0 0112 0v1",
  users: "M15 11a4 4 0 100-8 4 4 0 000 8zM2 21v-1a6 6 0 0112 0v1M19 8v4M21 10h-4",
  briefcase: "M6 7V5a2 2 0 012-2h8a2 2 0 012 2v2M2 11h20v9a1 1 0 01-1 1H3a1 1 0 01-1-1v-9zM2 11l4-4h12l4 4",
  clock: "M12 4a8 8 0 100 16 8 8 0 000-16zM12 8v4l3 2",
  chat: "M21 12a9 9 0 01-9 9c-1.6 0-3.1-.4-4.4-1.1L3 21l1.1-4.6A9 9 0 0112 3a9 9 0 019 9z",
  clipboard: "M8 4H6a2 2 0 00-2 2v14a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-2M8 4a2 2 0 012-2h4a2 2 0 012 2M8 4a2 2 0 002 2h4a2 2 0 002-2",
  file: "M6 2h8l6 6v12a2 2 0 01-2 2H6a2 2 0 01-2-2V4a2 2 0 012-2zM14 2v6h6",
  target: "M12 4a8 8 0 100 16 8 8 0 000-16zM12 8a4 4 0 100 8 4 4 0 000-8zM12 12h.01",
  map: "M3 7l6-3 6 3 6-3v13l-6 3-6-3-6 3V7zM9 4v13M15 7v13",
  logout: "M14 8V4a1 1 0 00-1-1H5a1 1 0 00-1 1v16a1 1 0 001 1h8a1 1 0 001-1v-4M17 12H7M17 12l-4-4M17 12l-4 4",
  loading: "M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83",
  paperclip: "M18.5 12.5l-7.8 7.8a4 4 0 01-5.66-5.66l7.8-7.8a2.5 2.5 0 014.53 0 2.5 2.5 0 010 3.54l-7.5 7.5",
  edit: "M4 20h4L18.5 9.5a2.12 2.12 0 00-3-3L5 17v3zM14.5 7.5l3 3",
  star: "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z",
  close: "M6 6l12 12M18 6L6 18",
  menu: "M3 8h18M3 12h18M3 16h18",
  send: "M4 4l16 8-16 8V4zM4 12h10",
  code: "M16 18l6-6-6-6M8 6l-6 6 6 6",
  "dollar-sign": "M12 2v20M8 7h8a4 4 0 010 8h-4M8 17h6a4 4 0 010 8H8",
  building: "M3 21h18M5 21V7l8-4 8 4v14M8 21v-4a2 2 0 012-2h4a2 2 0 012 2v4",
  lightbulb: "M12 2a7 7 0 00-7 7c0 3.866 7 13 7 13s7-9.134 7-13a7 7 0 00-7-7zM12 22a2 2 0 100-4 2 2 0 000 4z",
  "check-circle": "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm-2-15l-4 4 2 2 4-4-2-2zm2 4l6 6-2 2-6-6 2-2z",
  "alert-circle": "M12 22c5.523 0 10-4.477 10-10S17.523 2 12 2 2 6.477 2 12s4.477 10 10 10zm0-14v4m0 4h.01",
  "trending-up": "M22 12l-4-4-6 6-6-6-4 4v8h20v-8z",
  hash: "M4 9h16M4 15h16M10 3v18M14 3v18",
  check: "M20 6L9 17l-5-5",
  plus: "M12 5v14M5 12h14",
  tag: "M12 2l-10 10 3 3 10-10-3-3z M9 7l6 6",
  upload: "M12 16V4M12 4l-4 4M12 4l4 4M4 17v2a1 1 0 001 1h14a1 1 0 001-1v-2",
};

type IconProps = {
  name: IconName;
  size?: number;
  color?: string;
  className?: string;
  spin?: boolean;
  style?: React.CSSProperties;
};

export function Icon({ name, size = 20, color = "currentColor", className, spin, style }: IconProps) {
  const d = paths[name];
  if (!d) return null;
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke={color}
      strokeWidth={1.5}
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      style={{
        display: "inline-block",
        verticalAlign: "middle",
        flexShrink: 0,
        animation: spin ? "icon-spin 1s linear infinite" : undefined,
        ...style,
      }}
    >
      <path d={d} />
    </svg>
  );
}

export type { IconName };
