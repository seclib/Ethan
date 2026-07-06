"use client";

import { motion, AnimatePresence } from "framer-motion";

interface DetailPanelProps {
  open: boolean;
  onClose: () => void;
  title: string;
  children: React.ReactNode;
}

export function DetailPanel({ open, onClose, title, children }: DetailPanelProps) {
  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.div
            className="detail-panel-overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            onClick={onClose}
          />
          <motion.aside
            className="detail-panel"
            initial={{ x: "100%" }}
            animate={{ x: 0 }}
            exit={{ x: "100%" }}
            transition={{ duration: 0.25, ease: [0.2, 0.8, 0.25, 1] }}
          >
            <div className="detail-panel-header">
              <span className="detail-panel-title">{title}</span>
              <button className="detail-panel-close" onClick={onClose}>✕</button>
            </div>
            <div className="detail-panel-body">
              {children}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}