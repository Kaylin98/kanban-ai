"use client";

import { useEffect, useMemo, useRef, useState } from "react";
import {
  DndContext,
  DragOverlay,
  MeasuringStrategy,
  PointerSensor,
  useSensor,
  useSensors,
  pointerWithin,
  type CollisionDetection,
  type DragEndEvent,
  type DragOverEvent,
  type DragStartEvent,
} from "@dnd-kit/core";
import { ChatWidget } from "@/components/ChatWidget";
import { KanbanColumn } from "@/components/KanbanColumn";
import { KanbanCardPreview } from "@/components/KanbanCardPreview";
import { saveBoard } from "@/lib/api";
import { createId, findColumnId, moveCard, type BoardData } from "@/lib/kanban";

type KanbanBoardProps = {
  initialBoard: BoardData;
  onLogout: () => void;
};

export const KanbanBoard = ({ initialBoard, onLogout }: KanbanBoardProps) => {
  const [board, setBoard] = useState(initialBoard);
  const [activeCardId, setActiveCardId] = useState<string | null>(null);
  const dragStartBoard = useRef(board);
  const savedBoard = useRef(board);

  // Save every change, except the intermediate states while a card is dragged.
  useEffect(() => {
    if (activeCardId === null && board !== savedBoard.current) {
      savedBoard.current = board;
      saveBoard(board);
    }
  }, [board, activeCardId]);

  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: { distance: 6 },
    })
  );

  const cardsById = useMemo(() => board.cards, [board.cards]);

  // The column under the pointer is the target column. The slot is the number of
  // other cards in it whose midpoint is above the dragged card's center. Returns
  // the card currently in that slot (or the column when the slot is the end), so
  // the sortable preview and moveCard both place the card there.
  const collisionDetection: CollisionDetection = (args) => {
    const [columnHit] = pointerWithin({
      ...args,
      droppableContainers: args.droppableContainers.filter((container) =>
        board.columns.some((column) => column.id === container.id)
      ),
    });
    if (!columnHit) {
      return [];
    }
    const column = board.columns.find((c) => c.id === columnHit.id)!;
    const centerY = args.collisionRect.top + args.collisionRect.height / 2;
    const slot = column.cardIds.filter((id) => {
      const rect = args.droppableRects.get(id);
      return id !== args.active.id && rect && rect.top + rect.height / 2 < centerY;
    }).length;
    return [{ id: column.cardIds[slot] ?? column.id }];
  };

  const handleDragStart = (event: DragStartEvent) => {
    dragStartBoard.current = board;
    setActiveCardId(event.active.id as string);
  };

  // Move the card into another column as soon as it is dragged over it, so that
  // column's sortable list opens a gap and previews the drop position.
  const handleDragOver = ({ active, over }: DragOverEvent) => {
    if (!over) {
      return;
    }
    setBoard((prev) => {
      const activeColumnId = findColumnId(prev.columns, active.id as string);
      const overColumnId = findColumnId(prev.columns, over.id as string);
      if (activeColumnId === overColumnId) {
        return prev;
      }
      return {
        ...prev,
        columns: moveCard(prev.columns, active.id as string, over.id as string),
      };
    });
  };

  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    setActiveCardId(null);

    if (!over || active.id === over.id) {
      return;
    }

    setBoard((prev) => ({
      ...prev,
      columns: moveCard(prev.columns, active.id as string, over.id as string),
    }));
  };

  const handleDragCancel = () => {
    setActiveCardId(null);
    setBoard(dragStartBoard.current);
  };

  const handleRenameColumn = (columnId: string, title: string) => {
    setBoard((prev) => ({
      ...prev,
      columns: prev.columns.map((column) =>
        column.id === columnId ? { ...column, title } : column
      ),
    }));
  };

  const handleAddCard = (columnId: string, title: string, details: string) => {
    const id = createId("card");
    setBoard((prev) => ({
      ...prev,
      cards: {
        ...prev.cards,
        [id]: { id, title, details: details || "No details yet." },
      },
      columns: prev.columns.map((column) =>
        column.id === columnId
          ? { ...column, cardIds: [...column.cardIds, id] }
          : column
      ),
    }));
  };

  const handleEditCard = (cardId: string, title: string, details: string) => {
    setBoard((prev) => ({
      ...prev,
      cards: { ...prev.cards, [cardId]: { id: cardId, title, details } },
    }));
  };

  const handleDeleteCard = (columnId: string, cardId: string) => {
    setBoard((prev) => {
      return {
        ...prev,
        cards: Object.fromEntries(
          Object.entries(prev.cards).filter(([id]) => id !== cardId)
        ),
        columns: prev.columns.map((column) =>
          column.id === columnId
            ? {
                ...column,
                cardIds: column.cardIds.filter((id) => id !== cardId),
              }
            : column
        ),
      };
    });
  };

  // The server has already saved the AI's board, so mark it saved before showing it.
  const handleAIBoardUpdate = (aiBoard: BoardData) => {
    savedBoard.current = aiBoard;
    setBoard(aiBoard);
  };

  const activeCard = activeCardId ? cardsById[activeCardId] : null;

  return (
    <div className="relative overflow-clip">
      <div className="pointer-events-none absolute left-0 top-0 h-[420px] w-[420px] -translate-x-1/3 -translate-y-1/3 rounded-full bg-[radial-gradient(circle,_rgba(32,157,215,0.25)_0%,_rgba(32,157,215,0.05)_55%,_transparent_70%)]" />
      <div className="pointer-events-none absolute bottom-0 right-0 h-[520px] w-[520px] translate-x-1/4 translate-y-1/4 rounded-full bg-[radial-gradient(circle,_rgba(117,57,145,0.18)_0%,_rgba(117,57,145,0.05)_55%,_transparent_75%)]" />

      <main className="relative mx-auto flex min-h-screen max-w-[1500px] flex-col gap-8 px-4 pb-28 pt-6 sm:gap-10 sm:px-6 sm:pt-12">
        <header className="flex flex-col gap-6 rounded-[32px] border border-[var(--stroke)] bg-white/80 p-6 shadow-[var(--shadow)] backdrop-blur sm:p-8">
          <div className="flex flex-wrap items-start justify-between gap-6">
            <div>
              <p className="text-xs font-semibold uppercase tracking-[0.35em] text-[var(--gray-text)]">
                Single Board Kanban
              </p>
              <h1 className="mt-3 font-display text-3xl font-semibold text-[var(--navy-dark)] sm:text-4xl">
                Kanban Studio
              </h1>
              <p className="mt-3 max-w-xl text-sm leading-6 text-[var(--gray-text)]">
                Keep momentum visible. Rename columns, drag cards between stages,
                and capture quick notes without getting buried in settings.
              </p>
            </div>
            <div className="flex items-start gap-4">
              <div className="hidden rounded-2xl border border-[var(--stroke)] bg-[var(--surface)] px-5 py-4 md:block">
                <p className="text-xs font-semibold uppercase tracking-[0.25em] text-[var(--gray-text)]">
                  Focus
                </p>
                <p className="mt-2 text-lg font-semibold text-[var(--primary-blue)]">
                  One board. Five columns. Zero clutter.
                </p>
              </div>
              <button
                type="button"
                onClick={onLogout}
                className="rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-wide text-[var(--gray-text)] transition hover:text-[var(--navy-dark)]"
              >
                Log out
              </button>
            </div>
          </div>
          {/* Hidden on phones, where it wraps onto several rows and repeats the column titles. */}
          <div className="hidden flex-wrap items-center gap-3 sm:flex">
            {board.columns.map((column) => (
              <div
                key={column.id}
                className="flex items-center gap-2 rounded-full border border-[var(--stroke)] px-4 py-2 text-xs font-semibold uppercase tracking-[0.2em] text-[var(--navy-dark)]"
              >
                <span className="h-2 w-2 rounded-full bg-[var(--accent-yellow)]" />
                {column.title}
              </div>
            ))}
          </div>
        </header>

        <DndContext
          sensors={sensors}
          collisionDetection={collisionDetection}
          measuring={{ droppable: { strategy: MeasuringStrategy.Always } }}
          onDragStart={handleDragStart}
          onDragOver={handleDragOver}
          onDragEnd={handleDragEnd}
          onDragCancel={handleDragCancel}
        >
          {/* Columns never get narrower than 260px: on smaller screens the board scrolls
              sideways. The padding (offset by negative margins) keeps the column shadows
              and the drop ring from being clipped by the scroll container. */}
          <section className="-mx-4 -mb-10 -mt-2 grid grid-cols-[repeat(5,minmax(260px,1fr))] gap-4 overflow-x-auto px-4 pb-10 pt-2 sm:-mx-6 sm:gap-6 sm:px-6">
            {board.columns.map((column) => (
              <KanbanColumn
                key={column.id}
                column={column}
                cards={column.cardIds.map((cardId) => board.cards[cardId])}
                onRename={handleRenameColumn}
                onAddCard={handleAddCard}
                onDeleteCard={handleDeleteCard}
                onEditCard={handleEditCard}
              />
            ))}
          </section>
          {/* DragOverlay sizes itself to the dragged card. */}
          <DragOverlay>
            {activeCard ? <KanbanCardPreview card={activeCard} /> : null}
          </DragOverlay>
        </DndContext>
      </main>
      <ChatWidget onBoardUpdate={handleAIBoardUpdate} />
    </div>
  );
};
