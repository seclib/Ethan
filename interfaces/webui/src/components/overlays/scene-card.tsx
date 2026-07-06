"use client";

import { motion, AnimatePresence } from "framer-motion";

interface SceneCardProps {
  open: boolean;
  onClose: () => void;
  chapter: string;
  number?: string;
  label: string;
  title: string;
  description: string;
}

export function SceneCard({ open, onClose, chapter, number, label, title, description }: SceneCardProps) {
  return (
    <AnimatePresence>
      {open && (
        <motion.div
          className="scene-card-overlay"
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          transition={{ duration: 0.2 }}
          onClick={onClose}
        >
          <motion.div
            className="scene-card"
            initial={{ scale: 0.92, opacity: 0 }}
            animate={{ scale: 1, opacity: 1 }}
            exit={{ scale: 0.92, opacity: 0 }}
            transition={{ duration: 0.25, ease: [0.2, 0.8, 0.25, 1] }}
            onClick={(e) => e.stopPropagation()}
          >
            <div className="scene-card-glow" />
            <div className="scene-card-eyebrow">
              <span>{number || "—"}</span>
              <span className="scene-card-bar" />
              <span>{chapter}</span>
            </div>
            <div className="scene-card-title">{title}</div>
            <div className="scene-card-desc">{description}</div>
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}