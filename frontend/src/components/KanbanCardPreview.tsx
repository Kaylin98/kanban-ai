import type { Card } from "@/lib/kanban";

type KanbanCardPreviewProps = {
  card: Card;
};

// Shown in the DragOverlay, which dnd-kit sizes to the dragged card, so it fills that size.
export const KanbanCardPreview = ({ card }: KanbanCardPreviewProps) => (
  <article className="h-full rounded-2xl border border-transparent bg-white px-4 py-4 shadow-[0_18px_32px_rgba(3,33,71,0.16)]">
    <h4 className="font-display text-base font-semibold leading-6 text-[var(--navy-dark)] wrap-break-word">
      {card.title}
    </h4>
    <p className="mt-1.5 text-sm leading-6 text-[var(--gray-text)] wrap-break-word">
      {card.details}
    </p>
  </article>
);
