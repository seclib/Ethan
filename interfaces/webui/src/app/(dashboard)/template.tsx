"use client";

import { motion } from "framer-motion";
import { usePathname } from "next/navigation";

export default function Template({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  
  return (
    <motion.div
      key={pathname}
      initial={{ opacity: 0, filter: "blur(4px)", y: 4 }}
      animate={{ opacity: 1, filter: "blur(0px)", y: 0 }}
      exit={{ opacity: 0, filter: "blur(4px)", y: -4 }}
      transition={{ duration: 0.25, ease: "easeOut" }}
      className="contents"
    >
      {children}
    </motion.div>
  );
}
