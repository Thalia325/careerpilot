"use client";

import Link from "next/link";

export function EmptyState({
  icon,
  title,
  description,
  actionLabel,
  actionHref,
  actionOnClick
}: {
  icon?: string;
  title: string;
  description: string;
  actionLabel?: string;
  actionHref?: string;
  actionOnClick?: () => void;
}) {
  return (
    <div className="empty-state" role="region" aria-label={title}>
      {icon && (
        <div className="empty-state__icon" aria-hidden="true">
          {icon}
        </div>
      )}
      <h3 className="empty-state__title">{title}</h3>
      <p className="empty-state__description">{description}</p>
      {actionLabel && (
        <div className="empty-state__actions">
          {actionHref ? (
            <Link href={actionHref} className="app-header__button" aria-label={`${actionLabel}：前往${title.replace('还没有', '')}`}>
              {actionLabel}
            </Link>
          ) : (
            <button onClick={actionOnClick} aria-label={actionLabel}>
              {actionLabel}
            </button>
          )}
        </div>
      )}
    </div>
  );
}
